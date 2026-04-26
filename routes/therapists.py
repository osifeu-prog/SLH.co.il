"""
Therapists Network — Phase 2 (registration + admin approval).

Purpose: receive applications from /for-therapists.html, store them in a
dedicated `therapists` table (replacing the community_posts workaround),
and let admins approve/reject. Once approved, the user's `users.is_therapist`
flag flips to TRUE so /api/member-card surfaces it.

Phase 2 scope: register + list + approve + reject. Per-therapist self-service
endpoints (/me, /availability) and Telegram link land in Phase 3 + Phase 4.

Tables created idempotently on first call:
  - therapists                  — applications + approved profiles
  - users.is_therapist column   — additive, NOT NULL DEFAULT FALSE

Auth:
  - POST   /register                  — public, rate-limited (3/hour per email + IP)
  - GET    /applications              — admin (X-Admin-Key)
  - PATCH  /applications/{id}/approve — admin
  - PATCH  /applications/{id}/reject  — admin

Pattern: mirrors routes/ambassador_crm.py (set_pool, _ensure_table, header auth).
"""
from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/therapists", tags=["therapists"])

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


# ── rate limiting (in-memory, mirrors main.py:_check_community_rate) ──
_rate: dict[str, list[float]] = {}


def _rate_check(key: str, max_per_hour: int) -> bool:
    now = time.time()
    cutoff = now - 3600
    entries = [t for t in _rate.get(key, []) if t > cutoff]
    _rate[key] = entries
    if len(entries) >= max_per_hour:
        return False
    entries.append(now)
    return True


# ── DB init (idempotent) ──
async def _ensure_table(conn) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS therapists (
            id              BIGSERIAL PRIMARY KEY,
            user_id         BIGINT,
            telegram_id     BIGINT,
            name            TEXT      NOT NULL,
            email           TEXT      NOT NULL,
            phone           TEXT,
            profession      TEXT      NOT NULL,
            experience_yrs  INT       DEFAULT 0,
            handle          TEXT,
            specialties     TEXT,
            hours_per_week  TEXT,
            status          TEXT      NOT NULL DEFAULT 'pending',
            approved_at     TIMESTAMP,
            approved_by     BIGINT,
            rejected_reason TEXT,
            bio             TEXT,
            rate_zvk        NUMERIC(14,2) DEFAULT 0,
            availability    JSONB     DEFAULT '{}'::JSONB,
            source          TEXT      DEFAULT 'web_form',
            deleted_at      TIMESTAMP,
            created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_therapists_status "
        "ON therapists (status) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_therapists_user_id "
        "ON therapists (user_id) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_therapists_telegram "
        "ON therapists (telegram_id) WHERE deleted_at IS NULL"
    )
    await conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_therapists_email_active "
        "ON therapists (LOWER(email)) WHERE deleted_at IS NULL"
    )
    # additive column on users — main.py:7265 reads this via try/except
    await conn.execute(
        "ALTER TABLE users "
        "ADD COLUMN IF NOT EXISTS is_therapist BOOLEAN NOT NULL DEFAULT FALSE"
    )


VALID_STATUSES = {"pending", "approved", "rejected", "suspended"}


def _serialize(row) -> dict:
    return {
        "id":              row["id"],
        "user_id":         row["user_id"],
        "telegram_id":     row["telegram_id"],
        "name":            row["name"],
        "email":           row["email"],
        "phone":           row["phone"],
        "profession":      row["profession"],
        "experience_yrs":  row["experience_yrs"],
        "handle":          row["handle"],
        "specialties":     row["specialties"],
        "hours_per_week":  row["hours_per_week"],
        "status":          row["status"],
        "approved_at":     row["approved_at"].isoformat() if row["approved_at"] else None,
        "approved_by":     row["approved_by"],
        "rejected_reason": row["rejected_reason"],
        "bio":             row["bio"],
        "rate_zvk":        float(row["rate_zvk"]) if row["rate_zvk"] is not None else 0.0,
        "source":          row["source"],
        "created_at":      row["created_at"].isoformat(),
        "updated_at":      row["updated_at"].isoformat(),
    }


# ── models ──
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    profession: str = Field(..., min_length=1, max_length=200)
    experience_yrs: Optional[int] = Field(0, ge=0, le=80)
    handle: Optional[str] = Field(None, max_length=100)
    specialties: Optional[str] = Field(None, max_length=2000)
    hours_per_week: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field("web_form", max_length=50)


class ApproveRequest(BaseModel):
    user_id: Optional[int] = None  # if provided, also flips users.is_therapist=TRUE


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


# ── endpoints ──
@router.post("/register")
async def register_therapist(
    req: RegisterRequest,
    request: Request,
):
    """
    Public registration endpoint. Idempotent on email — second submission with
    same email and `status='pending'` returns the existing application_id
    instead of creating a duplicate.

    Rate limit: 3 per hour per (email + IP).
    """
    if _pool is None:
        raise HTTPException(503, "DB not ready")

    email_lc = req.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"therapist_register:{email_lc}:{client_ip}"
    if not _rate_check(rate_key, 3):
        raise HTTPException(429, "Too many registration attempts. Try again later.")

    async with _pool.acquire() as conn:
        await _ensure_table(conn)

        # Idempotency: if a pending application with this email already exists,
        # return its id rather than rejecting on the unique-active index.
        existing = await conn.fetchrow(
            "SELECT id, status FROM therapists "
            "WHERE LOWER(email) = $1 AND deleted_at IS NULL",
            email_lc,
        )
        if existing and existing["status"] == "pending":
            return {
                "ok": True,
                "application_id": existing["id"],
                "status": "pending",
                "idempotent": True,
            }
        if existing:
            # already approved/rejected — surface that, do NOT create a second row
            return {
                "ok": True,
                "application_id": existing["id"],
                "status": existing["status"],
                "idempotent": True,
            }

        row = await conn.fetchrow("""
            INSERT INTO therapists
                (name, email, phone, profession, experience_yrs, handle,
                 specialties, hours_per_week, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, status
        """,
            req.name.strip(), req.email.strip(), req.phone, req.profession,
            req.experience_yrs or 0, req.handle, req.specialties,
            req.hours_per_week, req.source or "web_form",
        )

    return {
        "ok": True,
        "application_id": row["id"],
        "status": row["status"],
    }


@router.get("/applications")
async def list_applications(
    status: Optional[str] = Query(None, description="pending/approved/rejected/suspended"),
    search: Optional[str] = Query(None, description="Substring on name/email/profession"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_admin_key: Optional[str] = Header(None),
):
    """List applications with filters + pagination. Admin only."""
    _require_admin_key(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "DB not ready")

    if status and status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")

    conds = ["deleted_at IS NULL"]
    params: list = []

    if status:
        params.append(status)
        conds.append(f"status = ${len(params)}")

    if search:
        params.append(f"%{search}%")
        ph = f"${len(params)}"
        conds.append(f"(name ILIKE {ph} OR email ILIKE {ph} OR profession ILIKE {ph})")

    where_sql = " AND ".join(conds)
    filter_params = params.copy()
    params.extend([limit, offset])

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        rows = await conn.fetch(
            f"SELECT * FROM therapists WHERE {where_sql} "
            f"ORDER BY created_at DESC "
            f"LIMIT ${len(params) - 1} OFFSET ${len(params)}",
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM therapists WHERE {where_sql}",
            *filter_params,
        )

    return {
        "applications": [_serialize(r) for r in rows],
        "total":        total,
        "limit":        limit,
        "offset":       offset,
    }


@router.patch("/applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    req: ApproveRequest,
    x_admin_key: Optional[str] = Header(None),
):
    """
    Approve an application. If `user_id` is provided, also link it and flip
    `users.is_therapist=TRUE` so /api/member-card surfaces the badge.
    """
    _require_admin_key(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "DB not ready")

    async with _pool.acquire() as conn:
        await _ensure_table(conn)

        row = await conn.fetchrow(
            "SELECT id, status, user_id FROM therapists "
            "WHERE id = $1 AND deleted_at IS NULL",
            application_id,
        )
        if not row:
            raise HTTPException(404, "application not found")
        if row["status"] == "approved":
            return {"ok": True, "application_id": application_id, "status": "approved",
                    "already_approved": True}

        async with conn.transaction():
            updated = await conn.fetchrow("""
                UPDATE therapists
                   SET status      = 'approved',
                       approved_at = NOW(),
                       approved_by = $1,
                       user_id     = COALESCE($2, user_id),
                       updated_at  = NOW()
                 WHERE id = $3 AND deleted_at IS NULL
                RETURNING *
            """, req.user_id, req.user_id, application_id)

            # Flip users.is_therapist if we have a user link.
            # Upsert tolerated: if the user row doesn't exist yet (e.g. they
            # haven't logged in to the website), do nothing — the flag will
            # appear on first login when the row is created.
            if updated and updated["user_id"]:
                await conn.execute(
                    "UPDATE users SET is_therapist = TRUE WHERE user_id = $1",
                    updated["user_id"],
                )

    return {"ok": True, "application_id": application_id, "status": "approved",
            "therapist": _serialize(updated)}


@router.patch("/applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    req: RejectRequest,
    x_admin_key: Optional[str] = Header(None),
):
    """Reject an application with a reason."""
    _require_admin_key(x_admin_key)
    if _pool is None:
        raise HTTPException(503, "DB not ready")

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        row = await conn.fetchrow("""
            UPDATE therapists
               SET status          = 'rejected',
                   rejected_reason = $1,
                   updated_at      = NOW()
             WHERE id = $2 AND deleted_at IS NULL
            RETURNING *
        """, req.reason, application_id)

    if not row:
        raise HTTPException(404, "application not found")
    return {"ok": True, "application_id": application_id, "status": "rejected",
            "therapist": _serialize(row)}
