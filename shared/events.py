"""
SLH Event Bus — PostgreSQL-backed durable event log.

Writes to `event_log` table. Bots poll for new events by cursor (last_processed_id).
No Redis dependency — works anywhere the DB is reachable.

API:
    await emit(pool, "payment.cleared", {"user_id": 42, "token": "SLH", "amount": 100})
    async for evt in subscribe(pool, cursor=last_id, types=["payment.cleared"]):
        handle(evt)
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Optional


async def ensure_event_log_table(conn) -> None:
    """Create event_log table + index. Idempotent."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS event_log (
            id BIGSERIAL PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            source TEXT
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_event_log_type_id ON event_log(event_type, id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log(created_at)"
    )


async def emit(pool, event_type: str, payload: Optional[dict] = None, source: Optional[str] = None) -> int:
    """Append an event. Returns the new event id. Never raises on DB errors — logs and returns -1."""
    if payload is None:
        payload = {}
    try:
        async with pool.acquire() as conn:
            await ensure_event_log_table(conn)
            row = await conn.fetchrow(
                "INSERT INTO event_log (event_type, payload, source) VALUES ($1, $2::jsonb, $3) RETURNING id",
                event_type, json.dumps(payload), source
            )
            return int(row["id"])
    except Exception as e:
        print(f"[events.emit][WARN] failed to emit {event_type}: {e!r}")
        return -1


async def fetch_since(pool, cursor: int = 0, limit: int = 100, types: Optional[list] = None) -> list:
    """Return events with id > cursor. If types is set, filter by event_type IN (...)."""
    async with pool.acquire() as conn:
        await ensure_event_log_table(conn)
        if types:
            rows = await conn.fetch(
                "SELECT id, event_type, payload, created_at, source FROM event_log "
                "WHERE id > $1 AND event_type = ANY($2::text[]) ORDER BY id ASC LIMIT $3",
                cursor, types, limit
            )
        else:
            rows = await conn.fetch(
                "SELECT id, event_type, payload, created_at, source FROM event_log "
                "WHERE id > $1 ORDER BY id ASC LIMIT $2",
                cursor, limit
            )
        return [
            {
                "id": r["id"],
                "type": r["event_type"],
                "payload": r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"]),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "source": r["source"],
            }
            for r in rows
        ]


async def subscribe(pool, cursor: int = 0, types: Optional[list] = None, poll_interval: float = 3.0) -> AsyncIterator[dict]:
    """Async generator — yields events as they arrive. Caller tracks cursor."""
    current = cursor
    while True:
        events = await fetch_since(pool, current, limit=50, types=types)
        for evt in events:
            yield evt
            current = evt["id"]
        await asyncio.sleep(poll_interval)


async def get_latest_id(pool) -> int:
    """Current max event id. Useful for subscribers that want only new events from now on."""
    async with pool.acquire() as conn:
        await ensure_event_log_table(conn)
        val = await conn.fetchval("SELECT COALESCE(MAX(id), 0) FROM event_log")
        return int(val)
