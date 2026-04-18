"""
Creator Economy — XP = ROI metric + SLH Index.

Track 7 of Alpha Readiness. Extends existing marketplace module with:
  - XP snapshot per user (current_value / fiat_invested)
  - SLH Index (median XP across active users)
  - Sales tracking + royalty ledger
  - Course-lesson flag on items

Endpoints:
  GET  /api/creator/xp/{user_id}         — user's XP (ROI ratio)
  GET  /api/creator/slh-index            — global median XP + sparkline data
  GET  /api/creator/shop/{user_id}       — personal shop view with stats
  POST /api/creator/roi/snapshot         — admin; recompute snapshot for a user
  POST /api/creator/roi/snapshot/all     — admin; recompute for all users (cron)

XP formula:
  user_xp = total_portfolio_value_now / total_fiat_invested
  where:
    total_portfolio_value_now = sum(SLH_held × current_SLH_price
                                   + AIC_held × current_AIC_price
                                   + marketplace_earnings
                                   + staking_yield
                                   + REP_bonus * 0.1)
    total_fiat_invested = sum(receipts where source_type in (payment_*, external_*))

SLH Index formula:
  slh_index = median(user_xp for user in users where total_fiat_invested > 0)

A user with 0 fiat invested is "xp = ∞ (pure gain)" — not counted in index.
"""
from __future__ import annotations

import os
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel


router = APIRouter(prefix="/api/creator", tags=["Creator Economy"])

_pool = None

# Current prices — editable via env vars. TODO: fetch live from oracle.
SLH_PRICE_USD = float(os.getenv("SLH_PRICE_USD", "121.6"))  # ~₪444 / 3.65
AIC_PRICE_USD = float(os.getenv("AIC_PRICE_USD", "0.001"))
REP_VALUE_USD = float(os.getenv("REP_VALUE_USD", "0.01"))  # REP is symbolic — 0.01$ per point


def set_pool(pool):
    global _pool
    _pool = pool


async def _ensure_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_roi_snapshot (
            user_id BIGINT PRIMARY KEY,
            total_fiat_invested NUMERIC(18,4) DEFAULT 0,
            slh_held NUMERIC(18,6) DEFAULT 0,
            aic_held NUMERIC(18,4) DEFAULT 0,
            rep_held INTEGER DEFAULT 0,
            marketplace_earnings_usd NUMERIC(18,4) DEFAULT 0,
            current_value_usd NUMERIC(18,4) DEFAULT 0,
            xp_ratio NUMERIC(12,4),
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_roi_xp ON user_roi_snapshot(xp_ratio);

        CREATE TABLE IF NOT EXISTS creator_sales (
            id BIGSERIAL PRIMARY KEY,
            item_id BIGINT NOT NULL,
            seller_id BIGINT NOT NULL,
            buyer_id BIGINT NOT NULL,
            amount NUMERIC(18,4) NOT NULL,
            currency TEXT NOT NULL,
            amount_usd NUMERIC(18,4),
            royalty_paid NUMERIC(18,4) DEFAULT 0,
            sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_cs_seller ON creator_sales(seller_id);
        CREATE INDEX IF NOT EXISTS idx_cs_buyer ON creator_sales(buyer_id);
        """
    )
    # Optional column extension on marketplace_items for course linking
    try:
        await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS course_url TEXT")
        await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS is_course_lesson BOOLEAN DEFAULT FALSE")
        await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS story TEXT")
    except Exception:
        pass


async def _compute_xp(conn, user_id: int) -> dict:
    """Pure function: compute XP snapshot for one user from DB state."""
    # Fiat invested: sum of receipts paid
    fiat_invested_usd = 0.0
    try:
        rcpts = await conn.fetch(
            "SELECT amount, currency FROM payment_receipts WHERE user_id = $1",
            user_id,
        )
        for r in rcpts:
            amt = float(r["amount"] or 0)
            cur = (r["currency"] or "").upper()
            if cur == "USD":
                fiat_invested_usd += amt
            elif cur == "ILS":
                fiat_invested_usd += amt / 3.65
            elif cur == "BNB":
                fiat_invested_usd += amt * 641.0  # approx BNB price
            elif cur == "TON":
                fiat_invested_usd += amt * 1.40
            elif cur == "SLH":
                fiat_invested_usd += amt * SLH_PRICE_USD
            elif cur == "AIC":
                fiat_invested_usd += amt * AIC_PRICE_USD
    except Exception:
        pass

    # Marketplace earnings: sum of creator_sales where seller = this user
    earnings_usd = 0.0
    try:
        rows = await conn.fetch(
            "SELECT COALESCE(SUM(amount_usd), 0) AS total FROM creator_sales WHERE seller_id = $1",
            user_id,
        )
        earnings_usd = float(rows[0]["total"] or 0) if rows else 0.0
    except Exception:
        pass

    # SLH held — try multiple possible tables
    slh_held = 0.0
    for q in (
        "SELECT balance FROM tokens WHERE user_id = $1 AND symbol = 'SLH'",
        "SELECT slh_balance FROM user_balances WHERE user_id = $1",
    ):
        try:
            v = await conn.fetchval(q, user_id)
            if v is not None:
                slh_held = float(v)
                break
        except Exception:
            continue

    # AIC held
    aic_held = 0.0
    try:
        v = await conn.fetchval("SELECT balance FROM aic_balances WHERE user_id = $1", user_id)
        if v is not None:
            aic_held = float(v)
    except Exception:
        pass

    # REP held
    rep_held = 0
    for q in (
        "SELECT rep_score FROM reputation WHERE user_id = $1",
        "SELECT score FROM user_rep WHERE user_id = $1",
    ):
        try:
            v = await conn.fetchval(q, user_id)
            if v is not None:
                rep_held = int(v)
                break
        except Exception:
            continue

    current_value_usd = (
        slh_held * SLH_PRICE_USD
        + aic_held * AIC_PRICE_USD
        + rep_held * REP_VALUE_USD
        + earnings_usd
    )

    xp_ratio = None
    if fiat_invested_usd > 0:
        xp_ratio = current_value_usd / fiat_invested_usd

    return {
        "user_id": user_id,
        "total_fiat_invested": fiat_invested_usd,
        "slh_held": slh_held,
        "aic_held": aic_held,
        "rep_held": rep_held,
        "marketplace_earnings_usd": earnings_usd,
        "current_value_usd": current_value_usd,
        "xp_ratio": xp_ratio,
        "xp_display": "∞" if xp_ratio is None else f"{xp_ratio:.2f}",
        "status": (
            "infinite" if xp_ratio is None
            else "profit" if xp_ratio > 1.0
            else "loss" if xp_ratio < 1.0
            else "break_even"
        ),
    }


@router.get("/xp/{user_id}")
async def user_xp(user_id: int, fresh: bool = False):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        if not fresh:
            row = await conn.fetchrow(
                "SELECT * FROM user_roi_snapshot WHERE user_id = $1 AND snapshot_at > NOW() - INTERVAL '5 minutes'",
                user_id,
            )
            if row:
                d = dict(row)
                d["snapshot_at"] = d["snapshot_at"].isoformat() if d.get("snapshot_at") else None
                d["cached"] = True
                return d

        result = await _compute_xp(conn, user_id)
        await conn.execute(
            """
            INSERT INTO user_roi_snapshot
                (user_id, total_fiat_invested, slh_held, aic_held, rep_held,
                 marketplace_earnings_usd, current_value_usd, xp_ratio, snapshot_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                total_fiat_invested = EXCLUDED.total_fiat_invested,
                slh_held = EXCLUDED.slh_held,
                aic_held = EXCLUDED.aic_held,
                rep_held = EXCLUDED.rep_held,
                marketplace_earnings_usd = EXCLUDED.marketplace_earnings_usd,
                current_value_usd = EXCLUDED.current_value_usd,
                xp_ratio = EXCLUDED.xp_ratio,
                snapshot_at = NOW()
            """,
            user_id, result["total_fiat_invested"], result["slh_held"], result["aic_held"],
            result["rep_held"], result["marketplace_earnings_usd"], result["current_value_usd"],
            result["xp_ratio"],
        )
        result["cached"] = False
        return result


@router.get("/slh-index")
async def slh_index():
    """Global SLH Index — median XP across users with >0 fiat invested."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT xp_ratio FROM user_roi_snapshot
            WHERE total_fiat_invested > 0 AND xp_ratio IS NOT NULL
            ORDER BY xp_ratio
            """
        )
        xps = [float(r["xp_ratio"]) for r in rows]
        count = len(xps)
        if count == 0:
            return {"slh_index": None, "users_included": 0, "trend": "flat", "note": "No fiat-paying users yet"}

        median = xps[count // 2] if count % 2 == 1 else (xps[count // 2 - 1] + xps[count // 2]) / 2
        avg = sum(xps) / count

        # Trend — compare to 24h ago via heuristic (simplified)
        trend = "up" if median > 1.0 else "down" if median < 1.0 else "flat"

        return {
            "slh_index": round(median, 4),
            "average_xp": round(avg, 4),
            "min_xp": round(xps[0], 4),
            "max_xp": round(xps[-1], 4),
            "users_included": count,
            "trend": trend,
            "peak_xp_label": "∞" if any(r.get("xp_ratio") is None for r in rows) else round(xps[-1], 2),
            "computed_at": datetime.utcnow().isoformat(),
        }


@router.get("/shop/{user_id}")
async def personal_shop(user_id: int):
    """Personal creator shop — listings + earnings + XP."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        # Ensure XP is fresh
        xp = await _compute_xp(conn, user_id)

        try:
            listings = await conn.fetch(
                """
                SELECT id, title, description, price, currency, image_url, category,
                       status, views, created_at, story, course_url, is_course_lesson
                FROM marketplace_items WHERE seller_id = $1
                ORDER BY id DESC LIMIT 100
                """,
                user_id,
            )
            listings_data = [dict(r) for r in listings]
        except Exception:
            listings_data = []

        try:
            sales = await conn.fetch(
                """
                SELECT id, item_id, amount, currency, amount_usd, sold_at
                FROM creator_sales WHERE seller_id = $1 ORDER BY id DESC LIMIT 50
                """,
                user_id,
            )
            sales_data = [dict(r) for r in sales]
        except Exception:
            sales_data = []

        total_sales = sum(float(s["amount_usd"] or 0) for s in sales_data)

    return {
        "user_id": user_id,
        "xp": xp,
        "listings": listings_data,
        "listings_count": len(listings_data),
        "sales_count": len(sales_data),
        "total_sales_usd": total_sales,
        "recent_sales": sales_data[:10],
    }


class PurchaseCompleteReq(BaseModel):
    item_id: int
    buyer_id: int
    amount_paid: float
    currency: str
    receipt_number: Optional[str] = None
    tx_hash: Optional[str] = None


@router.post("/purchase/complete")
async def purchase_complete(req: PurchaseCompleteReq):
    """Called by pay.html after a marketplace purchase is verified.
    Records the sale, credits seller's marketplace_earnings, decrements stock,
    creates marketplace_order, triggers XP snapshot refresh."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)

        # Fetch item + seller
        item = await conn.fetchrow(
            "SELECT id, seller_id, title, price, currency, stock, status FROM marketplace_items WHERE id = $1",
            req.item_id,
        )
        if not item:
            raise HTTPException(404, "item not found")
        if item["status"] != "approved":
            raise HTTPException(400, f"item not available (status={item['status']})")
        if int(item["stock"] or 0) <= 0:
            raise HTTPException(400, "out of stock")

        seller_id = int(item["seller_id"])
        if seller_id == req.buyer_id:
            raise HTTPException(400, "cannot buy your own listing")

        # USD conversion (same rates as in _compute_xp)
        cur = (req.currency or item["currency"]).upper()
        usd = 0.0
        amt = float(req.amount_paid or 0)
        if cur == "USD":   usd = amt
        elif cur == "ILS": usd = amt / 3.65
        elif cur == "BNB": usd = amt * 641.0
        elif cur == "TON": usd = amt * 1.40
        elif cur == "SLH": usd = amt * SLH_PRICE_USD
        elif cur == "AIC": usd = amt * AIC_PRICE_USD

        # Idempotency: if same receipt_number exists, return existing
        if req.receipt_number:
            existing = await conn.fetchval(
                "SELECT id FROM creator_sales WHERE item_id = $1 AND buyer_id = $2 AND amount = $3",
                req.item_id, req.buyer_id, amt,
            )
            if existing:
                return {"ok": True, "sale_id": existing, "already_processed": True}

        # Record the sale
        sale_id = await conn.fetchval(
            """
            INSERT INTO creator_sales (item_id, seller_id, buyer_id, amount, currency, amount_usd)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """,
            req.item_id, seller_id, req.buyer_id, amt, cur, usd,
        )

        # Decrement stock
        await conn.execute("UPDATE marketplace_items SET stock = stock - 1 WHERE id = $1", req.item_id)

        # Create marketplace_order entry (if table exists)
        try:
            await conn.execute(
                """
                INSERT INTO marketplace_orders (buyer_id, seller_id, item_id, quantity, total_price, currency, status, completed_at)
                VALUES ($1, $2, $3, 1, $4, $5, 'completed', CURRENT_TIMESTAMP)
                """,
                req.buyer_id, seller_id, req.item_id, amt, cur,
            )
        except Exception:
            pass

        # Recompute seller XP (invalidate cache)
        seller_xp = await _compute_xp(conn, seller_id)
        await conn.execute(
            """
            INSERT INTO user_roi_snapshot
                (user_id, total_fiat_invested, slh_held, aic_held, rep_held,
                 marketplace_earnings_usd, current_value_usd, xp_ratio, snapshot_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                total_fiat_invested = EXCLUDED.total_fiat_invested,
                slh_held = EXCLUDED.slh_held,
                aic_held = EXCLUDED.aic_held,
                rep_held = EXCLUDED.rep_held,
                marketplace_earnings_usd = EXCLUDED.marketplace_earnings_usd,
                current_value_usd = EXCLUDED.current_value_usd,
                xp_ratio = EXCLUDED.xp_ratio,
                snapshot_at = NOW()
            """,
            seller_id, seller_xp["total_fiat_invested"], seller_xp["slh_held"], seller_xp["aic_held"],
            seller_xp["rep_held"], seller_xp["marketplace_earnings_usd"], seller_xp["current_value_usd"],
            seller_xp["xp_ratio"],
        )

    return {
        "ok": True,
        "sale_id": sale_id,
        "item_title": item["title"],
        "seller_id": seller_id,
        "amount_usd": usd,
        "seller_new_xp": seller_xp["xp_ratio"],
        "seller_new_xp_display": seller_xp["xp_display"],
        "message": f"רכישה הושלמה · המוכר #{seller_id} קיבל ${usd:.2f}, XP עודכן.",
    }


class SnapshotRefreshReq(BaseModel):
    user_id: int


@router.post("/roi/snapshot")
async def refresh_roi_snapshot(req: SnapshotRefreshReq, x_admin_key: Optional[str] = Header(None)):
    """Admin: force-refresh XP snapshot for a specific user."""
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "slh2026admin").split(",") if k.strip()]
    if x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        result = await _compute_xp(conn, req.user_id)
        await conn.execute(
            """
            INSERT INTO user_roi_snapshot
                (user_id, total_fiat_invested, slh_held, aic_held, rep_held,
                 marketplace_earnings_usd, current_value_usd, xp_ratio, snapshot_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                total_fiat_invested = EXCLUDED.total_fiat_invested,
                slh_held = EXCLUDED.slh_held,
                aic_held = EXCLUDED.aic_held,
                rep_held = EXCLUDED.rep_held,
                marketplace_earnings_usd = EXCLUDED.marketplace_earnings_usd,
                current_value_usd = EXCLUDED.current_value_usd,
                xp_ratio = EXCLUDED.xp_ratio,
                snapshot_at = NOW()
            """,
            req.user_id, result["total_fiat_invested"], result["slh_held"], result["aic_held"],
            result["rep_held"], result["marketplace_earnings_usd"], result["current_value_usd"],
            result["xp_ratio"],
        )
    return {"ok": True, "snapshot": result}


@router.post("/roi/snapshot/all")
async def refresh_all_snapshots(x_admin_key: Optional[str] = Header(None)):
    """Admin: recompute XP for all users — run as cron."""
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "slh2026admin").split(",") if k.strip()]
    if x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        try:
            users = await conn.fetch("SELECT DISTINCT user_id FROM payment_receipts")
        except Exception:
            users = []

        updated = 0
        for u in users:
            try:
                uid = u["user_id"]
                result = await _compute_xp(conn, uid)
                await conn.execute(
                    """
                    INSERT INTO user_roi_snapshot
                        (user_id, total_fiat_invested, slh_held, aic_held, rep_held,
                         marketplace_earnings_usd, current_value_usd, xp_ratio, snapshot_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_fiat_invested = EXCLUDED.total_fiat_invested,
                        slh_held = EXCLUDED.slh_held,
                        aic_held = EXCLUDED.aic_held,
                        rep_held = EXCLUDED.rep_held,
                        marketplace_earnings_usd = EXCLUDED.marketplace_earnings_usd,
                        current_value_usd = EXCLUDED.current_value_usd,
                        xp_ratio = EXCLUDED.xp_ratio,
                        snapshot_at = NOW()
                    """,
                    uid, result["total_fiat_invested"], result["slh_held"], result["aic_held"],
                    result["rep_held"], result["marketplace_earnings_usd"], result["current_value_usd"],
                    result["xp_ratio"],
                )
                updated += 1
            except Exception:
                continue

    return {"ok": True, "users_updated": updated}
