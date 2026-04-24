"""Campaign admin â€” lead visibility + status tracking.

Osif was blind to who registered via /api/campaign/register â€” 10 real leads
sitting in DB with no way to see them. This router exposes:
  GET  /api/admin/campaign/list?campaign_id=&status=&limit=&offset=
  GET  /api/admin/campaign/stats                (all-campaign summary)
  POST /api/admin/campaign/note                 (add private note to a lead)
  POST /api/admin/campaign/status               (move lead: pending/contacted/closed/lost)

All endpoints are admin-gated via X-Admin-Key header.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/campaign", tags=["campaign-admin"])

_pool = None


def set_pool(pool):
    global _pool
    _pool = pool


def _check_admin(key: Optional[str]) -> None:
    allowed = (os.getenv("ADMIN_API_KEYS") or os.getenv("ADMIN_API_KEY") or "slh2026admin").split(",")
    if not key or key.strip() not in [k.strip() for k in allowed]:
        raise HTTPException(status_code=401, detail="admin key required")


@router.get("/list")
async def list_leads(
    x_admin_key: Optional[str] = Header(None),
    campaign_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "db pool not ready")

    where = []
    params: list = []
    if campaign_id:
        params.append(campaign_id)
        where.append(f"campaign_id = ${len(params)}")
    if status:
        params.append(status)
        where.append(f"status = ${len(params)}")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    params.extend([limit, offset])
    sql = f"""
        SELECT id, campaign_id, path_type, user_id, tg_username, full_name,
               phone, email, ref_code, affiliate_code, lang, status,
               amount_paid, notes, created_at, updated_at
        FROM campaign_registrations
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """
    async with _pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM campaign_registrations {where_sql}",
            *params[: len(params) - 2],
        )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "leads": [dict(r) for r in rows],
    }


@router.get("/stats")
async def stats(x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "db pool not ready")
    async with _pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM campaign_registrations")
        by_campaign = await conn.fetch(
            """SELECT campaign_id, COUNT(*) AS n, COUNT(*) FILTER (WHERE status='pending') AS pending,
                      COUNT(*) FILTER (WHERE status='contacted') AS contacted,
                      COUNT(*) FILTER (WHERE status='closed') AS closed,
                      COUNT(*) FILTER (WHERE status='lost') AS lost,
                      COALESCE(SUM(amount_paid),0) AS total_paid,
                      MAX(created_at) AS last_lead_at
               FROM campaign_registrations
               GROUP BY campaign_id
               ORDER BY n DESC"""
        )
        by_path = await conn.fetch(
            "SELECT path_type, COUNT(*) AS n FROM campaign_registrations GROUP BY path_type ORDER BY n DESC"
        )
        recent = await conn.fetch(
            """SELECT id, campaign_id, full_name, phone, status, created_at
               FROM campaign_registrations ORDER BY created_at DESC LIMIT 10"""
        )
    return {
        "total": total,
        "by_campaign": [dict(r) for r in by_campaign],
        "by_path": [dict(r) for r in by_path],
        "recent_10": [dict(r) for r in recent],
    }


class StatusUpdate(BaseModel):
    lead_id: int
    status: str  # pending | contacted | closed | lost
    amount_paid: Optional[float] = None


@router.post("/status")
async def update_status(req: StatusUpdate, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "db pool not ready")
    if req.status not in ("pending", "contacted", "closed", "lost"):
        raise HTTPException(400, "invalid status")
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE campaign_registrations
               SET status=$2, amount_paid=COALESCE($3, amount_paid), updated_at=NOW()
               WHERE id=$1
               RETURNING id, status, amount_paid, updated_at""",
            req.lead_id,
            req.status,
            req.amount_paid,
        )
        if not row:
            raise HTTPException(404, "lead not found")
    return dict(row)


class NoteUpdate(BaseModel):
    lead_id: int
    note: str


@router.post("/note")
async def append_note(req: NoteUpdate, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "db pool not ready")
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE campaign_registrations
               SET notes = COALESCE(notes,'') || E'\n' || $2, updated_at=NOW()
               WHERE id=$1
               RETURNING id, notes""",
            req.lead_id,
            req.note,
        )
        if not row:
            raise HTTPException(404, "lead not found")
    return dict(row)


@router.delete("/lead/{lead_id}")
async def delete_lead(lead_id: int, x_admin_key: Optional[str] = Header(None)):
    _check_admin(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "db pool not ready")
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "DELETE FROM campaign_registrations WHERE id=$1 RETURNING id",
            lead_id,
        )
        if not row:
            raise HTTPException(404, "lead not found")
    return {"deleted": row["id"]}
