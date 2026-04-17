"""
SLH AIC · AI Credits — 6th internal token
==========================================
Bridges user activity → AI API costs → system value.
See ops/AIC_TOKEN_DESIGN.md for full design.

Phase 1 MVP endpoints (read + earn/spend flows):
  GET  /api/aic/balance/{user_id}     — current balance + lifetime stats
  GET  /api/aic/transactions/{user_id} — tx history
  POST /api/aic/earn                  — add AIC (auto-triggered by system events)
  POST /api/aic/spend                 — deduct AIC for AI call
  GET  /api/aic/stats                 — global: supply, daily flow, top holders
  POST /api/admin/aic/mint            — admin: create AIC against reserve
  GET  /api/admin/aic/reserve         — reserve status

Added 2026-04-17.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(prefix="/api/aic", tags=["AIC Token"])
admin_router = APIRouter(prefix="/api/admin/aic", tags=["AIC Admin"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool

VALID_EARN_REASONS = {
    "post_bonus", "comment_bonus", "reaction_bonus",
    "streak_daily", "learning_path_milestone",
    "expert_verify_submit", "expert_approved",
    "referral_joined", "purchase_bonus", "staking_dividend",
    "system_seed", "admin_grant"
}
VALID_SPEND_REASONS = {
    "ai_chat", "ai_summary", "ai_analysis", "ai_translation",
    "ai_recommendation", "ai_dm_reply", "ai_matching",
    "expert_consult_prebrief"
}
EARN_CAP_PER_HOUR = 10  # anti-spam


async def _ensure_aic_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS aic_balances (
            user_id BIGINT PRIMARY KEY,
            balance NUMERIC(18,4) NOT NULL DEFAULT 0,
            lifetime_earned NUMERIC(18,4) NOT NULL DEFAULT 0,
            lifetime_spent NUMERIC(18,4) NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS aic_transactions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            kind TEXT NOT NULL,
            amount NUMERIC(18,4) NOT NULL,
            reason TEXT NOT NULL,
            provider TEXT,
            tokens_consumed INTEGER,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_aic_tx_user ON aic_transactions(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_aic_tx_reason ON aic_transactions(reason);
        CREATE INDEX IF NOT EXISTS idx_aic_tx_kind ON aic_transactions(kind, created_at DESC);

        CREATE TABLE IF NOT EXISTS aic_reserve (
            id SERIAL PRIMARY KEY,
            usd_amount NUMERIC(14,2) NOT NULL,
            source TEXT NOT NULL,
            note TEXT,
            recorded_at TIMESTAMPTZ DEFAULT now()
        );
        """
    )


async def _upsert_balance(conn, user_id: int, delta: Decimal, kind: str, reason: str, provider: Optional[str] = None, tokens: Optional[int] = None, meta: Optional[dict] = None):
    """Atomically update balance + log tx. kind must be earn|spend|mint|burn."""
    if kind not in ("earn", "spend", "mint", "burn"):
        raise HTTPException(400, f"invalid kind: {kind}")

    # Get or create balance row
    bal_row = await conn.fetchrow(
        "SELECT balance, lifetime_earned, lifetime_spent FROM aic_balances WHERE user_id=$1 FOR UPDATE",
        user_id,
    )
    if not bal_row:
        await conn.execute(
            "INSERT INTO aic_balances (user_id, balance, lifetime_earned, lifetime_spent) VALUES ($1, 0, 0, 0)",
            user_id,
        )
        cur_balance = Decimal("0")
        life_earn = Decimal("0")
        life_spend = Decimal("0")
    else:
        cur_balance = Decimal(str(bal_row["balance"]))
        life_earn = Decimal(str(bal_row["lifetime_earned"]))
        life_spend = Decimal(str(bal_row["lifetime_spent"]))

    if kind in ("spend", "burn"):
        if cur_balance + delta < 0:
            raise HTTPException(402, f"Insufficient AIC: have {cur_balance}, need {-delta}")
        new_balance = cur_balance + delta  # delta should be negative for spend
        new_spent = life_spend + (-delta)
        await conn.execute(
            "UPDATE aic_balances SET balance=$1, lifetime_spent=$2, updated_at=now() WHERE user_id=$3",
            new_balance, new_spent, user_id,
        )
    else:  # earn or mint
        new_balance = cur_balance + delta
        new_earned = life_earn + delta
        await conn.execute(
            "UPDATE aic_balances SET balance=$1, lifetime_earned=$2, updated_at=now() WHERE user_id=$3",
            new_balance, new_earned, user_id,
        )

    # Log tx
    import json
    tx_id = await conn.fetchval(
        """
        INSERT INTO aic_transactions (user_id, kind, amount, reason, provider, tokens_consumed, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb) RETURNING id
        """,
        user_id, kind, abs(delta), reason, provider, tokens, json.dumps(meta or {}),
    )

    return {
        "tx_id": tx_id,
        "new_balance": float(new_balance),
        "delta": float(delta),
    }


# ═══════ Public endpoints ═══════

@router.get("/balance/{user_id}")
async def get_balance(user_id: int):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        row = await conn.fetchrow(
            "SELECT balance, lifetime_earned, lifetime_spent, updated_at FROM aic_balances WHERE user_id=$1",
            user_id,
        )
    if not row:
        return {
            "user_id": user_id, "balance": 0, "lifetime_earned": 0,
            "lifetime_spent": 0, "has_wallet": False,
        }
    return {
        "user_id": user_id,
        "balance": float(row["balance"]),
        "lifetime_earned": float(row["lifetime_earned"]),
        "lifetime_spent": float(row["lifetime_spent"]),
        "updated_at": row["updated_at"].isoformat(),
        "has_wallet": True,
    }


@router.get("/transactions/{user_id}")
async def get_transactions(user_id: int, limit: int = 50, kind: Optional[str] = None):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(limit, 200))
    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        if kind:
            rows = await conn.fetch(
                "SELECT * FROM aic_transactions WHERE user_id=$1 AND kind=$2 ORDER BY id DESC LIMIT $3",
                user_id, kind, limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM aic_transactions WHERE user_id=$1 ORDER BY id DESC LIMIT $2",
                user_id, limit,
            )
    return {
        "user_id": user_id,
        "transactions": [
            {
                "id": r["id"], "kind": r["kind"], "amount": float(r["amount"]),
                "reason": r["reason"], "provider": r["provider"],
                "tokens_consumed": r["tokens_consumed"],
                "metadata": r["metadata"] if isinstance(r["metadata"], dict) else {},
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ],
    }


class EarnReq(BaseModel):
    user_id: int
    amount: float
    reason: str
    metadata: Optional[dict] = None


@router.post("/earn")
async def earn_aic(req: EarnReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    reason = (req.reason or "").strip().lower()
    if reason not in VALID_EARN_REASONS:
        raise HTTPException(400, f"invalid earn reason '{reason}'. allowed: {sorted(VALID_EARN_REASONS)}")
    amount = Decimal(str(req.amount))
    if amount <= 0 or amount > 100:
        raise HTTPException(400, "amount must be 0 < x <= 100")

    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        # anti-spam: cap per hour
        earned_last_hour = await conn.fetchval(
            """
            SELECT COALESCE(SUM(amount), 0) FROM aic_transactions
            WHERE user_id=$1 AND kind='earn' AND created_at > now() - interval '1 hour'
            """,
            req.user_id,
        )
        if float(earned_last_hour or 0) + float(amount) > EARN_CAP_PER_HOUR:
            raise HTTPException(429, f"earn cap exceeded ({EARN_CAP_PER_HOUR} AIC/hour)")
        result = await _upsert_balance(conn, req.user_id, amount, "earn", reason, meta=req.metadata)
    return {"ok": True, **result}


class SpendReq(BaseModel):
    user_id: int
    amount: float
    reason: str
    provider: Optional[str] = None
    tokens_consumed: Optional[int] = None
    metadata: Optional[dict] = None


@router.post("/spend")
async def spend_aic(req: SpendReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    reason = (req.reason or "").strip().lower()
    if reason not in VALID_SPEND_REASONS:
        raise HTTPException(400, f"invalid spend reason '{reason}'. allowed: {sorted(VALID_SPEND_REASONS)}")
    amount = Decimal(str(req.amount))
    if amount <= 0:
        raise HTTPException(400, "amount must be > 0")

    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        result = await _upsert_balance(
            conn, req.user_id, -amount, "spend", reason,
            provider=req.provider, tokens=req.tokens_consumed, meta=req.metadata,
        )
    return {"ok": True, **result}


@router.get("/stats")
async def aic_stats():
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        totals = await conn.fetchrow(
            """
            SELECT
              COALESCE(SUM(balance), 0) AS total_supply,
              COALESCE(SUM(lifetime_earned), 0) AS lifetime_earned_total,
              COALESCE(SUM(lifetime_spent), 0) AS lifetime_spent_total,
              COUNT(*) AS wallets_count
            FROM aic_balances
            """
        )
        daily = await conn.fetchrow(
            """
            SELECT
              COALESCE(SUM(CASE WHEN kind='earn' THEN amount ELSE 0 END), 0) AS earned_24h,
              COALESCE(SUM(CASE WHEN kind='spend' THEN amount ELSE 0 END), 0) AS spent_24h,
              COUNT(*) FILTER (WHERE created_at > now() - interval '24 hours') AS tx_24h
            FROM aic_transactions WHERE created_at > now() - interval '24 hours'
            """
        )
        top = await conn.fetch(
            "SELECT user_id, balance, lifetime_earned FROM aic_balances ORDER BY balance DESC LIMIT 10"
        )
        reserve = await conn.fetchval(
            "SELECT COALESCE(SUM(usd_amount), 0) FROM aic_reserve"
        )
    return {
        "total_supply": float(totals["total_supply"]),
        "lifetime_earned": float(totals["lifetime_earned_total"]),
        "lifetime_spent": float(totals["lifetime_spent_total"]),
        "wallets_count": totals["wallets_count"],
        "earned_24h": float(daily["earned_24h"] or 0),
        "spent_24h": float(daily["spent_24h"] or 0),
        "tx_24h": daily["tx_24h"] or 0,
        "reserve_usd": float(reserve or 0),
        "reserve_ratio": (float(reserve or 0) * 1000) / max(float(totals["total_supply"]), 1),
        "top_holders": [
            {"user_id": r["user_id"], "balance": float(r["balance"]), "lifetime_earned": float(r["lifetime_earned"])}
            for r in top
        ],
    }


# ═══════ Admin endpoints ═══════

def _check_admin(x_admin_key: Optional[str]):
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()]
    if not admin_keys:
        admin_keys = ["slh2026admin", "slh_admin_2026", "slh-spark-admin", "slh-institutional"]
    if not x_admin_key or x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")


class MintReq(BaseModel):
    user_id: int
    amount: float
    reserve_usd: Optional[float] = None
    note: Optional[str] = None


@admin_router.post("/mint")
async def admin_mint(req: MintReq, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    amount = Decimal(str(req.amount))
    if amount <= 0 or amount > 100000:
        raise HTTPException(400, "mint amount must be 0 < x <= 100000")

    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        if req.reserve_usd and req.reserve_usd > 0:
            await conn.execute(
                "INSERT INTO aic_reserve (usd_amount, source, note) VALUES ($1, 'admin_injection', $2)",
                Decimal(str(req.reserve_usd)), req.note,
            )
        result = await _upsert_balance(
            conn, req.user_id, amount, "mint", "admin_grant",
            meta={"note": req.note} if req.note else None,
        )
    return {"ok": True, **result}


@admin_router.get("/reserve")
async def admin_reserve(x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        total = await conn.fetchval("SELECT COALESCE(SUM(usd_amount), 0) FROM aic_reserve")
        recent = await conn.fetch(
            "SELECT id, usd_amount, source, note, recorded_at FROM aic_reserve ORDER BY id DESC LIMIT 20"
        )
    return {
        "total_usd": float(total),
        "recent": [
            {
                "id": r["id"], "usd_amount": float(r["usd_amount"]),
                "source": r["source"], "note": r["note"],
                "recorded_at": r["recorded_at"].isoformat(),
            }
            for r in recent
        ],
    }


class ReserveAddReq(BaseModel):
    usd_amount: float
    source: str  # stripe_purchase | slh_swap | admin_injection
    note: Optional[str] = None


@admin_router.post("/reserve/add")
async def admin_reserve_add(req: ReserveAddReq, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    if req.usd_amount <= 0:
        raise HTTPException(400, "usd_amount must be > 0")
    async with _pool.acquire() as conn:
        await _ensure_aic_tables(conn)
        row = await conn.fetchrow(
            "INSERT INTO aic_reserve (usd_amount, source, note) VALUES ($1, $2, $3) RETURNING id, recorded_at",
            Decimal(str(req.usd_amount)), req.source, req.note,
        )
    return {"ok": True, "id": row["id"], "recorded_at": row["recorded_at"].isoformat()}
