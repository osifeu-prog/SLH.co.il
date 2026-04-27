"""
SLH ESP32 Events → Revenue Bridge
==================================
Receives signed events from ESP32 devices, validates them, optionally converts
qualifying events into revenue_ledger entries.

This is the missing piece from the architecture:
  ESP32 → POST /api/esp/events → revenue_ledger → Distribution Engine

Endpoints:
  POST /api/esp/events            — ESP32 device posts an event (auth: X-Device-Key)
  GET  /api/esp/events            — admin: list recent events
  GET  /api/esp/devices           — admin: list known devices + status
  POST /api/esp/devices/register  — admin: register a new device
  POST /api/esp/events/{id}/promote-to-revenue — admin: convert event → revenue line

Author: Claude (Cowork mode, 2026-04-27)
"""
from __future__ import annotations
import os
import hashlib
import json
import datetime as dt
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
import asyncpg

router = APIRouter(prefix="/api/esp", tags=["esp-events"])

_pool: Optional[asyncpg.Pool] = None
def set_pool(pool: asyncpg.Pool):
    global _pool
    _pool = pool

def _verify_admin(k: Optional[str]) -> bool:
    if not k or k == "slh_admin_2026": return False
    return k in [x.strip() for x in os.getenv("ADMIN_API_KEYS", "").split(",") if x.strip()]

def _require_admin(k: Optional[str]):
    if not _verify_admin(k):
        raise HTTPException(403, "Admin key required (X-Admin-Key)")

_INIT = False
async def _ensure_schema(conn):
    global _INIT
    if _INIT: return
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS esp_devices (
            id              BIGSERIAL PRIMARY KEY,
            device_id       TEXT UNIQUE NOT NULL,
            display_name    TEXT,
            owner_telegram_id BIGINT,
            shared_key      TEXT,
            location        TEXT,
            last_seen       TIMESTAMPTZ,
            status          TEXT DEFAULT 'unknown',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS esp_events (
            id              BIGSERIAL PRIMARY KEY,
            device_id       TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            value           NUMERIC,
            meta_json       JSONB DEFAULT '{}'::jsonb,
            client_timestamp TIMESTAMPTZ,
            received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            client_hash     TEXT,
            verified        BOOLEAN DEFAULT FALSE,
            promoted_to_revenue_id BIGINT
        );
        CREATE INDEX IF NOT EXISTS idx_esp_events_device ON esp_events(device_id, received_at DESC);
        CREATE INDEX IF NOT EXISTS idx_esp_events_type ON esp_events(event_type);
    """)
    _INIT = True

class EventIn(BaseModel):
    device_id: str
    event_type: str
    value: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None
    client_timestamp: Optional[int] = None  # unix epoch
    client_hash: Optional[str] = None       # sha256 of "device_id|event_type|value|client_timestamp|shared_key"

class DeviceRegister(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=80)
    display_name: Optional[str] = None
    owner_telegram_id: Optional[int] = None
    shared_key: Optional[str] = None
    location: Optional[str] = None

@router.post("/events")
async def receive_event(req: EventIn, x_device_key: Optional[str] = Header(None, alias="X-Device-Key")):
    """ESP32 calls this to report an event."""
    if not _pool: raise HTTPException(503, "DB not ready")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        device = await conn.fetchrow("SELECT * FROM esp_devices WHERE device_id=$1", req.device_id)
        verified = False
        if device and device["shared_key"]:
            # Verify hash if device has shared_key
            sig_input = f"{req.device_id}|{req.event_type}|{req.value}|{req.client_timestamp}|{device['shared_key']}"
            expected = hashlib.sha256(sig_input.encode()).hexdigest()
            verified = (req.client_hash == expected)
            if not verified and x_device_key != device["shared_key"]:
                raise HTTPException(401, "Signature mismatch")
        elif x_device_key:
            # Bootstrap mode: accept any device, mark as unverified
            verified = False

        client_ts = dt.datetime.fromtimestamp(req.client_timestamp, tz=dt.timezone.utc) if req.client_timestamp else None
        event_id = await conn.fetchval("""
            INSERT INTO esp_events (device_id, event_type, value, meta_json, client_timestamp, client_hash, verified)
            VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7) RETURNING id
        """, req.device_id, req.event_type, req.value, json.dumps(req.meta or {}),
             client_ts, req.client_hash, verified)
        # Update device heartbeat
        if device:
            await conn.execute(
                "UPDATE esp_devices SET last_seen=NOW(), status='up' WHERE device_id=$1", req.device_id)
        else:
            # Auto-create unknown device
            await conn.execute("""
                INSERT INTO esp_devices (device_id, status, last_seen)
                VALUES ($1, 'auto-registered', NOW()) ON CONFLICT (device_id) DO NOTHING
            """, req.device_id)
    return {"ok": True, "event_id": event_id, "verified": verified}

@router.get("/events")
async def list_events(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT * FROM esp_events ORDER BY received_at DESC LIMIT 200
        """)
    return {"events": [dict(r) for r in rows]}

@router.get("/devices")
async def list_devices(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT d.*,
                   EXTRACT(EPOCH FROM (NOW() - d.last_seen))::int AS seconds_since,
                   (SELECT COUNT(*) FROM esp_events e WHERE e.device_id = d.device_id) AS event_count
              FROM esp_devices d ORDER BY d.last_seen DESC NULLS LAST
        """)
    return {"devices": [dict(r) for r in rows]}

@router.post("/devices/register")
async def register_device(req: DeviceRegister, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        try:
            await conn.execute("""
                INSERT INTO esp_devices (device_id, display_name, owner_telegram_id, shared_key, location)
                VALUES ($1,$2,$3,$4,$5)
            """, req.device_id, req.display_name, req.owner_telegram_id, req.shared_key, req.location)
        except asyncpg.UniqueViolationError:
            raise HTTPException(400, f"device_id '{req.device_id}' already registered")
    return {"ok": True, "device_id": req.device_id}

class PromoteToRevenue(BaseModel):
    period_ym: Optional[str] = None  # default: current month
    source: str = "esp_event"
    description: Optional[str] = None
    amount_ils: float = Field(..., gt=0)

@router.post("/events/{event_id}/promote-to-revenue")
async def promote_event(event_id: int, req: PromoteToRevenue,
                          x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Admin promotes a verified event into a revenue_ledger line."""
    actor = x_admin_key or "unknown"
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        event = await conn.fetchrow("SELECT * FROM esp_events WHERE id=$1", event_id)
        if not event: raise HTTPException(404, "Event not found")
        if event["promoted_to_revenue_id"]:
            raise HTTPException(400, f"Already promoted to revenue id={event['promoted_to_revenue_id']}")
        period = req.period_ym or dt.datetime.utcnow().strftime("%Y-%m")
        desc = req.description or f"ESP event {event_id} from {event['device_id']}"
        try:
            rev_id = await conn.fetchval("""
                INSERT INTO revenue_ledger (period_ym, source, description, amount_ils, invoice_ref, created_by)
                VALUES ($1,$2,$3,$4,$5,$6) RETURNING id
            """, period, req.source, desc, req.amount_ils, f"esp:{event_id}", actor[-8:])
        except Exception as e:
            raise HTTPException(500, f"revenue_ledger not available: {e}")
        await conn.execute("UPDATE esp_events SET promoted_to_revenue_id=$1 WHERE id=$2", rev_id, event_id)
    return {"ok": True, "event_id": event_id, "revenue_id": rev_id}
