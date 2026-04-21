"""
Treasury — revenue tracking, buyback log, burn events.

Purpose: transparency about what the treasury does with revenue.
Every sale that goes through the ecosystem leaves a trail:
  1. revenue_entries: what came in (fiat or crypto)
  2. buyback_events: planned/executed SLH buybacks from market
  3. burn_events: tokens sent to dead address (AIC internally, SLH on-chain)

No signer integration yet — SLH buybacks + burns logged here but
executed manually by Osif via MetaMask. This gives us a public audit
trail without needing hot wallets on Railway.

Endpoints:
  GET  /api/treasury/summary           — totals (revenue, bought back, burned)
  GET  /api/treasury/buybacks          — chronological buyback log
  GET  /api/treasury/burns             — chronological burn log
  POST /api/treasury/revenue/record   — internal; called by payments_auto on each sale
  POST /api/treasury/buyback/log      — admin; log a buyback after MetaMask TX
  POST /api/treasury/burn/log          — admin; log a burn after MetaMask TX
  GET  /api/treasury/burn-rate         — how much would be auto-burned from unburned AIC
  POST /api/treasury/aic/burn          — admin; execute AIC burn (2% of marketplace in AIC)
"""
from __future__ import annotations

import json
import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel


router = APIRouter(prefix="/api/treasury", tags=["Treasury"])

_pool = None

# Burn policy — what percentage of AIC-denominated marketplace sales get burned
BURN_RATE_AIC = float(os.getenv("TREASURY_BURN_RATE_AIC", "0.02"))  # 2% default
# Buyback policy — what % of fiat revenue the treasury commits to SLH buyback
BUYBACK_RATE_FIAT = float(os.getenv("TREASURY_BUYBACK_RATE", "0.10"))  # 10% default

# House cut configuration (Level 5 model) — % of gross sale that becomes house revenue.
# Default 0 keeps behavior identical to pre-audit; set via env to monetize channels.
MARKETPLACE_HOUSE_CUT = float(os.getenv("MARKETPLACE_HOUSE_CUT", "0"))     # 0 = current state (full 100% to seller)
ACADEMIA_HOUSE_CUT = float(os.getenv("ACADEMIA_HOUSE_CUT", "0.30"))        # CLAUDE.md says 70/30 to lecturer
PAYMENT_HOUSE_CUT = float(os.getenv("PAYMENT_HOUSE_CUT", "1.0"))           # direct deposits = 100% treasury

DEAD_ADDRESS = "0x000000000000000000000000000000000000dEaD"


def set_pool(pool):
    global _pool
    _pool = pool


async def record_revenue_internal(
    conn,
    source_type: str,
    amount_gross: float,
    currency: str,
    source_id: Optional[int] = None,
    user_id: Optional[int] = None,
    house_cut: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Call this from any payment flow to make revenue visible in /api/treasury/health.

    Uses the SAME DB connection as the caller — no HTTP round-trip, safe inside
    an existing transaction. Swallows errors by design: better to have invisible
    revenue than to break a customer's purchase because of an audit bug.

    Args:
        conn: asyncpg connection/transaction in which the parent sale is committed
        source_type: canonical tag, e.g. 'marketplace_sale' | 'academia_course' |
                     'academia_vip' | 'ambassador_sub' | 'payment_receipt' | 'genesis_nft'
        amount_gross: the full ticket charged to the customer (in `currency` units)
        currency: 'ILS' | 'BNB' | 'TON' | 'SLH' | 'AIC' | 'USD'
        source_id: FK to the parent sale/receipt row (for audit trace)
        user_id: the paying customer (optional)
        house_cut: fraction of gross that becomes house revenue; if None, picks a
                   sensible default based on source_type
        metadata: additional JSON context (gross, seller_id, etc.)
    """
    try:
        # Choose cut default if caller didn't specify
        if house_cut is None:
            st = (source_type or "").lower()
            if st in ("marketplace_sale", "marketplace_order"):
                house_cut = MARKETPLACE_HOUSE_CUT
            elif st in ("academia_course", "academia_enrollment"):
                house_cut = ACADEMIA_HOUSE_CUT
            elif st in ("academia_vip", "ambassador_sub", "premium_group", "genesis_nft"):
                house_cut = 1.0  # full to treasury
            elif st == "payment_receipt":
                house_cut = PAYMENT_HOUSE_CUT
            else:
                house_cut = 1.0

        house_amount = float(amount_gross) * float(house_cut or 0.0)
        if house_amount <= 0:
            # Nothing to record (valid state for current marketplace config), but
            # still leave an audit trail with amount=0 so the flow is visible.
            pass

        meta = dict(metadata or {})
        meta["gross_amount"] = float(amount_gross)
        meta["house_cut_applied"] = float(house_cut or 0.0)
        meta["currency_raw"] = currency

        await conn.execute(
            """
            INSERT INTO treasury_revenue
                (source_type, source_id, amount, currency, user_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            source_type,
            source_id,
            house_amount,
            (currency or "").upper(),
            user_id,
            json.dumps(meta, default=str),
        )
    except Exception:
        # Intentionally swallowed — revenue-recording bugs must NEVER break sales.
        # See ops/REVENUE_RECORDING_AUDIT_20260421.md for why this is the policy.
        pass


async def _ensure_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS treasury_revenue (
            id BIGSERIAL PRIMARY KEY,
            source_type TEXT NOT NULL,      -- 'payment_receipt' | 'marketplace_sale' | 'staking_fee' | 'manual'
            source_id BIGINT,
            amount NUMERIC(18,6) NOT NULL,
            currency TEXT NOT NULL,         -- 'ILS' | 'BNB' | 'TON' | 'SLH' | 'AIC'
            user_id BIGINT,
            metadata JSONB DEFAULT '{}'::jsonb,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_treasury_rev_currency ON treasury_revenue(currency);
        CREATE INDEX IF NOT EXISTS idx_treasury_rev_at ON treasury_revenue(recorded_at);

        CREATE TABLE IF NOT EXISTS treasury_buybacks (
            id BIGSERIAL PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'planned',  -- 'planned' | 'executed' | 'cancelled'
            slh_amount NUMERIC(18,6) NOT NULL,
            fiat_spent NUMERIC(18,6),
            fiat_currency TEXT,
            tx_hash TEXT,
            executed_by BIGINT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS treasury_burns (
            id BIGSERIAL PRIMARY KEY,
            token TEXT NOT NULL,             -- 'SLH' | 'AIC' | 'ZVK'
            amount NUMERIC(18,6) NOT NULL,
            reason TEXT NOT NULL,            -- 'marketplace_auto' | 'buyback' | 'manual_admin'
            tx_hash TEXT,                    -- on-chain burns only (SLH)
            executed_by BIGINT,
            source_sale_id BIGINT,
            burned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_burns_token ON treasury_burns(token);
        CREATE INDEX IF NOT EXISTS idx_burns_at ON treasury_burns(burned_at);
        """
    )


# ---------- Public read-only endpoints ----------

@router.get("/summary")
async def treasury_summary():
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        revenue_by_currency = await conn.fetch(
            "SELECT currency, SUM(amount) AS total, COUNT(*) AS count FROM treasury_revenue GROUP BY currency"
        )
        buybacks_total = await conn.fetchrow(
            "SELECT COALESCE(SUM(slh_amount),0) AS slh, COUNT(*) AS count FROM treasury_buybacks WHERE status = 'executed'"
        )
        burns_by_token = await conn.fetch(
            "SELECT token, COALESCE(SUM(amount),0) AS total, COUNT(*) AS count FROM treasury_burns GROUP BY token"
        )

    return {
        "revenue_by_currency": [dict(r) for r in revenue_by_currency],
        "buybacks": dict(buybacks_total) if buybacks_total else {"slh": 0, "count": 0},
        "burns_by_token": [dict(r) for r in burns_by_token],
        "policy": {
            "burn_rate_aic": BURN_RATE_AIC,
            "buyback_rate_fiat": BUYBACK_RATE_FIAT,
            "dead_address": DEAD_ADDRESS,
        },
    }


@router.get("/buybacks")
async def buyback_log(limit: int = 50):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, status, slh_amount, fiat_spent, fiat_currency, tx_hash, notes, created_at, executed_at
            FROM treasury_buybacks ORDER BY id DESC LIMIT $1
            """,
            max(1, min(limit, 200)),
        )
    return {"buybacks": [dict(r) for r in rows]}


@router.get("/burns")
async def burn_log(limit: int = 100):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, token, amount, reason, tx_hash, source_sale_id, burned_at
            FROM treasury_burns ORDER BY id DESC LIMIT $1
            """,
            max(1, min(limit, 500)),
        )
    return {"burns": [dict(r) for r in rows]}


@router.get("/burn-rate")
async def burn_rate_preview():
    """What percentage would be burned if admin runs /aic/burn now."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        aic_sales = await conn.fetchval(
            """
            SELECT COALESCE(SUM(amount), 0) FROM treasury_revenue
            WHERE currency = 'AIC' AND recorded_at > (
                SELECT COALESCE(MAX(burned_at), '1970-01-01') FROM treasury_burns
                WHERE token = 'AIC' AND reason = 'marketplace_auto'
            )
            """
        ) or 0
    pending = float(aic_sales) * BURN_RATE_AIC
    return {
        "aic_sales_since_last_burn": float(aic_sales),
        "burn_rate": BURN_RATE_AIC,
        "pending_burn_aic": pending,
    }


# ---------- Single Truth Test (public sustainability snapshot) ----------
# Answers the R >= P + W question from the Level 4 economic analysis.
# Conversion rates are env-configurable and echoed in the response for honesty.
_ZVK_ILS = float(os.getenv("ZVK_ILS", "4.4"))
_SLH_ILS = float(os.getenv("SLH_PRICE_ILS", "444"))
_BNB_ILS = float(os.getenv("BNB_ILS", "2200"))
_TON_ILS = float(os.getenv("TON_ILS", "18"))
_USD_ILS = float(os.getenv("USD_ILS", "3.65"))


def _to_ils(amount: float, currency: str) -> float:
    c = (currency or "").upper()
    if c in ("ILS", "NIS"):
        return amount
    if c == "BNB":
        return amount * _BNB_ILS
    if c == "TON":
        return amount * _TON_ILS
    if c == "SLH":
        return amount * _SLH_ILS
    if c == "AIC":
        return amount * _ZVK_ILS
    if c == "USD":
        return amount * _USD_ILS
    # Unknown currency: treat as ILS rather than silently zero it out
    return amount


@router.get("/health")
async def treasury_health():
    """
    Single Truth Test - R / P / W / Buffer snapshot for SLH sustainability.

    R (Revenue In)        - treasury_revenue aggregated today / 7d / 30d / lifetime
    P (Contingent Liab.)  - outstanding ZVK x ZVK_ILS + upcoming SLH buyback commitment
    W (Executed Outflows) - treasury_buybacks.fiat_spent + treasury_burns valued in ILS
    Buffer                - aic_reserve (USD) + max(0, R_lifetime - W)
    Status                - pre_revenue / healthy / caution / undercollateralized
    """
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)

        # ----- R: revenue by currency, per period -----
        period_defs = [("today", "1 day"), ("d7", "7 days"), ("d30", "30 days"), ("lifetime", "100 years")]
        revenue_periods: dict = {}
        R_ils: dict = {}
        for label, interval in period_defs:
            rows = await conn.fetch(
                f"""
                SELECT currency, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
                FROM treasury_revenue
                WHERE recorded_at > now() - interval '{interval}'
                GROUP BY currency
                """
            )
            by_cur = {r["currency"]: {"amount": float(r["total"]), "count": r["count"]} for r in rows}
            revenue_periods[label] = by_cur
            R_ils[label] = sum(_to_ils(d["amount"], cur) for cur, d in by_cur.items())

        # ----- P: outstanding ZVK + upcoming buyback commitment -----
        # aic_transactions may not exist yet on fresh DB; treat as zeros.
        aic_outstanding = 0.0
        try:
            aic_net = await conn.fetchrow(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN kind='earn'  THEN amount ELSE 0 END), 0) AS earned,
                  COALESCE(SUM(CASE WHEN kind='spend' THEN amount ELSE 0 END), 0) AS spent,
                  COALESCE(SUM(CASE WHEN kind='mint'  THEN amount ELSE 0 END), 0) AS minted,
                  COALESCE(SUM(CASE WHEN kind='burn'  THEN amount ELSE 0 END), 0) AS burned
                FROM aic_transactions
                """
            )
            aic_outstanding = max(0.0, (float(aic_net["earned"]) + float(aic_net["minted"]))
                                   - (float(aic_net["spent"]) + float(aic_net["burned"])))
        except Exception:
            aic_outstanding = 0.0

        P_zvk_contingent_ils = aic_outstanding * _ZVK_ILS

        fiat_r_lifetime_ils = sum(
            _to_ils(d["amount"], cur)
            for cur, d in revenue_periods["lifetime"].items()
            if (cur or "").upper() in ("ILS", "NIS", "BNB", "TON", "USD")
        )
        buyback_executed = await conn.fetchrow(
            """
            SELECT
              COALESCE(SUM(fiat_spent), 0) AS fiat_ils,
              COALESCE(SUM(slh_amount), 0) AS slh_bought,
              COUNT(*) AS count
            FROM treasury_buybacks
            WHERE status = 'executed'
            """
        )
        buyback_fiat_spent = float(buyback_executed["fiat_ils"])
        slh_bought_total = float(buyback_executed["slh_bought"])
        buybacks_count = int(buyback_executed["count"])
        P_upcoming_buyback = max(0.0, BUYBACK_RATE_FIAT * fiat_r_lifetime_ils - buyback_fiat_spent)
        P_total_ils = P_zvk_contingent_ils + P_upcoming_buyback

        # ----- W: executed outflows -----
        burn_rows = await conn.fetch(
            "SELECT token, COALESCE(SUM(amount),0) AS total, COUNT(*) AS count FROM treasury_burns GROUP BY token"
        )
        burns_by_token = {
            r["token"]: {"amount": float(r["total"]), "count": r["count"]} for r in burn_rows
        }
        W_burns_ils = sum(_to_ils(d["amount"], tok) for tok, d in burns_by_token.items())
        W_total_ils = buyback_fiat_spent + W_burns_ils

        # ----- Buffer -----
        reserve_usd = 0.0
        try:
            reserve_usd = float(await conn.fetchval("SELECT COALESCE(SUM(usd_amount), 0) FROM aic_reserve") or 0)
        except Exception:
            reserve_usd = 0.0
        reserve_ils = reserve_usd * _USD_ILS
        net_treasury_ils = R_ils["lifetime"] - W_total_ils
        buffer_ils = reserve_ils + max(0.0, net_treasury_ils)

    # ----- Status -----
    if P_total_ils < 100:
        status = {"code": "pre_revenue", "color": "blue",
                  "label_he": "pre-revenue", "coverage_ratio": None}
    else:
        coverage = buffer_ils / P_total_ils
        if coverage >= 0.20:
            status = {"code": "healthy", "color": "green",
                      "label_he": "healthy", "coverage_ratio": round(coverage, 4)}
        elif coverage >= 0.10:
            status = {"code": "caution", "color": "yellow",
                      "label_he": "caution", "coverage_ratio": round(coverage, 4)}
        else:
            status = {"code": "undercollateralized", "color": "red",
                      "label_he": "undercollateralized", "coverage_ratio": round(coverage, 4)}

    # ----- Breakeven (Level 5 model) -----
    # Milestones from ops/LEVEL_5_SLH_BREAKEVEN_MODEL.md
    BE_SURVIVAL = float(os.getenv("BREAKEVEN_SURVIVAL_ILS", "1000"))
    BE_SUSTAIN = float(os.getenv("BREAKEVEN_SUSTAIN_ILS", "5000"))
    BE_THRIVING = float(os.getenv("BREAKEVEN_THRIVING_ILS", "20000"))

    r30 = float(R_ils["d30"])
    if r30 >= BE_THRIVING:
        next_tier = "above_thriving"
    elif r30 >= BE_SUSTAIN:
        next_tier = "thriving"
    elif r30 >= BE_SURVIVAL:
        next_tier = "sustainable"
    else:
        next_tier = "survival"

    breakeven = {
        "current_r_ils_30d": round(r30, 2),
        "targets_ils_per_mo": {
            "survival": BE_SURVIVAL,
            "sustainable": BE_SUSTAIN,
            "thriving": BE_THRIVING,
        },
        "progress_pct": {
            "survival": round(100 * r30 / BE_SURVIVAL, 1) if BE_SURVIVAL else None,
            "sustainable": round(100 * r30 / BE_SUSTAIN, 1) if BE_SUSTAIN else None,
            "thriving": round(100 * r30 / BE_THRIVING, 1) if BE_THRIVING else None,
        },
        "next_milestone": next_tier,
        "gap_to_next_ils": (
            max(0.0, BE_SURVIVAL - r30) if next_tier == "survival"
            else max(0.0, BE_SUSTAIN - r30) if next_tier == "sustainable"
            else max(0.0, BE_THRIVING - r30) if next_tier == "thriving"
            else 0.0
        ),
    }

    return {
        "as_of": datetime.utcnow().isoformat() + "Z",
        "rates_ils": {
            "ZVK": _ZVK_ILS, "AIC": _ZVK_ILS, "SLH": _SLH_ILS,
            "BNB": _BNB_ILS, "TON": _TON_ILS, "USD": _USD_ILS,
        },
        "R_revenue": {
            "ils_today": round(R_ils["today"], 2),
            "ils_7d": round(R_ils["d7"], 2),
            "ils_30d": round(R_ils["d30"], 2),
            "ils_lifetime": round(R_ils["lifetime"], 2),
            "by_currency_period": revenue_periods,
        },
        "P_contingent_obligations": {
            "ils_total": round(P_total_ils, 2),
            "zvk_outstanding_units": round(aic_outstanding, 4),
            "zvk_contingent_ils": round(P_zvk_contingent_ils, 2),
            "upcoming_slh_buyback_ils": round(P_upcoming_buyback, 2),
            "buyback_rate": BUYBACK_RATE_FIAT,
        },
        "W_outflows": {
            "ils_total": round(W_total_ils, 2),
            "buybacks_executed_ils": round(buyback_fiat_spent, 2),
            "buybacks_slh_bought": slh_bought_total,
            "buybacks_count": buybacks_count,
            "burns_by_token": burns_by_token,
            "burns_ils_equiv": round(W_burns_ils, 2),
        },
        "buffer": {
            "ils_total": round(buffer_ils, 2),
            "reserve_usd": reserve_usd,
            "net_treasury_ils": round(net_treasury_ils, 2),
        },
        "status": status,
        "breakeven": breakeven,
        "notes": [
            "Rates are fixed approximations from env vars; exposed under rates_ils for transparency.",
            "P is contingent, not a guaranteed cash claim - ZVK is activity reward, not yield.",
            "Status 'pre_revenue' means P < 100 ILS; coverage math kicks in above that threshold.",
            "Breakeven milestones (survival=1000, sustainable=5000, thriving=20000 ILS/mo) from ops/LEVEL_5_SLH_BREAKEVEN_MODEL.md",
        ],
    }


# ---------- Admin-only write endpoints ----------

def _check_admin(x_admin_key: Optional[str]):
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()]
    if x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")


class RevenueRecordReq(BaseModel):
    source_type: str
    source_id: Optional[int] = None
    amount: float
    currency: str
    user_id: Optional[int] = None
    metadata: Optional[dict] = None


@router.post("/revenue/record")
async def record_revenue(req: RevenueRecordReq, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rid = await conn.fetchval(
            """
            INSERT INTO treasury_revenue (source_type, source_id, amount, currency, user_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """,
            req.source_type, req.source_id, req.amount, req.currency, req.user_id,
            __import__('json').dumps(req.metadata or {}),
        )
    return {"ok": True, "revenue_id": rid}


class BuybackLogReq(BaseModel):
    status: str = "executed"     # or 'planned'
    slh_amount: float
    fiat_spent: Optional[float] = None
    fiat_currency: Optional[str] = None
    tx_hash: Optional[str] = None
    notes: Optional[str] = None


@router.post("/buyback/log")
async def log_buyback(req: BuybackLogReq, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    executed_at = datetime.utcnow() if req.status == "executed" else None
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        bid = await conn.fetchval(
            """
            INSERT INTO treasury_buybacks (status, slh_amount, fiat_spent, fiat_currency, tx_hash, notes, executed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
            """,
            req.status, req.slh_amount, req.fiat_spent, req.fiat_currency, req.tx_hash, req.notes, executed_at,
        )
    return {"ok": True, "buyback_id": bid, "status": req.status}


class BurnLogReq(BaseModel):
    token: str          # 'SLH' | 'AIC' | 'ZVK'
    amount: float
    reason: str = "manual_admin"
    tx_hash: Optional[str] = None
    source_sale_id: Optional[int] = None


@router.post("/burn/log")
async def log_burn(req: BurnLogReq, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        bid = await conn.fetchval(
            """
            INSERT INTO treasury_burns (token, amount, reason, tx_hash, source_sale_id)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
            """,
            req.token.upper(), req.amount, req.reason, req.tx_hash, req.source_sale_id,
        )
    return {"ok": True, "burn_id": bid}


@router.post("/aic/burn")
async def execute_aic_burn(x_admin_key: Optional[str] = Header(None)):
    """Admin-only: runs the pending AIC burn based on marketplace AIC sales since last burn."""
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        aic_sales = await conn.fetchval(
            """
            SELECT COALESCE(SUM(amount), 0) FROM treasury_revenue
            WHERE currency = 'AIC' AND recorded_at > (
                SELECT COALESCE(MAX(burned_at), '1970-01-01') FROM treasury_burns
                WHERE token = 'AIC' AND reason = 'marketplace_auto'
            )
            """
        ) or 0
        burn_amount = float(aic_sales) * BURN_RATE_AIC
        if burn_amount <= 0:
            return {"ok": True, "burned": 0, "message": "nothing to burn yet"}

        bid = await conn.fetchval(
            """
            INSERT INTO treasury_burns (token, amount, reason)
            VALUES ('AIC', $1, 'marketplace_auto') RETURNING id
            """,
            burn_amount,
        )
    return {"ok": True, "burn_id": bid, "burned_aic": burn_amount, "source_sales": float(aic_sales)}
