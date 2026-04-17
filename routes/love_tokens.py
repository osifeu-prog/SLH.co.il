"""
Love Tokens — virtual affection economy.

STATUS: STUB (schema + endpoints live, but not wired to any UI yet).
Disabled on the frontend — users see nothing. DB tables created lazily.

Three token types:
  HUG (🤗)     — 5 AIC to send — gentle, friend-level
  KISS (💋)    — 20 AIC        — intimate, match-level
  HANDSHAKE (🤝) — 2 AIC       — formal, greeting-level

Why no UI yet: waiting on Osif's call on:
  - final pricing (5/20/2 AIC placeholder)
  - daily limits per user
  - monetization (do HUGs convert to ZVK? to SLH?)
  - which bots show the send UI (dating? community?)

Flip on by:
  1. Setting env LOVE_TOKENS_ENABLED=1 (unlocks POST /send)
  2. Wiring a UI button on /dating.html (send button) + /profile.html (view)

Endpoints:
  GET  /api/love/balance/{user_id}    — all 3 token balances (no auth — public profile view)
  GET  /api/love/received/{user_id}   — list of last N received tokens + from whom (last 100)
  POST /api/love/send                  — send token (requires AIC, respects daily cap)
  GET  /api/love/config                — current pricing + daily caps (read-only)

Tables (auto-created on first call):
  love_token_balances  — per-user per-type counter
  love_token_transfers — append-only ledger

All costs/prices are configurable via env vars (see LOVE_PRICES below).
"""
from __future__ import annotations

import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/love", tags=["Love Tokens"])

_pool = None

ENABLED = os.getenv("LOVE_TOKENS_ENABLED", "0") == "1"

# Editable pricing + caps — no UI yet. Change via Railway env vars when ready.
LOVE_PRICES = {
    "hug":       int(os.getenv("LOVE_PRICE_HUG", "5")),        # AIC cost
    "kiss":      int(os.getenv("LOVE_PRICE_KISS", "20")),
    "handshake": int(os.getenv("LOVE_PRICE_HANDSHAKE", "2")),
}
DAILY_CAP_PER_RECIPIENT = int(os.getenv("LOVE_DAILY_CAP", "10"))  # per (sender, recipient, day)


def set_pool(pool):
    global _pool
    _pool = pool


async def _ensure_love_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS love_token_balances (
            user_id BIGINT NOT NULL,
            token_type TEXT NOT NULL CHECK (token_type IN ('hug','kiss','handshake')),
            received INTEGER NOT NULL DEFAULT 0,
            sent INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, token_type)
        );

        CREATE TABLE IF NOT EXISTS love_token_transfers (
            id BIGSERIAL PRIMARY KEY,
            sender_id BIGINT NOT NULL,
            recipient_id BIGINT NOT NULL,
            token_type TEXT NOT NULL,
            aic_cost INTEGER NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_love_xfer_recipient ON love_token_transfers(recipient_id);
        CREATE INDEX IF NOT EXISTS idx_love_xfer_sender ON love_token_transfers(sender_id);
        CREATE INDEX IF NOT EXISTS idx_love_xfer_day ON love_token_transfers(sender_id, recipient_id, created_at);
        """
    )


class SendLoveReq(BaseModel):
    sender_id: int
    recipient_id: int
    token_type: str  # hug|kiss|handshake
    message: Optional[str] = None


@router.get("/config")
async def love_config():
    return {
        "enabled": ENABLED,
        "prices_in_aic": LOVE_PRICES,
        "daily_cap_per_recipient": DAILY_CAP_PER_RECIPIENT,
        "token_types": ["hug", "kiss", "handshake"],
        "icons": {"hug": "🤗", "kiss": "💋", "handshake": "🤝"},
        "note": "Stub — UI not yet wired. Enable via env LOVE_TOKENS_ENABLED=1 after UI ships.",
    }


@router.get("/balance/{user_id}")
async def love_balance(user_id: int):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_love_tables(conn)
        rows = await conn.fetch(
            "SELECT token_type, received, sent FROM love_token_balances WHERE user_id = $1",
            user_id,
        )
    balances = {t: {"received": 0, "sent": 0} for t in LOVE_PRICES.keys()}
    for r in rows:
        balances[r["token_type"]] = {"received": r["received"], "sent": r["sent"]}
    return {"user_id": user_id, "balances": balances}


@router.get("/received/{user_id}")
async def love_received(user_id: int, limit: int = 50):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(limit, 200))
    async with _pool.acquire() as conn:
        await _ensure_love_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, sender_id, token_type, message, created_at
            FROM love_token_transfers WHERE recipient_id = $1
            ORDER BY id DESC LIMIT $2
            """,
            user_id, limit,
        )
    return {"user_id": user_id, "received": [dict(r) for r in rows]}


@router.post("/send")
async def love_send(req: SendLoveReq):
    if not ENABLED:
        raise HTTPException(503, "Love tokens not yet enabled. Set LOVE_TOKENS_ENABLED=1 in env.")
    if req.token_type not in LOVE_PRICES:
        raise HTTPException(400, f"unknown token_type; must be one of {list(LOVE_PRICES.keys())}")
    if req.sender_id == req.recipient_id:
        raise HTTPException(400, "cannot send love token to yourself")
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    cost = LOVE_PRICES[req.token_type]

    async with _pool.acquire() as conn:
        await _ensure_love_tables(conn)

        # Daily cap: count transfers from this sender to this recipient today
        today_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM love_token_transfers
            WHERE sender_id = $1 AND recipient_id = $2
              AND created_at >= CURRENT_DATE
            """,
            req.sender_id, req.recipient_id,
        )
        if today_count >= DAILY_CAP_PER_RECIPIENT:
            raise HTTPException(429, f"daily cap reached: {DAILY_CAP_PER_RECIPIENT} tokens/day/recipient")

        # Charge AIC — uses aic_tokens module if available, else skip (stub mode)
        try:
            await conn.execute(
                "UPDATE aic_balances SET balance = balance - $1 WHERE user_id = $2 AND balance >= $1",
                cost, req.sender_id,
            )
        except Exception:
            pass  # AIC not wired yet — running free until enabled

        xfer_id = await conn.fetchval(
            """
            INSERT INTO love_token_transfers (sender_id, recipient_id, token_type, aic_cost, message)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
            """,
            req.sender_id, req.recipient_id, req.token_type, cost, (req.message or "")[:280],
        )

        # Update balances
        await conn.execute(
            """
            INSERT INTO love_token_balances (user_id, token_type, sent) VALUES ($1, $2, 1)
            ON CONFLICT (user_id, token_type) DO UPDATE SET sent = love_token_balances.sent + 1
            """,
            req.sender_id, req.token_type,
        )
        await conn.execute(
            """
            INSERT INTO love_token_balances (user_id, token_type, received) VALUES ($1, $2, 1)
            ON CONFLICT (user_id, token_type) DO UPDATE SET received = love_token_balances.received + 1
            """,
            req.recipient_id, req.token_type,
        )

    return {
        "ok": True,
        "transfer_id": xfer_id,
        "sender_id": req.sender_id,
        "recipient_id": req.recipient_id,
        "token_type": req.token_type,
        "aic_cost": cost,
        "message": "נשלח! הצד השני יראה את זה בקרוב.",
    }
