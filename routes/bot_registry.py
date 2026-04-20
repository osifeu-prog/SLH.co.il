"""
Bot Registry + Heartbeat

Provides a truthful "alive" signal for the 25-bot fleet. Any bot that
wants to count as "live" calls POST /api/bots/heartbeat every 30s.
The audit endpoint + dashboard then show active = (last_heartbeat_at > NOW() - 60s).

Endpoints:
  POST /api/bots/heartbeat     — bots call this periodically (secret-gated)
  GET  /api/bots/list          — admin view of all registered bots
  GET  /api/bots/active/count  — public count of bots alive in last 60s

Schema:
  bots (
    bot_name PK,               -- e.g. "ledger", "academia", "air"
    display_name,              -- "SLH Ledger", "SLH Academia"
    username,                  -- "@SLH_ledger_bot"
    version,                   -- from bot's own version tag
    last_heartbeat_at,         -- NOW() when bot POSTs /heartbeat
    first_seen_at,
    status,                    -- 'active' / 'stopped' / 'unknown'
    metadata JSONB             -- free-form: uptime_s, memory_mb, custom fields
  )

Activity rule:
  active = (last_heartbeat_at >= NOW() - INTERVAL '60 seconds')
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/bots", tags=["Bot Registry"])

_pool = None

# Shared secret — bots pass this in `X-Bot-Secret` header. Defaults to BOT_SYNC_SECRET
# (same env var used by the bot-sync auth flow). Falls back to a dev default.
BOT_SECRET = os.getenv("BOT_SYNC_SECRET", "slh_bot_heartbeat_2026")

# Admin keys — for /list (read all). Reuses the main API's admin keys.
ADMIN_KEYS_RAW = os.getenv("ADMIN_API_KEYS") or ""
_ADMIN_KEYS = {k.strip() for k in ADMIN_KEYS_RAW.split(",") if k.strip()}
# If ADMIN_API_KEYS env is unset, leave _ADMIN_KEYS empty — admin calls will fail 403
# (safer than falling back to a public default; set ADMIN_API_KEYS on Railway for prod).


def set_pool(pool):
    global _pool
    _pool = pool


async def init_tables():
    """Create bots table if missing. Safe to call multiple times."""
    if _pool is None:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bots (
                bot_name           TEXT PRIMARY KEY,
                display_name       TEXT,
                username           TEXT,
                version            TEXT,
                status             TEXT DEFAULT 'unknown',
                last_heartbeat_at  TIMESTAMPTZ,
                first_seen_at      TIMESTAMPTZ DEFAULT NOW(),
                metadata           JSONB DEFAULT '{}'::jsonb
            )
            """
        )
        # Index for the activity query — used by /active/count and /api/system/audit
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_bots_last_heartbeat ON bots(last_heartbeat_at DESC)"
        )


# ──────────────── Models ────────────────

class HeartbeatReq(BaseModel):
    bot_name: str
    display_name: Optional[str] = None
    username: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[dict] = None


# ──────────────── Endpoints ────────────────

@router.post("/heartbeat")
async def heartbeat(
    req: HeartbeatReq,
    x_bot_secret: Optional[str] = Header(default=None, alias="X-Bot-Secret"),
):
    """
    A bot calls this every 30s to prove it's alive.

    Auth: `X-Bot-Secret` must match BOT_SYNC_SECRET env var. This stops
    random clients from inflating the "active bots" number.

    Upserts on bot_name. Updates last_heartbeat_at = NOW(), status = 'active'.
    """
    if x_bot_secret != BOT_SECRET:
        raise HTTPException(status_code=401, detail="invalid bot secret")

    if not req.bot_name or len(req.bot_name) > 64:
        raise HTTPException(status_code=400, detail="bot_name required (<=64 chars)")

    if _pool is None:
        raise HTTPException(status_code=503, detail="db pool not initialized")

    import json
    meta_json = json.dumps(req.metadata or {})

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO bots (bot_name, display_name, username, version, status,
                              last_heartbeat_at, first_seen_at, metadata)
            VALUES ($1, $2, $3, $4, 'active', NOW(), NOW(), $5::jsonb)
            ON CONFLICT (bot_name) DO UPDATE SET
                display_name = COALESCE(EXCLUDED.display_name, bots.display_name),
                username     = COALESCE(EXCLUDED.username,     bots.username),
                version      = COALESCE(EXCLUDED.version,      bots.version),
                status       = 'active',
                last_heartbeat_at = NOW(),
                metadata     = COALESCE(EXCLUDED.metadata, bots.metadata)
            """,
            req.bot_name,
            req.display_name,
            req.username,
            req.version,
            meta_json,
        )
    return {"ok": True, "bot_name": req.bot_name, "recorded_at": datetime.utcnow().isoformat()}


@router.get("/active/count")
async def active_count():
    """Public: number of bots that heartbeat-ed in the last 60s."""
    if _pool is None:
        return {"active": 0, "total_registered": 0, "window_seconds": 60}
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE last_heartbeat_at >= NOW() - INTERVAL '60 seconds') AS active,
                COUNT(*)                                                                    AS total_registered
            FROM bots
            """
        )
    return {
        "active": int(row["active"] or 0),
        "total_registered": int(row["total_registered"] or 0),
        "window_seconds": 60,
    }


@router.get("/list")
async def list_bots(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    """Admin: full list of registered bots with activity flag."""
    if x_admin_key not in _ADMIN_KEYS:
        raise HTTPException(status_code=401, detail="admin key required")

    if _pool is None:
        return {"bots": [], "total": 0, "active": 0}

    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT bot_name, display_name, username, version, status,
                   last_heartbeat_at, first_seen_at, metadata,
                   (last_heartbeat_at >= NOW() - INTERVAL '60 seconds') AS is_active,
                   EXTRACT(EPOCH FROM (NOW() - last_heartbeat_at))::INT AS seconds_since_heartbeat
            FROM bots
            ORDER BY last_heartbeat_at DESC NULLS LAST, bot_name
            """
        )

    bots = []
    active = 0
    for r in rows:
        is_act = bool(r["is_active"])
        if is_act:
            active += 1
        bots.append({
            "bot_name": r["bot_name"],
            "display_name": r["display_name"],
            "username": r["username"],
            "version": r["version"],
            "status": r["status"],
            "last_heartbeat_at": r["last_heartbeat_at"].isoformat() if r["last_heartbeat_at"] else None,
            "first_seen_at": r["first_seen_at"].isoformat() if r["first_seen_at"] else None,
            "metadata": r["metadata"] or {},
            "is_active": is_act,
            "seconds_since_heartbeat": r["seconds_since_heartbeat"],
        })

    return {"bots": bots, "total": len(bots), "active": active}


@router.delete("/{bot_name}")
async def remove_bot(
    bot_name: str,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    """Admin: remove a bot from the registry (e.g. decommissioned)."""
    if x_admin_key not in _ADMIN_KEYS:
        raise HTTPException(status_code=401, detail="admin key required")
    if _pool is None:
        raise HTTPException(status_code=503, detail="db pool not initialized")
    async with _pool.acquire() as conn:
        result = await conn.execute("DELETE FROM bots WHERE bot_name=$1", bot_name)
    return {"ok": True, "deleted": bot_name, "affected": result}
