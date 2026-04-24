"""
Mission Control — Tasks + Events.

Purpose: central task tracking for the SLH ecosystem. Every open item
(KNOWN_ISSUES, DROP_OFF handoffs, manual adds) lives in one table and
can be filtered / edited / assigned / commented from /admin/mission-control.html.

Replaces: scattered markdown files in ops/TEAM_HANDOFF_*, OPEN_TASKS_MASTER_*.
Those stay as human-readable exports; this API is the source of truth.

Table: tasks + task_events — created idempotently on first API call.

Auth: X-Admin-Key header (ADMIN_API_KEYS env var). Same pattern as
ambassador_crm.py and the rest of the admin routes.

Endpoints:
  GET    /api/admin/tasks                 — list with filters + pagination
  POST   /api/admin/tasks                 — create single task
  PATCH  /api/admin/tasks/{id}            — update fields + log event
  DELETE /api/admin/tasks/{id}            — soft delete
  GET    /api/admin/tasks/{id}/events     — audit log for one task
  POST   /api/admin/tasks/{id}/events     — add comment / custom event
  POST   /api/admin/tasks/bulk-import     — seed/migration endpoint
  GET    /api/admin/overview              — aggregated dashboard stats
"""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin", tags=["mission-control"])

_pool = None


def set_pool(pool):
    global _pool
    _pool = pool


_ADMIN_KEYS = {
    k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()
}


def _require_admin_key(x_admin_key: Optional[str]) -> None:
    if not x_admin_key or x_admin_key not in _ADMIN_KEYS:
        raise HTTPException(403, "Admin key required (X-Admin-Key header)")


VALID_STATUSES = {"open", "in_progress", "blocked", "done", "cancelled"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
VALID_CATEGORIES = {
    "infra", "crm", "community", "qa",
    "owner", "code", "strategic", "security",
}


async def _ensure_tables(conn) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id                   BIGSERIAL PRIMARY KEY,
            title                TEXT NOT NULL,
            description          TEXT,
            category             TEXT NOT NULL DEFAULT 'code',
            priority             TEXT NOT NULL DEFAULT 'P1',
            status               TEXT NOT NULL DEFAULT 'open',
            assignee_name        TEXT,
            assignee_telegram_id BIGINT,
            source               TEXT,
            blocker              TEXT,
            due_date             DATE,
            estimated_minutes    INTEGER,
            completed_at         TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at           TIMESTAMPTZ
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS task_events (
            id                   BIGSERIAL PRIMARY KEY,
            task_id              BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            event_type           TEXT NOT NULL,
            actor_name           TEXT,
            actor_telegram_id    BIGINT,
            payload              JSONB,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_tasks_status "
        "ON tasks(status) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_tasks_assignee "
        "ON tasks(assignee_name) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_tasks_category "
        "ON tasks(category) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_tasks_priority_status "
        "ON tasks(priority, status) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_task_events_task "
        "ON task_events(task_id, created_at DESC)"
    )


def _serialize_task(row) -> dict:
    return {
        "id":                   row["id"],
        "title":                row["title"],
        "description":          row["description"],
        "category":             row["category"],
        "priority":             row["priority"],
        "status":               row["status"],
        "assignee_name":        row["assignee_name"],
        "assignee_telegram_id": row["assignee_telegram_id"],
        "source":               row["source"],
        "blocker":              row["blocker"],
        "due_date":             row["due_date"].isoformat() if row["due_date"] else None,
        "estimated_minutes":    row["estimated_minutes"],
        "completed_at":         row["completed_at"].isoformat() if row["completed_at"] else None,
        "created_at":           row["created_at"].isoformat(),
        "updated_at":           row["updated_at"].isoformat(),
    }


def _serialize_event(row) -> dict:
    import json
    payload = row["payload"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            pass
    return {
        "id":                row["id"],
        "task_id":           row["task_id"],
        "event_type":        row["event_type"],
        "actor_name":        row["actor_name"],
        "actor_telegram_id": row["actor_telegram_id"],
        "payload":           payload,
        "created_at":        row["created_at"].isoformat(),
    }


async def _log_event(conn, task_id: int, event_type: str,
                     actor_name: Optional[str], actor_tg: Optional[int],
                     payload: Optional[dict] = None) -> None:
    import json
    await conn.execute(
        "INSERT INTO task_events (task_id, event_type, actor_name, actor_telegram_id, payload) "
        "VALUES ($1, $2, $3, $4, $5::jsonb)",
        task_id, event_type, actor_name, actor_tg,
        json.dumps(payload) if payload else None,
    )


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "code"
    priority: str = "P1"
    status: str = "open"
    assignee_name: Optional[str] = None
    assignee_telegram_id: Optional[int] = None
    source: Optional[str] = None
    blocker: Optional[str] = None
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    actor_name: Optional[str] = Field(None, description="Who is creating this task")
    actor_telegram_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_telegram_id: Optional[int] = None
    source: Optional[str] = None
    blocker: Optional[str] = None
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    actor_name: Optional[str] = None
    actor_telegram_id: Optional[int] = None


class TaskEventCreate(BaseModel):
    event_type: str = "commented"
    actor_name: Optional[str] = None
    actor_telegram_id: Optional[int] = None
    payload: Optional[dict] = None


class BulkImport(BaseModel):
    tasks: list[TaskCreate]
    skip_duplicates_by_source: bool = True


def _validate_enums(category: Optional[str], priority: Optional[str], status: Optional[str]) -> None:
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(400, f"category must be one of {sorted(VALID_CATEGORIES)}")
    if priority is not None and priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"priority must be one of {sorted(VALID_PRIORITIES)}")
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")


@router.post("/tasks")
async def create_task(req: TaskCreate, x_admin_key: Optional[str] = Header(None)):
    _require_admin_key(x_admin_key)
    _validate_enums(req.category, req.priority, req.status)

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        row = await conn.fetchrow("""
            INSERT INTO tasks
                (title, description, category, priority, status,
                 assignee_name, assignee_telegram_id, source, blocker,
                 due_date, estimated_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """,
            req.title, req.description, req.category, req.priority, req.status,
            req.assignee_name, req.assignee_telegram_id, req.source, req.blocker,
            req.due_date, req.estimated_minutes,
        )
        await _log_event(conn, row["id"], "created", req.actor_name, req.actor_telegram_id,
                         {"title": req.title, "priority": req.priority, "category": req.category})
    return {"ok": True, "task": _serialize_task(row)}


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    assignee: Optional[str] = Query(None, description="Substring match on assignee_name"),
    search: Optional[str] = Query(None, description="Substring match on title/description"),
    include_done: bool = Query(False, description="Include status=done (default excluded)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)
    _validate_enums(category, priority, status)

    conds = ["deleted_at IS NULL"]
    params: list = []

    if status:
        params.append(status)
        conds.append(f"status = ${len(params)}")
    elif not include_done:
        conds.append("status <> 'done'")

    if priority:
        params.append(priority)
        conds.append(f"priority = ${len(params)}")

    if category:
        params.append(category)
        conds.append(f"category = ${len(params)}")

    if assignee:
        params.append(f"%{assignee}%")
        conds.append(f"assignee_name ILIKE ${len(params)}")

    if search:
        params.append(f"%{search}%")
        placeholder = f"${len(params)}"
        conds.append(f"(title ILIKE {placeholder} OR description ILIKE {placeholder})")

    where = " AND ".join(conds)
    filter_params = params.copy()
    params.extend([limit, offset])

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            f"SELECT * FROM tasks WHERE {where} "
            f"ORDER BY "
            f"  CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, "
            f"  CASE status WHEN 'in_progress' THEN 0 WHEN 'blocked' THEN 1 "
            f"              WHEN 'open' THEN 2 WHEN 'done' THEN 3 ELSE 4 END, "
            f"  created_at DESC "
            f"LIMIT ${len(params) - 1} OFFSET ${len(params)}",
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM tasks WHERE {where}",
            *filter_params,
        )

    return {
        "tasks":  [_serialize_task(r) for r in rows],
        "total":  total,
        "limit":  limit,
        "offset": offset,
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    req: TaskUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)
    _validate_enums(req.category, req.priority, req.status)

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        existing = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1 AND deleted_at IS NULL", task_id
        )
        if not existing:
            raise HTTPException(404, "task not found or already deleted")

        updates: dict[str, Any] = {}
        for field in ("title", "description", "category", "priority", "status",
                      "assignee_name", "assignee_telegram_id", "source", "blocker",
                      "due_date", "estimated_minutes"):
            value = getattr(req, field)
            if value is not None:
                updates[field] = value

        if req.status == "done" and existing["status"] != "done":
            updates["completed_at"] = datetime.utcnow()
        elif req.status is not None and req.status != "done" and existing["completed_at"]:
            updates["completed_at"] = None

        if not updates:
            raise HTTPException(400, "no fields to update")

        set_parts = [f"{col} = ${i + 1}" for i, col in enumerate(updates.keys())]
        set_parts.append("updated_at = NOW()")
        set_sql = ", ".join(set_parts)
        params = list(updates.values()) + [task_id]

        row = await conn.fetchrow(
            f"UPDATE tasks SET {set_sql} WHERE id = ${len(params)} RETURNING *",
            *params,
        )

        event_payload = {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                         for k, v in updates.items() if k != "completed_at"}
        if req.status and req.status != existing["status"]:
            await _log_event(conn, task_id, "status_changed",
                             req.actor_name, req.actor_telegram_id,
                             {"from": existing["status"], "to": req.status})
        if req.assignee_name and req.assignee_name != existing["assignee_name"]:
            await _log_event(conn, task_id, "assigned",
                             req.actor_name, req.actor_telegram_id,
                             {"from": existing["assignee_name"], "to": req.assignee_name})
        if event_payload and not req.status and not req.assignee_name:
            await _log_event(conn, task_id, "updated",
                             req.actor_name, req.actor_telegram_id, event_payload)

    return {"ok": True, "task": _serialize_task(row)}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    actor_name: Optional[str] = Query(None),
    actor_telegram_id: Optional[int] = Query(None),
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        result = await conn.execute(
            "UPDATE tasks SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL",
            task_id,
        )
        if result == "UPDATE 0":
            raise HTTPException(404, "task not found or already deleted")
        await _log_event(conn, task_id, "deleted", actor_name, actor_telegram_id, None)
    return {"ok": True, "id": task_id, "deleted": True}


@router.get("/tasks/{task_id}/events")
async def task_events(
    task_id: int,
    limit: int = Query(100, ge=1, le=500),
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            "SELECT * FROM task_events WHERE task_id = $1 "
            "ORDER BY created_at DESC LIMIT $2",
            task_id, limit,
        )
    return {"events": [_serialize_event(r) for r in rows], "task_id": task_id}


@router.post("/tasks/{task_id}/events")
async def add_task_event(
    task_id: int,
    req: TaskEventCreate,
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        existing = await conn.fetchval(
            "SELECT id FROM tasks WHERE id = $1 AND deleted_at IS NULL", task_id
        )
        if not existing:
            raise HTTPException(404, "task not found")
        await _log_event(conn, task_id, req.event_type, req.actor_name,
                         req.actor_telegram_id, req.payload)
    return {"ok": True, "task_id": task_id, "event_type": req.event_type}


@router.post("/tasks/bulk-import")
async def bulk_import(
    req: BulkImport,
    x_admin_key: Optional[str] = Header(None),
):
    _require_admin_key(x_admin_key)

    inserted = 0
    skipped = 0
    errors: list[dict] = []

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        async with conn.transaction():
            for idx, t in enumerate(req.tasks):
                try:
                    _validate_enums(t.category, t.priority, t.status)
                except HTTPException as e:
                    errors.append({"index": idx, "title": t.title, "error": e.detail})
                    continue

                if req.skip_duplicates_by_source and t.source:
                    dup = await conn.fetchval(
                        "SELECT id FROM tasks WHERE source = $1 AND deleted_at IS NULL",
                        t.source,
                    )
                    if dup:
                        skipped += 1
                        continue

                row = await conn.fetchrow("""
                    INSERT INTO tasks
                        (title, description, category, priority, status,
                         assignee_name, assignee_telegram_id, source, blocker,
                         due_date, estimated_minutes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                """,
                    t.title, t.description, t.category, t.priority, t.status,
                    t.assignee_name, t.assignee_telegram_id, t.source, t.blocker,
                    t.due_date, t.estimated_minutes,
                )
                await _log_event(conn, row["id"], "created",
                                 t.actor_name or "bulk_import",
                                 t.actor_telegram_id, {"source": t.source})
                inserted += 1

    return {"ok": True, "inserted": inserted, "skipped": skipped, "errors": errors}


@router.get("/overview")
async def overview(x_admin_key: Optional[str] = Header(None)):
    """Aggregated stats for mission-control dashboard."""
    _require_admin_key(x_admin_key)

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)

        by_status = await conn.fetch("""
            SELECT status, COUNT(*) AS cnt
            FROM tasks WHERE deleted_at IS NULL
            GROUP BY status
        """)
        by_priority = await conn.fetch("""
            SELECT priority, COUNT(*) AS cnt
            FROM tasks WHERE deleted_at IS NULL AND status <> 'done'
            GROUP BY priority
        """)
        by_category = await conn.fetch("""
            SELECT category, COUNT(*) AS cnt
            FROM tasks WHERE deleted_at IS NULL AND status <> 'done'
            GROUP BY category
            ORDER BY cnt DESC
        """)
        by_assignee = await conn.fetch("""
            SELECT COALESCE(assignee_name, '(unassigned)') AS name,
                   COUNT(*) FILTER (WHERE status IN ('open','in_progress','blocked')) AS open_cnt,
                   COUNT(*) FILTER (WHERE status = 'done') AS done_cnt
            FROM tasks WHERE deleted_at IS NULL
            GROUP BY assignee_name
            ORDER BY open_cnt DESC
        """)
        done_today = await conn.fetchval("""
            SELECT COUNT(*) FROM tasks
            WHERE deleted_at IS NULL AND status = 'done'
              AND completed_at >= CURRENT_DATE
        """)
        blocked_reasons = await conn.fetch("""
            SELECT id, title, blocker, assignee_name, priority
            FROM tasks WHERE deleted_at IS NULL AND status = 'blocked'
            ORDER BY
              CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END
            LIMIT 20
        """)
        recent_events = await conn.fetch("""
            SELECT te.*, t.title AS task_title, t.priority AS task_priority
            FROM task_events te
            JOIN tasks t ON t.id = te.task_id
            WHERE t.deleted_at IS NULL
            ORDER BY te.created_at DESC
            LIMIT 20
        """)

    return {
        "counts": {
            "by_status":   {r["status"]: r["cnt"] for r in by_status},
            "by_priority": {r["priority"]: r["cnt"] for r in by_priority},
            "by_category": [{"category": r["category"], "count": r["cnt"]} for r in by_category],
            "by_assignee": [
                {"name": r["name"], "open": r["open_cnt"], "done": r["done_cnt"]}
                for r in by_assignee
            ],
            "done_today": done_today or 0,
        },
        "blocked": [
            {"id": r["id"], "title": r["title"], "blocker": r["blocker"],
             "assignee": r["assignee_name"], "priority": r["priority"]}
            for r in blocked_reasons
        ],
        "recent_events": [
            {**_serialize_event(r),
             "task_title": r["task_title"], "task_priority": r["task_priority"]}
            for r in recent_events
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
