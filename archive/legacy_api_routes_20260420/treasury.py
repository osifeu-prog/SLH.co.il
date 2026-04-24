"""
Treasury â€” revenue tracking, buyback log, burn events.

Purpose: transparency about what the treasury does with revenue.
Every sale that goes through the ecosystem leaves a trail:
  1. revenue_entries: what came in (fiat or crypto)
  2. buyback_events: planned/executed SLH buybacks from market
  3. burn_events: tokens sent to dead address (AIC internally, SLH on-chain)

No signer integration yet â€” SLH buybacks + burns logged here but
executed manually by Osif via MetaMask. This gives us a public audit
trail without needing hot wallets on Railway.

Endpoints:
  GET  /api/treasury/summary           â€” totals (revenue, bought back, burned)
  GET  /api/treasury/buybacks          â€” chronological buyback log
  GET  /api/treasury/burns             â€” chronological burn log
  POST /api/treasury/revenue/record   â€” internal; called by payments_auto on each sale
  POST /api/treasury/buyback/log      â€” admin; log a buyback after MetaMask TX
  POST /api/treasury/burn/log          â€” admin; log a burn after MetaMask TX
  GET  /api/treasury/burn-rate         â€” how much would be auto-burned from unburned AIC
  POST /api/treasury/aic/burn          â€” admin; execute AIC burn (2% of marketplace in AIC)
"""
from __future__ import annotations

import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel


router = APIRouter(prefix="/api/treasury", tags=["Treasury"])

_pool = None

# Burn policy â€” what percentage of AIC-denominated marketplace sales get burned
BURN_RATE_AIC = float(os.getenv("TREASURY_BURN_RATE_AIC", "0.02"))  # 2% default
# Buyback policy â€” what % of fiat revenue the treasury commits to SLH buyback
BUYBACK_RATE_FIAT = float(os.getenv("TREASURY_BUYBACK_RATE", "0.10"))  # 10% default

DEAD_ADDRESS = "0x000000000000000000000000000000000000dEaD"


def set_pool(pool):
    global _pool
    _pool = pool


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


# ---------- Admin-only write endpoints ----------

def _check_admin(x_admin_key: Optional[str]):
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "slh2026admin").split(",") if k.strip()]
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
