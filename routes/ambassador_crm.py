"""
Ambassador CRM — Phase 0 (MVP).

Purpose: give SLH ambassadors (users who recruit investors to the platform)
a first-party CRM for their pipeline. Think Eliezer with 130 contacts —
he needs names, phones, notes, status, last-contact date, commitment amount.

Scope: contact management only. NO money flow through SLH for now (requires
legal entity + licensing before ambassador-mediated investments). When legal
clears → add deposits/commissions/payouts as a separate module.

Table: ambassador_contacts — created idempotently on first API call.

Auth: X-Admin-Key header (admin-only). Each ambassador is identified by
their Telegram ID as a query/body param; admin (Osif) can query any
ambassador's data. Future: per-ambassador JWT for self-service web dashboard.

Endpoints:
  POST   /api/ambassador/contacts             — create a single contact
  GET    /api/ambassador/contacts             — list with filters + pagination
  PATCH  /api/ambassador/contacts/{id}        — update fields
  POST   /api/ambassador/contacts/import      — bulk CSV import
  GET    /api/ambassador/stats/{amb_id}       — pipeline summary
"""
from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/ambassador", tags=["ambassador-crm"])

_pool = None


def set_pool(pool):
    global _pool
    _pool = pool


# ── auth (same ADMIN_API_KEYS env pattern used across the repo) ──
_ADMIN_KEYS = {
    k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()
}


def _require_admin_key(x_admin_key: Optional[str]) -> None:
    if not x_admin_key or x_admin_key not in _ADMIN_KEYS:
        raise HTTPException(403, "Admin key required (X-Admin-Key header)")


# ── DB init (idempotent) ──
async def _ensure_table(conn) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS ambassador_contacts (
            id             BIGSERIAL PRIMARY KEY,
            ambassador_id  BIGINT    NOT NULL,
            name           TEXT      NOT NULL,
            phone          TEXT,
            telegram_id    BIGINT,
            email          TEXT,
            status         TEXT      NOT NULL DEFAULT 'lead',
            notes          TEXT,
            last_contact   TIMESTAMP,
            amount_ils     NUMERIC(14,2) DEFAULT 0,
            tags           TEXT[]    DEFAULT ARRAY[]::TEXT[],
            deleted_at     TIMESTAMP,
            created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_amb_contacts_owner "
        "ON ambassador_contacts (ambassador_id) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_amb_contacts_status "
        "ON ambassador_contacts (ambassador_id, status) WHERE deleted_at IS NULL"
    )


VALID_STATUSES = {"lead", "qualified", "committed", "funded", "lost"}


def _serialize(row) -> dict:
    return {
        "id":            row["id"],
        "ambassador_id": row["ambassador_id"],
        "name":          row["name"],
        "phone":         row["phone"],
        "telegram_id":   row["telegram_id"],
        "email":         row["email"],
        "status":        row["status"],
        "notes":         row["notes"],
        "last_contact":  row["last_contact"].isoformat() if row["last_contact"] else None,
        "amount_ils":    float(row["amount_ils"]) if row["amount_ils"] is not None else 0.0,
        "tags":          list(row["tags"] or []),
        "created_at":    row["created_at"].isoformat(),
        "updated_at":    row["updated_at"].isoformat(),
    }


# ── models ──
class ContactCreate(BaseModel):
    ambassador_id: int
    name: str
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    status: Optional[str] = "lead"
    notes: Optional[str] = None
    amount_ils: Optional[float] = 0


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    last_contact: Optional[datetime] = None
    amount_ils: Optional[float] = None


# ── endpoints ──
@router.post("/contacts")
async def create_contact(
    req: ContactCreate,
    x_admin_key: Optional[str] = Header(None),
):
    """Create a single contact for an ambassador's pipeline."""
    _require_admin_key(x_admin_key)
    if req.status and req.status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        row = await conn.fetchrow("""
            INSERT INTO ambassador_contacts
                (ambassador_id, name, phone, telegram_id, email, status, notes, amount_ils)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """,
            req.ambassador_id, req.name, req.phone, req.telegram_id, req.email,
            req.status or "lead", req.notes, req.amount_ils or 0,
        )
    return {"ok": True, "contact": _serialize(row)}


@router.get("/contacts")
async def list_contacts(
    ambassador_id: int = Query(..., description="Ambassador's Telegram ID"),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Substring match on name/phone/notes"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_admin_key: Optional[str] = Header(None),
):
    """List an ambassador's contacts with optional filters + pagination."""
    _require_admin_key(x_admin_key)

    conds = ["ambassador_id = $1", "deleted_at IS NULL"]
    params: list = [ambassador_id]

    if status:
        params.append(status)
        conds.append(f"status = ${len(params)}")

    if search:
        params.append(f"%{search}%")
        like_placeholder = f"${len(params)}"
        conds.append(
            f"(name ILIKE {like_placeholder} OR phone ILIKE {like_placeholder} "
            f"OR notes ILIKE {like_placeholder})"
        )

    where_sql = " AND ".join(conds)
    filter_params = params.copy()
    params.extend([limit, offset])

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        rows = await conn.fetch(
            f"SELECT * FROM ambassador_contacts WHERE {where_sql} "
            f"ORDER BY created_at DESC "
            f"LIMIT ${len(params) - 1} OFFSET ${len(params)}",
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM ambassador_contacts WHERE {where_sql}",
            *filter_params,
        )

    return {
        "contacts": [_serialize(r) for r in rows],
        "total":    total,
        "limit":    limit,
        "offset":   offset,
    }


@router.patch("/contacts/{contact_id}")
async def update_contact(
    contact_id: int,
    req: ContactUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    """Update specific fields. Only non-null fields are touched."""
    _require_admin_key(x_admin_key)
    if req.status and req.status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "no fields to update")

    set_parts = [f"{col} = ${i+1}" for i, col in enumerate(updates.keys())]
    set_parts.append("updated_at = NOW()")
    set_sql = ", ".join(set_parts)
    params = list(updates.values()) + [contact_id]

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        row = await conn.fetchrow(
            f"UPDATE ambassador_contacts SET {set_sql} "
            f"WHERE id = ${len(params)} AND deleted_at IS NULL RETURNING *",
            *params,
        )
    if not row:
        raise HTTPException(404, "contact not found or already deleted")
    return {"ok": True, "contact": _serialize(row)}


@router.post("/contacts/import")
async def import_contacts_csv(
    ambassador_id: int = Form(..., description="Ambassador's Telegram ID"),
    file: UploadFile = File(..., description="CSV with columns: name (required), phone, telegram_id, email, status, notes, amount_ils"),
    x_admin_key: Optional[str] = Header(None),
):
    """Bulk-import contacts from a CSV. Only 'name' is required per row."""
    _require_admin_key(x_admin_key)

    body = await file.read()
    if not body:
        raise HTTPException(400, "empty file")
    text = body.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(400, "CSV has no header row")
    fieldnames_lower = {c.strip().lower() for c in reader.fieldnames}
    if "name" not in fieldnames_lower:
        raise HTTPException(400, "CSV must have a 'name' column")

    inserted = 0
    errors: list[dict] = []

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        async with conn.transaction():
            for idx, raw in enumerate(reader, start=2):  # row 1 = headers
                row = {
                    (k or "").strip().lower(): (v or "").strip()
                    for k, v in raw.items()
                }
                name = row.get("name", "").strip()
                if not name:
                    errors.append({"row": idx, "error": "missing name"})
                    continue

                status = row.get("status") or "lead"
                if status not in VALID_STATUSES:
                    status = "lead"

                try:
                    tg = int(row["telegram_id"]) if row.get("telegram_id") else None
                except (ValueError, TypeError):
                    tg = None
                try:
                    amt = float(row["amount_ils"]) if row.get("amount_ils") else 0
                except (ValueError, TypeError):
                    amt = 0

                await conn.execute("""
                    INSERT INTO ambassador_contacts
                        (ambassador_id, name, phone, telegram_id, email, status, notes, amount_ils)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    ambassador_id, name, row.get("phone") or None, tg,
                    row.get("email") or None, status, row.get("notes") or None, amt,
                )
                inserted += 1

    return {"ok": True, "inserted": inserted, "errors": errors}


@router.get("/stats/{ambassador_id}")
async def pipeline_stats(
    ambassador_id: int,
    x_admin_key: Optional[str] = Header(None),
):
    """Pipeline summary — count + total amount per status."""
    _require_admin_key(x_admin_key)

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        rows = await conn.fetch("""
            SELECT status,
                   COUNT(*)                     AS cnt,
                   COALESCE(SUM(amount_ils), 0) AS total
            FROM ambassador_contacts
            WHERE ambassador_id = $1 AND deleted_at IS NULL
            GROUP BY status
        """, ambassador_id)

    by_status = {
        r["status"]: {"count": r["cnt"], "total_ils": float(r["total"])}
        for r in rows
    }
    total_cnt = sum(v["count"] for v in by_status.values())
    total_amt = sum(v["total_ils"] for v in by_status.values())
    return {
        "ambassador_id":  ambassador_id,
        "by_status":      by_status,
        "total_contacts": total_cnt,
        "total_ils":      total_amt,
    }
