"""
SLH Command Center — System Status Router
==========================================
Unified status + control endpoints for the Command Center UI.

Endpoints:
  GET  /api/system/status              — overall ecosystem health snapshot
  GET  /api/system/bots                — live bot status (heartbeats from DB)
  GET  /api/system/stats               — aggregated KPIs for the dashboard
  POST /api/system/bots/heartbeat      — bots call this every 30s to register liveness
  POST /api/system/bots/restart        — admin-only: signal a bot to restart (writes intent to DB)
  POST /api/system/bots/stop           — admin-only: signal a bot to stop
  POST /api/system/bots/logs           — admin-only: returns last N log lines (placeholder)
  POST /api/system/emergency-pause     — admin-only: signal ALL bots to pause

Architecture:
  This router is the **glue** between Command Center UI and the rest of the system.
  It does NOT directly run/stop containers — instead it writes intents to a DB table
  (`bot_control_intents`) which the orchestrator script polls and executes locally.
  This keeps the API stateless and the orchestrator simple.

DB tables touched (auto-created on first call):
  - bot_heartbeats       (bot_name, last_seen, status, version, container_id, meta_json)
  - bot_control_intents  (id, bot_name, action, requested_by, requested_at, executed_at, result)

Author: Claude (Cowork mode session, 2026-04-27)
"""
from __future__ import annotations
import os
import json
import time
import datetime as dt
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Body
from pydantic import BaseModel
import asyncpg

router = APIRouter(prefix="/api/system", tags=["system"])

# ─────────────────────────────────────────────────────────────────
# Pool injection (set by main.py at startup, like other routers)
# ─────────────────────────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None
def set_pool(pool: asyncpg.Pool):
    global _pool
    _pool = pool

# ─────────────────────────────────────────────────────────────────
# Expected bots (canonical list)
# ─────────────────────────────────────────────────────────────────
EXPECTED_BOTS = [
    "core-bot", "guardian-bot", "botshop", "wallet-bot", "factory-bot",
    "fun-bot", "admin-bot", "airdrop-bot", "campaign-bot", "game-bot",
    "ton-mnh-bot", "slh-ton-bot", "ledger-bot", "osif-shop-bot", "nifti-bot",
    "chance-bot", "nfty-bot", "ts-set-bot", "crazy-panel-bot", "nft-shop-bot",
    "beynonibank-bot", "test-bot", "claude-bot", "academia-bot", "expertnet-bot",
]

# ─────────────────────────────────────────────────────────────────
# DB schema (idempotent — safe to call repeatedly)
# ─────────────────────────────────────────────────────────────────
_SCHEMA_INITIALIZED = False
async def _ensure_schema(conn):
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED:
        return
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_heartbeats (
            bot_name      TEXT PRIMARY KEY,
            last_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status        TEXT NOT NULL DEFAULT 'up',
            version       TEXT,
            container_id  TEXT,
            meta_json     JSONB DEFAULT '{}'::jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_bot_heartbeats_last_seen ON bot_heartbeats(last_seen DESC);

        CREATE TABLE IF NOT EXISTS bot_control_intents (
            id            BIGSERIAL PRIMARY KEY,
            bot_name      TEXT NOT NULL,
            action        TEXT NOT NULL CHECK (action IN ('restart', 'stop', 'start', 'pause', 'logs')),
            requested_by  BIGINT,
            requested_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            executed_at   TIMESTAMPTZ,
            result        TEXT,
            payload_json  JSONB DEFAULT '{}'::jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_intents_pending ON bot_control_intents(executed_at) WHERE executed_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_intents_bot ON bot_control_intents(bot_name, requested_at DESC);
    """)
    _SCHEMA_INITIALIZED = True

# ─────────────────────────────────────────────────────────────────
# Auth helper (matches the X-Admin-Key pattern used elsewhere)
# ─────────────────────────────────────────────────────────────────
def _verify_admin(x_admin_key: Optional[str]) -> bool:
    """Return True if the provided admin key is valid."""
    if not x_admin_key:
        return False
    env_keys_str = os.getenv("ADMIN_API_KEYS", "")
    env_keys = [k.strip() for k in env_keys_str.split(",") if k.strip()]
    # Reject the legacy default — security
    if x_admin_key == "slh_admin_2026":
        return False
    return x_admin_key in env_keys

def _require_admin(x_admin_key: Optional[str]):
    if not _verify_admin(x_admin_key):
        raise HTTPException(403, "Admin key required (X-Admin-Key header). Default key 'slh_admin_2026' is rejected.")


# ═════════════════════════════════════════════════════════════════
# READ ENDPOINTS (no auth — public health/status)
# ═════════════════════════════════════════════════════════════════

@router.get("/status")
async def system_status():
    """One-shot ecosystem health snapshot.

    Returns: {
      ok, api_up, db_up, bots: {expected, online, down, last_check},
      timestamp_iso, version
    }
    """
    if not _pool:
        return {"ok": False, "error": "DB pool not initialized"}
    try:
        async with _pool.acquire() as conn:
            await _ensure_schema(conn)
            # DB ping
            await conn.fetchval("SELECT 1")
            # Bot status: any bot with last_seen < 90s ago is "up"
            rows = await conn.fetch("""
                SELECT bot_name, status,
                       EXTRACT(EPOCH FROM (NOW() - last_seen))::int AS seconds_since
                  FROM bot_heartbeats
            """)
        online = sum(1 for r in rows if r["seconds_since"] < 90 and r["status"] == "up")
        down   = sum(1 for r in rows if r["seconds_since"] >= 90 or r["status"] != "up")
        unknown = max(0, len(EXPECTED_BOTS) - len(rows))
        return {
            "ok": True,
            "api_up": True,
            "db_up": True,
            "bots": {
                "expected": len(EXPECTED_BOTS),
                "online": online,
                "down": down,
                "unknown": unknown,
                "last_check": dt.datetime.utcnow().isoformat() + "Z",
            },
            "timestamp_iso": dt.datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "api_up": True, "db_up": False}


@router.get("/bots")
async def bots_status():
    """Live status of all bots.

    Returns: { bots: [{name, container, status, last_seen, version, seconds_since}], ... }
    Bots not in heartbeats table are returned with status='unknown'.
    """
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT bot_name, last_seen, status, version, container_id,
                   EXTRACT(EPOCH FROM (NOW() - last_seen))::int AS seconds_since
              FROM bot_heartbeats
        """)
    by_name: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        seconds = int(r["seconds_since"])
        # If we haven't seen the bot in 90s, mark it as down even if it last said 'up'
        live_status = r["status"] if seconds < 90 else "down"
        by_name[r["bot_name"]] = {
            "name": r["bot_name"],
            "status": live_status,
            "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
            "seconds_since": seconds,
            "version": r["version"],
            "container_id": r["container_id"],
        }
    bots: List[Dict[str, Any]] = []
    for name in EXPECTED_BOTS:
        if name in by_name:
            bots.append(by_name[name])
        else:
            bots.append({"name": name, "status": "unknown", "last_seen": None, "seconds_since": None})
    return {"bots": bots, "timestamp_iso": dt.datetime.utcnow().isoformat() + "Z"}


@router.get("/stats")
async def system_stats():
    """Aggregated KPIs for the Command Center dashboard.

    Returns counts that exist; missing ones are simply absent (graceful).
    """
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    out: Dict[str, Any] = {}
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        # Try each — failures are non-fatal
        try:
            out["users_total"] = await conn.fetchval("SELECT COUNT(*) FROM web_users")
        except Exception:
            try:
                out["users_total"] = await conn.fetchval("SELECT COUNT(*) FROM users")
            except Exception:
                pass
        try:
            out["users_active_24h"] = await conn.fetchval(
                "SELECT COUNT(*) FROM web_users WHERE last_login > NOW() - INTERVAL '24 hours'"
            )
        except Exception:
            pass
        try:
            out["devices_total"] = await conn.fetchval("SELECT COUNT(*) FROM devices")
        except Exception:
            try:
                out["devices_total"] = await conn.fetchval("SELECT COUNT(*) FROM device_registry")
            except Exception:
                out["devices_total"] = 0
        try:
            out["transactions_total"] = await conn.fetchval("SELECT COUNT(*) FROM transactions")
        except Exception:
            try:
                out["transactions_total"] = await conn.fetchval("SELECT COUNT(*) FROM ledger")
            except Exception:
                pass
        try:
            out["tables"] = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'"
            )
        except Exception:
            pass
    out["timestamp_iso"] = dt.datetime.utcnow().isoformat() + "Z"
    return out


# ═════════════════════════════════════════════════════════════════
# HEARTBEAT (called by bots themselves — auth via shared secret)
# ═════════════════════════════════════════════════════════════════

class HeartbeatRequest(BaseModel):
    bot_name: str
    status: str = "up"           # "up" | "warn" | "down"
    version: Optional[str] = None
    container_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

@router.post("/bots/heartbeat")
async def bot_heartbeat(
    req: HeartbeatRequest,
    x_bot_key: Optional[str] = Header(None, alias="X-Bot-Key"),
):
    """Bots call this every ~30s to report they're alive.

    Auth via X-Bot-Key header matching env var BOT_HEARTBEAT_KEY.
    If env var is not set, accepts unauthenticated calls (dev mode).
    """
    expected_key = os.getenv("BOT_HEARTBEAT_KEY", "")
    if expected_key and x_bot_key != expected_key:
        raise HTTPException(401, "Invalid bot key")
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    if req.bot_name not in EXPECTED_BOTS:
        # Don't reject — just log the unexpected bot. Useful for new bots.
        print(f"[system_status] Heartbeat from unexpected bot: {req.bot_name}")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        await conn.execute("""
            INSERT INTO bot_heartbeats (bot_name, last_seen, status, version, container_id, meta_json)
            VALUES ($1, NOW(), $2, $3, $4, $5::jsonb)
            ON CONFLICT (bot_name) DO UPDATE SET
                last_seen = NOW(),
                status = EXCLUDED.status,
                version = COALESCE(EXCLUDED.version, bot_heartbeats.version),
                container_id = COALESCE(EXCLUDED.container_id, bot_heartbeats.container_id),
                meta_json = EXCLUDED.meta_json
        """, req.bot_name, req.status, req.version, req.container_id,
             json.dumps(req.meta or {}))
    return {"ok": True, "bot": req.bot_name, "received_at": dt.datetime.utcnow().isoformat() + "Z"}


# ═════════════════════════════════════════════════════════════════
# CONTROL ENDPOINTS (admin-only)
# ═════════════════════════════════════════════════════════════════

class BotControlRequest(BaseModel):
    bot: str
    payload: Optional[Dict[str, Any]] = None

async def _enqueue_intent(bot_name: str, action: str, payload: Optional[Dict[str, Any]] = None):
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    if bot_name not in EXPECTED_BOTS and bot_name != "*":
        raise HTTPException(400, f"Unknown bot: {bot_name}")
    if action not in ("restart", "stop", "start", "pause", "logs"):
        raise HTTPException(400, f"Unknown action: {action}")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        intent_id = await conn.fetchval("""
            INSERT INTO bot_control_intents (bot_name, action, payload_json)
            VALUES ($1, $2, $3::jsonb)
            RETURNING id
        """, bot_name, action, json.dumps(payload or {}))
    return intent_id

@router.post("/bots/restart")
async def restart_bot(
    req: BotControlRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _require_admin(x_admin_key)
    intent_id = await _enqueue_intent(req.bot, "restart", req.payload)
    return {"ok": True, "intent_id": intent_id, "message": f"Restart intent queued for {req.bot}"}

@router.post("/bots/stop")
async def stop_bot(
    req: BotControlRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _require_admin(x_admin_key)
    intent_id = await _enqueue_intent(req.bot, "stop", req.payload)
    return {"ok": True, "intent_id": intent_id, "message": f"Stop intent queued for {req.bot}"}

@router.post("/bots/logs")
async def bot_logs(
    req: BotControlRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Request the last N log lines from a bot. Currently a stub — orchestrator picks this up."""
    _require_admin(x_admin_key)
    intent_id = await _enqueue_intent(req.bot, "logs", req.payload or {"lines": 100})
    return {"ok": True, "intent_id": intent_id, "message": f"Logs request queued for {req.bot}"}


class EmergencyPauseRequest(BaseModel):
    reason: Optional[str] = None

@router.post("/emergency-pause")
async def emergency_pause(
    req: EmergencyPauseRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Signal ALL bots to pause. Used in incident response."""
    _require_admin(x_admin_key)
    intent_id = await _enqueue_intent("*", "pause", {"reason": req.reason})
    return {
        "ok": True,
        "intent_id": intent_id,
        "message": "Emergency pause queued for ALL bots. Orchestrator will execute within 60s.",
    }


# ═════════════════════════════════════════════════════════════════
# ORCHESTRATOR-FACING ENDPOINTS
# (called by the local PowerShell/Python orchestrator that polls intents)
# ═════════════════════════════════════════════════════════════════

@router.get("/intents/pending")
async def pending_intents(
    x_orchestrator_key: Optional[str] = Header(None, alias="X-Orchestrator-Key"),
):
    """Return all unexecuted control intents. Orchestrator polls this every 15s."""
    expected_key = os.getenv("ORCHESTRATOR_KEY", "")
    if not expected_key:
        raise HTTPException(503, "ORCHESTRATOR_KEY env var not configured")
    if x_orchestrator_key != expected_key:
        raise HTTPException(401, "Invalid orchestrator key")
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT id, bot_name, action, requested_at, payload_json
              FROM bot_control_intents
             WHERE executed_at IS NULL
             ORDER BY requested_at ASC
             LIMIT 50
        """)
    return {
        "intents": [
            {
                "id": r["id"],
                "bot": r["bot_name"],
                "action": r["action"],
                "requested_at": r["requested_at"].isoformat(),
                "payload": r["payload_json"],
            }
            for r in rows
        ]
    }


class IntentResultRequest(BaseModel):
    intent_id: int
    result: str   # "ok" | "failed" | "partial"
    output: Optional[str] = None

@router.post("/intents/result")
async def intent_result(
    req: IntentResultRequest,
    x_orchestrator_key: Optional[str] = Header(None, alias="X-Orchestrator-Key"),
):
    expected_key = os.getenv("ORCHESTRATOR_KEY", "")
    if not expected_key or x_orchestrator_key != expected_key:
        raise HTTPException(401, "Invalid orchestrator key")
    if not _pool:
        raise HTTPException(503, "DB pool not initialized")
    payload = json.dumps({"output": req.output}) if req.output else "{}"
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        await conn.execute("""
            UPDATE bot_control_intents
               SET executed_at = NOW(),
                   result = $1,
                   payload_json = payload_json || $2::jsonb
             WHERE id = $3
        """, req.result, payload, req.intent_id)
    return {"ok": True}
