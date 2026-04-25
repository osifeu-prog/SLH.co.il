"""SLH Swarm — independent device mesh API.

Implements the Phase-1 endpoints from `ops/SWARM_V1_BLUEPRINT_20260424.md`.

Mesh topology (no router required):
    ESP <--ESP-NOW--> ESP <--BLE/WiFi--> Phone (relay) <--HTTPS--> this API

Devices register, beat heartbeats, log events, and poll for commands.
Two tables: swarm_devices, swarm_events, swarm_commands. Created on first hit.

NOT business logic — just the mesh state plane. Tokens/payments stay in main.py.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

log = logging.getLogger("slh.swarm")

router = APIRouter(prefix="/api/swarm", tags=["swarm"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DeviceRegisterReq(BaseModel):
    device_id: str = Field(..., max_length=64)
    public_key_hex: str = Field(..., min_length=32, max_length=256)
    device_type: str = Field("wallet")  # wallet | sensor | beacon | bridge
    owner_user_id: Optional[int] = None
    metadata: Optional[dict] = None


class HeartbeatReq(BaseModel):
    device_id: str
    rssi: Optional[int] = None
    battery_pct: Optional[int] = None
    free_heap: Optional[int] = None
    fw: Optional[str] = None
    peers_seen: Optional[list[str]] = None  # MACs of mesh peers visible
    relay_via: Optional[str] = None  # device_id or phone-id of upstream relay


class EventReq(BaseModel):
    device_id: str
    event_type: str = Field(..., max_length=64)
    payload: Optional[dict] = None
    event_id: Optional[str] = None  # idempotency key (UUID from device)


class CommandQueueReq(BaseModel):
    target_device: str
    command_type: str
    payload: Optional[dict] = None
    ttl_seconds: Optional[int] = 300


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

_SCHEMA_READY = False


async def _ensure_schema(pool) -> None:
    """Idempotent. Creates the 3 swarm tables if missing."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS swarm_devices (
                device_id        TEXT PRIMARY KEY,
                owner_user_id    BIGINT,
                public_key_hex   TEXT NOT NULL,
                device_type      TEXT NOT NULL DEFAULT 'wallet',
                registered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_heartbeat   TIMESTAMPTZ,
                last_rssi        INT,
                last_battery_pct INT,
                status           TEXT NOT NULL DEFAULT 'active',
                metadata         JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS swarm_events (
                id          BIGSERIAL PRIMARY KEY,
                event_id    TEXT UNIQUE,
                device_id   TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_swarm_events_device_at ON swarm_events (device_id, created_at DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_swarm_events_type ON swarm_events (event_type, created_at DESC)"
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS swarm_commands (
                id              BIGSERIAL PRIMARY KEY,
                command_id      TEXT UNIQUE,
                target_device   TEXT NOT NULL,
                command_type    TEXT NOT NULL,
                payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at      TIMESTAMPTZ,
                delivered_at    TIMESTAMPTZ,
                ack_at          TIMESTAMPTZ,
                ack_payload     JSONB
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_swarm_commands_target_pending ON swarm_commands (target_device) WHERE delivered_at IS NULL"
        )
    _SCHEMA_READY = True


def _pool(request: Request):
    """Pool accessor — falls back gracefully if app.state.db_pool is missing."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


def _emit_event_to_log(pool, event_type: str, payload: dict) -> None:
    """Fire-and-forget public event for /api/events/public."""
    try:
        from shared.events import emit as _emit
        import asyncio
        asyncio.create_task(_emit(pool, event_type, payload, source="api.swarm"))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/devices/register")
async def register_device(req: DeviceRegisterReq, request: Request):
    """Register or upsert a swarm device. Returns the persisted record."""
    pool = _pool(request)
    await _ensure_schema(pool)

    if not req.device_id or len(req.device_id) > 64:
        raise HTTPException(400, "device_id required, max 64 chars")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO swarm_devices (device_id, owner_user_id, public_key_hex, device_type, metadata)
            VALUES ($1, $2, $3, $4, COALESCE($5::jsonb, '{}'::jsonb))
            ON CONFLICT (device_id) DO UPDATE SET
                public_key_hex = EXCLUDED.public_key_hex,
                device_type    = EXCLUDED.device_type,
                metadata       = swarm_devices.metadata || EXCLUDED.metadata,
                status         = CASE WHEN swarm_devices.status = 'revoked'
                                      THEN swarm_devices.status
                                      ELSE EXCLUDED.metadata::jsonb->>'force_status' END
            RETURNING device_id, owner_user_id, device_type, registered_at, status
            """,
            req.device_id,
            req.owner_user_id,
            req.public_key_hex,
            req.device_type,
            __import__("json").dumps(req.metadata or {}),
        )

    _emit_event_to_log(
        pool,
        "swarm.device_registered",
        {"device_id": req.device_id, "device_type": req.device_type},
    )

    return {
        "ok": True,
        "device_id": row["device_id"],
        "device_type": row["device_type"],
        "registered_at": row["registered_at"].isoformat() if row["registered_at"] else None,
        "status": row["status"] or "active",
    }


@router.post("/devices/heartbeat")
async def heartbeat(req: HeartbeatReq, request: Request):
    """Update device liveness + (optionally) log peers seen for mesh map."""
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE swarm_devices
               SET last_heartbeat = NOW(),
                   last_rssi = COALESCE($2, last_rssi),
                   last_battery_pct = COALESCE($3, last_battery_pct)
             WHERE device_id = $1
            """,
            req.device_id,
            req.rssi,
            req.battery_pct,
        )
        # If 0 rows updated, device isn't registered — auto-register as 'unknown'
        if result.endswith("UPDATE 0"):
            return {"ok": False, "error": "device_not_registered", "hint": "POST /api/swarm/devices/register first"}

        # Log peers + relay path as an event so the mesh map can be reconstructed
        if req.peers_seen or req.relay_via:
            await conn.execute(
                """
                INSERT INTO swarm_events (event_id, device_id, event_type, payload)
                VALUES ($1, $2, 'mesh.topology', $3::jsonb)
                """,
                f"hb-{req.device_id}-{int(time.time() * 1000)}",
                req.device_id,
                __import__("json").dumps({
                    "peers_seen": req.peers_seen or [],
                    "relay_via": req.relay_via,
                    "fw": req.fw,
                    "free_heap": req.free_heap,
                }),
            )

    return {"ok": True, "ts": time.time()}


@router.post("/events")
async def post_event(req: EventReq, request: Request):
    """Log a mesh event (alert, button-press, sensor reading, signed-tx, etc.)."""
    pool = _pool(request)
    await _ensure_schema(pool)

    event_id = req.event_id or f"evt-{secrets.token_hex(8)}"
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO swarm_events (event_id, device_id, event_type, payload)
                VALUES ($1, $2, $3, $4::jsonb)
                ON CONFLICT (event_id) DO NOTHING
                """,
                event_id,
                req.device_id,
                req.event_type,
                __import__("json").dumps(req.payload or {}),
            )
        except Exception as e:
            raise HTTPException(500, f"insert failed: {e}")

    # Mirror to public event_log so /api/events/public shows mesh activity
    _emit_event_to_log(
        pool,
        f"swarm.{req.event_type}",
        {"device_id": req.device_id, "event_id": event_id, **(req.payload or {})},
    )
    return {"ok": True, "event_id": event_id}


@router.get("/devices/{device_id}/commands")
async def poll_commands(device_id: str, request: Request, limit: int = Query(5, le=50)):
    """Device polls for commands queued for it. Marks them delivered atomically."""
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            UPDATE swarm_commands
               SET delivered_at = NOW()
             WHERE id IN (
                SELECT id FROM swarm_commands
                 WHERE target_device = $1
                   AND delivered_at IS NULL
                   AND (expires_at IS NULL OR expires_at > NOW())
                 ORDER BY created_at ASC
                 LIMIT $2
                 FOR UPDATE SKIP LOCKED
             )
            RETURNING command_id, command_type, payload, created_at
            """,
            device_id,
            limit,
        )

    return {
        "commands": [
            {
                "command_id": r["command_id"],
                "command_type": r["command_type"],
                "payload": r["payload"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ],
    }


@router.post("/commands/queue")
async def queue_command(
    req: CommandQueueReq,
    request: Request,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None),
):
    """Admin: queue a command for a device. Auth via X-Admin-Key (matches /api/admin/*)."""
    # Reuse the canonical admin verifier from main.py if available.
    try:
        from main import _require_admin
        _require_admin(authorization, x_admin_key)
    except Exception:
        # If main hasn't loaded us via include_router, fall back to env match.
        env_keys = {k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()}
        if not (x_admin_key and x_admin_key in env_keys):
            raise HTTPException(403, "Admin authentication required")

    pool = _pool(request)
    await _ensure_schema(pool)

    command_id = f"cmd-{secrets.token_hex(10)}"
    expires_at = None
    if req.ttl_seconds:
        # Postgres-side 'NOW() + interval' would be nicer but we want explicit timing
        from datetime import datetime, timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=req.ttl_seconds)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO swarm_commands (command_id, target_device, command_type, payload, expires_at)
            VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            command_id,
            req.target_device,
            req.command_type,
            __import__("json").dumps(req.payload or {}),
            expires_at,
        )

    return {"ok": True, "command_id": command_id, "expires_at": expires_at.isoformat() if expires_at else None}


@router.post("/commands/{command_id}/ack")
async def ack_command(command_id: str, request: Request, payload: Optional[dict] = None):
    """Device acknowledges executing a command + sends optional result payload."""
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE swarm_commands
               SET ack_at = NOW(),
                   ack_payload = $2::jsonb
             WHERE command_id = $1
            """,
            command_id,
            __import__("json").dumps(payload or {}),
        )
    if result.endswith("UPDATE 0"):
        raise HTTPException(404, "command not found")
    return {"ok": True}


@router.get("/devices")
async def list_devices(
    request: Request,
    limit: int = Query(50, le=200),
    owner_user_id: Optional[int] = None,
):
    """Public-ish list of swarm devices (no PII — just IDs, types, last heartbeat)."""
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        if owner_user_id is not None:
            rows = await conn.fetch(
                """
                SELECT device_id, device_type, registered_at, last_heartbeat, last_rssi,
                       last_battery_pct, status,
                       (NOW() - last_heartbeat) < INTERVAL '120 seconds' AS online
                  FROM swarm_devices
                 WHERE owner_user_id = $1
                 ORDER BY last_heartbeat DESC NULLS LAST
                 LIMIT $2
                """,
                owner_user_id,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT device_id, device_type, registered_at, last_heartbeat, last_rssi,
                       last_battery_pct, status,
                       (NOW() - last_heartbeat) < INTERVAL '120 seconds' AS online
                  FROM swarm_devices
                 ORDER BY last_heartbeat DESC NULLS LAST
                 LIMIT $1
                """,
                limit,
            )

    return {
        "count": len(rows),
        "devices": [
            {
                "device_id": r["device_id"],
                "device_type": r["device_type"],
                "registered_at": r["registered_at"].isoformat() if r["registered_at"] else None,
                "last_heartbeat": r["last_heartbeat"].isoformat() if r["last_heartbeat"] else None,
                "last_rssi": r["last_rssi"],
                "last_battery_pct": r["last_battery_pct"],
                "status": r["status"],
                "online": bool(r["online"]),
            }
            for r in rows
        ],
    }


@router.get("/stats")
async def stats(request: Request):
    """Snapshot of mesh health for dashboards."""
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        s = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM swarm_devices) AS total_devices,
                (SELECT COUNT(*) FROM swarm_devices
                  WHERE last_heartbeat > NOW() - INTERVAL '120 seconds') AS online,
                (SELECT COUNT(*) FROM swarm_events
                  WHERE created_at > NOW() - INTERVAL '24 hours') AS events_24h,
                (SELECT COUNT(*) FROM swarm_commands
                  WHERE delivered_at IS NULL
                    AND (expires_at IS NULL OR expires_at > NOW())) AS pending_commands
            """
        )
    return {
        "total_devices": int(s["total_devices"] or 0),
        "online": int(s["online"] or 0),
        "events_24h": int(s["events_24h"] or 0),
        "pending_commands": int(s["pending_commands"] or 0),
    }
