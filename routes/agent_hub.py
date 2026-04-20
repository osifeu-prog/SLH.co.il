"""
Agent Hub — multi-agent coordination API for SLH Spark.

Backs the /agent-hub.html "ICQ of AI agents" page. Every paste from Claude,
Copilot, Gemini, Grok, or Osif lands here — shared across devices, searchable,
priority-tagged. The website keeps localStorage as an offline fallback only.

Endpoints (prefix /api/agent-hub):
  POST   /message          — insert a new coordination message
  GET    /messages         — paginated feed with filters (source, priority, topic, search)
  GET    /stats            — aggregate counts by source + priority
  DELETE /message/{id}     — admin-only (X-Admin-Key header)
  POST   /bulk-import      — admin-only, useful for migrating localStorage dumps

All endpoints degrade gracefully if the DB pool is unavailable (503, never 500
on a missing pool). Admin authentication mirrors the existing pattern used by
creator_economy.py and arkham_bridge.py — comma-separated ADMIN_API_KEYS env
var, falls back to ADMIN_API_KEY single-value, then a hard-coded default that
prints a warning in production.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, HTTPException, Header, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-hub", tags=["agent-hub"])

# Global connection pool (set by main.py startup, same pattern as system_audit.py)
_pool = None


def set_pool(pool):
    """Inject the shared asyncpg pool from main.py startup."""
    global _pool
    _pool = pool


# ============================================================
# CONFIG
# ============================================================

MAX_CONTENT_BYTES = 10 * 1024  # 10 KB per message

ALLOWED_SOURCES = {"Claude", "Copilot", "Gemini", "Grok", "Osif", "Agent"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "info"}


def _admin_keys() -> set[str]:
    """Read admin keys from env. Mirrors the pattern in creator_economy.py."""
    raw = os.getenv("ADMIN_API_KEYS") or os.getenv("ADMIN_API_KEY") or ""
    return {k.strip() for k in raw.split(",") if k.strip()}


def _require_admin(x_admin_key: Optional[str]) -> None:
    keys = _admin_keys()
    if not x_admin_key or x_admin_key not in keys:
        raise HTTPException(status_code=403, detail="admin key required")


# ============================================================
# MODELS
# ============================================================

class AgentHubMessageIn(BaseModel):
    source: str
    priority: str
    topic: Optional[str] = None
    content: str
    agent_id: Optional[str] = None

    @validator("source")
    def _validate_source(cls, v: str) -> str:
        if v not in ALLOWED_SOURCES:
            raise ValueError(f"source must be one of {sorted(ALLOWED_SOURCES)}")
        return v

    @validator("priority")
    def _validate_priority(cls, v: str) -> str:
        if v not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(ALLOWED_PRIORITIES)}")
        return v

    @validator("content")
    def _validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("content is empty")
        if len(v.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError(f"content exceeds {MAX_CONTENT_BYTES} bytes")
        return v

    @validator("topic")
    def _validate_topic(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 200:
            raise ValueError("topic must be <= 200 chars")
        return v or None

    @validator("agent_id")
    def _validate_agent_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 120:
            raise ValueError("agent_id must be <= 120 chars")
        return v or None


class BulkImportIn(BaseModel):
    messages: List[AgentHubMessageIn] = Field(default_factory=list)


# ============================================================
# DATABASE INIT
# ============================================================

async def init_agent_hub_tables():
    """Create the agent_hub_messages table + indexes. Safe to call repeatedly."""
    if _pool is None:
        logger.warning("[agent-hub] init skipped — pool not set")
        return
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_hub_messages (
                    id BIGSERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    topic TEXT,
                    content TEXT NOT NULL,
                    agent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_hub_source ON agent_hub_messages(source)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_hub_priority ON agent_hub_messages(priority)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_hub_created ON agent_hub_messages(created_at DESC)"
            )
        logger.info("[agent-hub] tables ready")
    except Exception as e:  # noqa: BLE001
        logger.error(f"[agent-hub] init failed: {e!r}")


def _row_to_dict(row) -> dict:
    created = row["created_at"]
    return {
        "id": row["id"],
        "source": row["source"],
        "priority": row["priority"],
        "topic": row["topic"],
        "content": row["content"],
        "agent_id": row["agent_id"],
        "created_at": created.isoformat() if isinstance(created, datetime) else created,
    }


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/message")
async def post_message(msg: AgentHubMessageIn):
    """Insert a new coordination message. Returns {id, created_at}."""
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")
    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agent_hub_messages (source, priority, topic, content, agent_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, created_at
                """,
                msg.source, msg.priority, msg.topic, msg.content, msg.agent_id,
            )
            return {
                "id": row["id"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        # If the table doesn't exist yet, try to create it and retry once.
        logger.warning(f"[agent-hub] insert failed, trying init: {e!r}")
        try:
            await init_agent_hub_tables()
            async with _pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO agent_hub_messages (source, priority, topic, content, agent_id)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, created_at
                    """,
                    msg.source, msg.priority, msg.topic, msg.content, msg.agent_id,
                )
                return {
                    "id": row["id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                }
        except Exception as e2:  # noqa: BLE001
            logger.error(f"[agent-hub] insert failed after init: {e2!r}")
            raise HTTPException(status_code=500, detail=f"insert failed: {e2}")


@router.get("/messages")
async def list_messages(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    priority: Optional[str] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
):
    """Paginated feed, newest first, with optional filters."""
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")

    # Build WHERE clause dynamically
    where_parts: List[str] = []
    args: list = []
    idx = 1

    if source:
        # Allow lowercase legacy values from old localStorage dumps too
        where_parts.append(f"LOWER(source) = LOWER(${idx})")
        args.append(source)
        idx += 1
    if priority:
        where_parts.append(f"priority = ${idx}")
        args.append(priority)
        idx += 1
    if topic:
        where_parts.append(f"topic ILIKE ${idx}")
        args.append(f"%{topic}%")
        idx += 1
    if search:
        where_parts.append(f"content ILIKE ${idx}")
        args.append(f"%{search}%")
        idx += 1

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    sql = (
        f"SELECT id, source, priority, topic, content, agent_id, created_at "
        f"FROM agent_hub_messages {where_sql} "
        f"ORDER BY created_at DESC, id DESC "
        f"LIMIT ${idx} OFFSET ${idx + 1}"
    )
    args.extend([limit, offset])

    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
            # Count for pagination metadata (separate lightweight query)
            count_sql = f"SELECT COUNT(*) FROM agent_hub_messages {where_sql}"
            count_args = args[:-2]  # drop limit/offset
            total = await conn.fetchval(count_sql, *count_args) or 0
            return {
                "total": int(total),
                "limit": limit,
                "offset": offset,
                "messages": [_row_to_dict(r) for r in rows],
            }
    except Exception as e:  # noqa: BLE001
        # Table may not exist yet — return empty gracefully
        logger.warning(f"[agent-hub] list failed: {e!r}")
        return {"total": 0, "limit": limit, "offset": offset, "messages": []}


@router.get("/stats")
async def get_stats():
    """Aggregate counts. Returns {total, by_source, by_priority, last_message_at}."""
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")

    empty = {
        "total": 0,
        "by_source": {s: 0 for s in sorted(ALLOWED_SOURCES)},
        "by_priority": {p: 0 for p in sorted(ALLOWED_PRIORITIES)},
        "last_message_at": None,
    }

    try:
        async with _pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM agent_hub_messages") or 0

            by_source_rows = await conn.fetch(
                "SELECT source, COUNT(*) AS n FROM agent_hub_messages GROUP BY source"
            )
            by_source = {s: 0 for s in sorted(ALLOWED_SOURCES)}
            for r in by_source_rows:
                # Normalize case so old lowercase rows still aggregate by canonical name
                src = r["source"]
                if src in by_source:
                    by_source[src] = int(r["n"])
                else:
                    # Unknown / legacy label — expose as-is so Osif can see it
                    by_source[src] = int(r["n"])

            by_priority_rows = await conn.fetch(
                "SELECT priority, COUNT(*) AS n FROM agent_hub_messages GROUP BY priority"
            )
            by_priority = {p: 0 for p in sorted(ALLOWED_PRIORITIES)}
            for r in by_priority_rows:
                p = r["priority"]
                by_priority[p] = int(r["n"])

            last_at = await conn.fetchval(
                "SELECT MAX(created_at) FROM agent_hub_messages"
            )

            return {
                "total": int(total),
                "by_source": by_source,
                "by_priority": by_priority,
                "last_message_at": last_at.isoformat() if last_at else None,
            }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[agent-hub] stats failed: {e!r}")
        return empty


@router.delete("/message/{message_id}")
async def delete_message(
    message_id: int,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin-only: delete a single coordination message."""
    _require_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")
    try:
        async with _pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM agent_hub_messages WHERE id = $1", message_id
            )
            # asyncpg returns e.g. "DELETE 1" or "DELETE 0"
            deleted = result.endswith(" 1")
            if not deleted:
                raise HTTPException(status_code=404, detail="message not found")
            return {"status": "deleted", "id": message_id}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[agent-hub] delete failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-import")
async def bulk_import(
    payload: BulkImportIn,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin-only: migrate a localStorage dump into the server store.

    Returns ``{imported, skipped}``. Each message is inserted one by one so a
    single bad entry doesn't blow up the whole batch.
    """
    _require_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")

    if not payload.messages:
        return {"imported": 0, "skipped": 0}

    imported = 0
    skipped = 0
    try:
        async with _pool.acquire() as conn:
            for m in payload.messages:
                try:
                    await conn.execute(
                        """
                        INSERT INTO agent_hub_messages (source, priority, topic, content, agent_id)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        m.source, m.priority, m.topic, m.content, m.agent_id,
                    )
                    imported += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[agent-hub] bulk row skipped: {e!r}")
                    skipped += 1
        return {"imported": imported, "skipped": skipped}
    except Exception as e:  # noqa: BLE001
        logger.error(f"[agent-hub] bulk-import failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))
