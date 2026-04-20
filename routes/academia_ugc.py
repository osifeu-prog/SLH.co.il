"""
Academia UGC — User-Generated Content infrastructure for SLH Academia.

Backs the instructor marketplace: users can register as instructors, upload
courses (admin-approved), get paid 70% of every license sold (platform takes
30%), and students can review the courses they purchased.

Schema additions:
  academy_instructors  — instructor profiles + lifetime stats
  academy_earnings     — per-license 70/30 split ledger
  academy_reviews      — student reviews (1-5 stars), one per (course, user)
  + ALTER academy_courses to add instructor_id, approval_status, language, preview_url

Endpoints (prefix /api/academia):
  POST   /instructor/register
  POST   /instructor/approve            — admin (X-Admin-Key)
  GET    /instructor/{user_id}
  POST   /course/create
  POST   /course/approve                — admin (X-Admin-Key)
  GET    /courses                       — public catalog with filters
  GET    /course/{slug}                 — single course + review aggregate
  POST   /review
  GET    /earnings/{instructor_user_id}
  POST   /earnings/trigger-split        — internal/admin (X-Admin-Key)

All queries parameterized. Admin pattern mirrors agent_hub.py (X-Admin-Key
checked against ADMIN_API_KEYS / ADMIN_API_KEY env vars, dev fallback
slh2026admin). DB pool is optional — endpoints return 503 if missing
instead of 500.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, HTTPException, Header, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/academia", tags=["academia-ugc"])

# Global connection pool (set by main.py startup, same pattern as agent_hub)
_pool = None


def set_pool(pool):
    """Inject the shared asyncpg pool from main.py startup."""
    global _pool
    _pool = pool


# ============================================================
# CONFIG
# ============================================================

# Revenue split — instructor keeps 70%, platform takes 30%
PLATFORM_CUT_PCT = 30
INSTRUCTOR_CUT_PCT = 70

ALLOWED_LANGUAGES = {"he", "en", "ar", "ru"}
APPROVAL_STATUSES = {"pending", "approved", "rejected"}


def _admin_keys() -> set[str]:
    """Read admin keys from env. Mirrors the pattern in agent_hub.py."""
    raw = os.getenv("ADMIN_API_KEYS") or os.getenv("ADMIN_API_KEY") or ""
    return {k.strip() for k in raw.split(",") if k.strip()}


def _require_admin(x_admin_key: Optional[str]) -> None:
    keys = _admin_keys()
    if not x_admin_key or x_admin_key not in keys:
        raise HTTPException(status_code=403, detail="admin key required")


# ============================================================
# MODELS
# ============================================================

class InstructorRegisterIn(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    bio_he: Optional[str] = None
    payout_wallet: Optional[str] = None  # TON or BSC address

    @validator("display_name")
    def _validate_name(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 200:
            raise ValueError("display_name too long")
        return v or None

    @validator("bio_he")
    def _validate_bio(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 4000:
            raise ValueError("bio_he too long")
        return v or None

    @validator("payout_wallet")
    def _validate_wallet(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 200:
            raise ValueError("payout_wallet too long")
        return v or None


class InstructorApproveIn(BaseModel):
    instructor_id: int
    approved: bool


class CourseCreateIn(BaseModel):
    instructor_user_id: int
    slug: str
    title_he: str
    description_he: Optional[str] = None
    price_ils: Optional[float] = 0.0
    price_slh: Optional[float] = 0.0
    materials_url: Optional[str] = None
    preview_url: Optional[str] = None
    language: str = "he"

    @validator("slug")
    def _validate_slug(cls, v):
        v = (v or "").strip().lower()
        if not v or len(v) > 120:
            raise ValueError("slug must be 1-120 chars")
        # Permissive — allow alphanum + hyphen + underscore
        for ch in v:
            if not (ch.isalnum() or ch in "-_"):
                raise ValueError("slug must be alphanumeric, '-' or '_' only")
        return v

    @validator("title_he")
    def _validate_title(cls, v):
        v = (v or "").strip()
        if not v or len(v) > 300:
            raise ValueError("title_he must be 1-300 chars")
        return v

    @validator("language")
    def _validate_language(cls, v):
        v = (v or "he").strip().lower()
        if v not in ALLOWED_LANGUAGES:
            raise ValueError(f"language must be one of {sorted(ALLOWED_LANGUAGES)}")
        return v


class CourseApproveIn(BaseModel):
    course_id: int
    approved: bool
    reason: Optional[str] = None


class ReviewIn(BaseModel):
    course_id: int
    user_id: int
    rating: int = Field(..., ge=1, le=5)
    comment_he: Optional[str] = None

    @validator("comment_he")
    def _validate_comment(cls, v):
        if v is None:
            return None
        v = v.strip()
        if len(v) > 2000:
            raise ValueError("comment_he too long")
        return v or None


class EarningsTriggerIn(BaseModel):
    license_id: int
    # Optional override — useful when the license itself doesn't carry the price
    gross_ils: Optional[float] = None


class EarningsPayoutIn(BaseModel):
    earnings_id: int
    payout_tx: str  # bank reference, crypto TX hash, or internal wallet_send id
    note: Optional[str] = None


# ============================================================
# DATABASE INIT
# ============================================================

async def init_academia_ugc_tables():
    """Create UGC tables + extend academy_courses. Safe to call repeatedly."""
    if _pool is None:
        logger.warning("[academia-ugc] init skipped — pool not set")
        return
    try:
        async with _pool.acquire() as conn:
            # Instructors
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS academy_instructors (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    display_name TEXT,
                    bio_he TEXT,
                    payout_wallet TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    total_courses INT DEFAULT 0,
                    total_students INT DEFAULT 0,
                    total_earned_ils NUMERIC(12,2) DEFAULT 0,
                    total_earned_slh NUMERIC(18,4) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_instr_user ON academy_instructors(user_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_instr_approved ON academy_instructors(approved)"
            )

            # Extend academy_courses with instructor + approval columns
            await conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='academy_courses' AND column_name='instructor_id') THEN
                        ALTER TABLE academy_courses ADD COLUMN instructor_id BIGINT REFERENCES academy_instructors(id);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='academy_courses' AND column_name='approval_status') THEN
                        ALTER TABLE academy_courses ADD COLUMN approval_status TEXT DEFAULT 'pending';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='academy_courses' AND column_name='language') THEN
                        ALTER TABLE academy_courses ADD COLUMN language TEXT DEFAULT 'he';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='academy_courses' AND column_name='preview_url') THEN
                        ALTER TABLE academy_courses ADD COLUMN preview_url TEXT;
                    END IF;
                END
                $$;
            """)

            # Earnings ledger
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS academy_earnings (
                    id BIGSERIAL PRIMARY KEY,
                    instructor_id BIGINT REFERENCES academy_instructors(id),
                    course_id BIGINT REFERENCES academy_courses(id),
                    license_id BIGINT REFERENCES academy_licenses(id),
                    gross_ils NUMERIC(12,2),
                    platform_cut_ils NUMERIC(12,2),
                    instructor_cut_ils NUMERIC(12,2),
                    paid_out BOOLEAN DEFAULT FALSE,
                    payout_tx TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_earn_instr ON academy_earnings(instructor_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_earn_paid ON academy_earnings(paid_out)"
            )
            # Idempotency guard for trigger-split
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_earn_license ON academy_earnings(license_id)"
            )

            # Reviews
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS academy_reviews (
                    id BIGSERIAL PRIMARY KEY,
                    course_id BIGINT REFERENCES academy_courses(id),
                    user_id BIGINT NOT NULL,
                    rating INT CHECK (rating >= 1 AND rating <= 5),
                    comment_he TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(course_id, user_id)
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_review_course ON academy_reviews(course_id)"
            )
        logger.info("[academia-ugc] tables ready")
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] init failed: {e!r}")


# ============================================================
# HELPERS
# ============================================================

def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


async def _require_pool() -> None:
    if _pool is None:
        raise HTTPException(status_code=503, detail="database pool not ready")


async def _get_instructor_by_user(conn, user_id: int):
    return await conn.fetchrow(
        "SELECT id, user_id, display_name, bio_he, payout_wallet, approved, "
        "total_courses, total_students, total_earned_ils, total_earned_slh, created_at "
        "FROM academy_instructors WHERE user_id = $1",
        user_id,
    )


# ============================================================
# ENDPOINTS — INSTRUCTORS
# ============================================================

@router.post("/instructor/register")
async def instructor_register(payload: InstructorRegisterIn):
    """Register a pending instructor (must be approved by admin before uploading)."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            # Idempotent — if user already registered, return existing
            existing = await _get_instructor_by_user(conn, payload.user_id)
            if existing:
                return {
                    "id": existing["id"],
                    "approved": bool(existing["approved"]),
                    "message": "כבר רשום כמדריך — ממתין לאישור" if not existing["approved"]
                               else "כבר רשום ומאושר",
                }
            row = await conn.fetchrow(
                """
                INSERT INTO academy_instructors
                    (user_id, display_name, bio_he, payout_wallet, approved)
                VALUES ($1, $2, $3, $4, FALSE)
                RETURNING id, approved
                """,
                payload.user_id,
                payload.display_name,
                payload.bio_he,
                payload.payout_wallet,
            )
            return {
                "id": row["id"],
                "approved": bool(row["approved"]),
                "message": "נרשמת כמדריך — ממתין לאישור מנהל",
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] instructor_register failed: {e!r}")
        # Try to init tables and retry once
        try:
            await init_academia_ugc_tables()
            async with _pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO academy_instructors
                        (user_id, display_name, bio_he, payout_wallet, approved)
                    VALUES ($1, $2, $3, $4, FALSE)
                    ON CONFLICT (user_id) DO NOTHING
                    RETURNING id, approved
                    """,
                    payload.user_id,
                    payload.display_name,
                    payload.bio_he,
                    payload.payout_wallet,
                )
                if row:
                    return {
                        "id": row["id"],
                        "approved": False,
                        "message": "נרשמת כמדריך — ממתין לאישור מנהל",
                    }
                # ON CONFLICT path
                existing = await _get_instructor_by_user(conn, payload.user_id)
                return {
                    "id": existing["id"] if existing else None,
                    "approved": bool(existing["approved"]) if existing else False,
                    "message": "כבר רשום כמדריך",
                }
        except Exception as e2:  # noqa: BLE001
            logger.error(f"[academia-ugc] register retry failed: {e2!r}")
            raise HTTPException(status_code=500, detail=f"register failed: {e2}")


@router.post("/instructor/approve")
async def instructor_approve(
    payload: InstructorApproveIn,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin-only: flip an instructor's approved flag."""
    _require_admin(x_admin_key)
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE academy_instructors SET approved = $1 WHERE id = $2",
                payload.approved,
                payload.instructor_id,
            )
            if not result.endswith(" 1"):
                raise HTTPException(status_code=404, detail="instructor not found")
            return {
                "status": "ok",
                "instructor_id": payload.instructor_id,
                "approved": payload.approved,
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] instructor_approve failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instructor/{user_id}")
async def get_instructor(user_id: int):
    """Return instructor profile + live stats (recomputed from earnings + courses)."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            row = await _get_instructor_by_user(conn, user_id)
            if not row:
                raise HTTPException(status_code=404, detail="instructor not found")

            # Live stats — courses + students + earnings
            stats = await conn.fetchrow(
                """
                SELECT
                    (SELECT COUNT(*) FROM academy_courses WHERE instructor_id = $1) AS total_courses,
                    (SELECT COUNT(DISTINCT l.user_id)
                       FROM academy_licenses l
                       JOIN academy_courses c ON c.id = l.course_id
                      WHERE c.instructor_id = $1) AS total_students,
                    (SELECT COALESCE(SUM(instructor_cut_ils), 0)
                       FROM academy_earnings WHERE instructor_id = $1) AS earned_ils,
                    (SELECT COALESCE(SUM(instructor_cut_ils), 0)
                       FROM academy_earnings
                      WHERE instructor_id = $1 AND paid_out = FALSE) AS unpaid_ils
                """,
                row["id"],
            )

            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "display_name": row["display_name"],
                "bio_he": row["bio_he"],
                "payout_wallet": row["payout_wallet"],
                "approved": bool(row["approved"]),
                "created_at": _iso(row["created_at"]),
                "stats": {
                    "total_courses": int(stats["total_courses"] or 0),
                    "total_students": int(stats["total_students"] or 0),
                    "total_earned_ils": _to_float(stats["earned_ils"]),
                    "total_earned_slh": _to_float(row["total_earned_slh"]),
                    "unpaid_ils": _to_float(stats["unpaid_ils"]),
                },
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] get_instructor failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENDPOINTS — COURSES
# ============================================================

@router.post("/course/create")
async def course_create(payload: CourseCreateIn):
    """Instructor uploads a new course. Must be an approved instructor."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            instr = await _get_instructor_by_user(conn, payload.instructor_user_id)
            if not instr:
                raise HTTPException(
                    status_code=403,
                    detail="not registered as instructor",
                )
            if not instr["approved"]:
                raise HTTPException(
                    status_code=403,
                    detail="instructor not yet approved by admin",
                )

            # Slug uniqueness check
            existing = await conn.fetchval(
                "SELECT id FROM academy_courses WHERE slug = $1", payload.slug
            )
            if existing:
                raise HTTPException(status_code=409, detail="slug already exists")

            row = await conn.fetchrow(
                """
                INSERT INTO academy_courses
                    (slug, title_he, description_he, price_ils, price_slh,
                     materials_url, preview_url, language, instructor_id,
                     approval_status, active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pending', FALSE)
                RETURNING id, slug, approval_status
                """,
                payload.slug,
                payload.title_he,
                payload.description_he,
                payload.price_ils or 0,
                payload.price_slh or 0,
                payload.materials_url,
                payload.preview_url,
                payload.language,
                instr["id"],
            )
            return {
                "id": row["id"],
                "slug": row["slug"],
                "approval_status": row["approval_status"],
                "message": "הקורס נוצר וממתין לאישור מנהל",
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] course_create failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/course/approve")
async def course_approve(
    payload: CourseApproveIn,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin-only: approve or reject a course. Approved courses become active."""
    _require_admin(x_admin_key)
    await _require_pool()
    try:
        new_status = "approved" if payload.approved else "rejected"
        async with _pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE academy_courses SET approval_status = $1, active = $2 WHERE id = $3",
                new_status,
                payload.approved,
                payload.course_id,
            )
            if not result.endswith(" 1"):
                raise HTTPException(status_code=404, detail="course not found")

            # Bump instructor's total_courses cache when approving
            if payload.approved:
                await conn.execute(
                    """
                    UPDATE academy_instructors
                       SET total_courses = (
                           SELECT COUNT(*) FROM academy_courses
                            WHERE instructor_id = academy_instructors.id
                              AND approval_status = 'approved'
                       )
                     WHERE id = (SELECT instructor_id FROM academy_courses WHERE id = $1)
                    """,
                    payload.course_id,
                )

            return {
                "status": "ok",
                "course_id": payload.course_id,
                "approval_status": new_status,
                "reason": payload.reason,
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] course_approve failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses")
async def list_courses(
    approved: bool = True,
    language: Optional[str] = None,
    instructor_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Public catalog. Defaults to approved-only."""
    await _require_pool()

    where_parts: List[str] = []
    args: list = []
    idx = 1

    if approved:
        where_parts.append(f"c.approval_status = ${idx}")
        args.append("approved")
        idx += 1
        where_parts.append("c.active = TRUE")
    if language:
        where_parts.append(f"c.language = ${idx}")
        args.append(language)
        idx += 1
    if instructor_id is not None:
        where_parts.append(f"c.instructor_id = ${idx}")
        args.append(instructor_id)
        idx += 1

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    sql = (
        "SELECT c.id, c.slug, c.title_he, c.description_he, c.price_ils, c.price_slh, "
        "c.materials_url, c.preview_url, c.language, c.approval_status, c.active, "
        "c.instructor_id, c.created_at, "
        "i.display_name AS instructor_name "
        "FROM academy_courses c "
        "LEFT JOIN academy_instructors i ON i.id = c.instructor_id "
        f"{where_sql} "
        f"ORDER BY c.id DESC LIMIT ${idx} OFFSET ${idx + 1}"
    )
    args.extend([limit, offset])

    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
            count_sql = (
                f"SELECT COUNT(*) FROM academy_courses c {where_sql}"
            )
            total = await conn.fetchval(count_sql, *args[:-2]) or 0
            return {
                "total": int(total),
                "limit": limit,
                "offset": offset,
                "courses": [
                    {
                        "id": r["id"],
                        "slug": r["slug"],
                        "title_he": r["title_he"],
                        "description_he": r["description_he"],
                        "price_ils": _to_float(r["price_ils"]),
                        "price_slh": _to_float(r["price_slh"]),
                        "materials_url": r["materials_url"],
                        "preview_url": r["preview_url"],
                        "language": r["language"],
                        "approval_status": r["approval_status"],
                        "active": bool(r["active"]),
                        "instructor_id": r["instructor_id"],
                        "instructor_name": r["instructor_name"],
                        "created_at": _iso(r["created_at"]),
                    }
                    for r in rows
                ],
            }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[academia-ugc] list_courses failed: {e!r}")
        return {"total": 0, "limit": limit, "offset": offset, "courses": []}


@router.get("/course/{slug}")
async def get_course(slug: str):
    """Single course detail + review aggregate (avg rating, count, recent reviews)."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            c = await conn.fetchrow(
                """
                SELECT c.id, c.slug, c.title_he, c.description_he, c.price_ils, c.price_slh,
                       c.materials_url, c.preview_url, c.language, c.approval_status, c.active,
                       c.instructor_id, c.created_at,
                       i.display_name AS instructor_name, i.user_id AS instructor_user_id
                FROM academy_courses c
                LEFT JOIN academy_instructors i ON i.id = c.instructor_id
                WHERE c.slug = $1
                """,
                slug,
            )
            if not c:
                raise HTTPException(status_code=404, detail="course not found")

            agg = await conn.fetchrow(
                """
                SELECT COUNT(*) AS n,
                       COALESCE(AVG(rating), 0) AS avg_rating
                FROM academy_reviews
                WHERE course_id = $1
                """,
                c["id"],
            )
            recent = await conn.fetch(
                """
                SELECT id, user_id, rating, comment_he, created_at
                FROM academy_reviews
                WHERE course_id = $1
                ORDER BY created_at DESC
                LIMIT 20
                """,
                c["id"],
            )
            return {
                "id": c["id"],
                "slug": c["slug"],
                "title_he": c["title_he"],
                "description_he": c["description_he"],
                "price_ils": _to_float(c["price_ils"]),
                "price_slh": _to_float(c["price_slh"]),
                "materials_url": c["materials_url"],
                "preview_url": c["preview_url"],
                "language": c["language"],
                "approval_status": c["approval_status"],
                "active": bool(c["active"]),
                "instructor": {
                    "id": c["instructor_id"],
                    "user_id": c["instructor_user_id"],
                    "display_name": c["instructor_name"],
                } if c["instructor_id"] else None,
                "created_at": _iso(c["created_at"]),
                "reviews": {
                    "count": int(agg["n"] or 0),
                    "avg_rating": round(float(agg["avg_rating"] or 0), 2),
                    "recent": [
                        {
                            "id": r["id"],
                            "user_id": r["user_id"],
                            "rating": int(r["rating"]),
                            "comment_he": r["comment_he"],
                            "created_at": _iso(r["created_at"]),
                        }
                        for r in recent
                    ],
                },
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] get_course failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENDPOINTS — REVIEWS
# ============================================================

@router.post("/review")
async def post_review(payload: ReviewIn):
    """Student review. Requires an active license on the course."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            # Verify the user owns an active license for this course
            license_id = await conn.fetchval(
                """
                SELECT id FROM academy_licenses
                WHERE user_id = $1 AND course_id = $2 AND status = 'active'
                LIMIT 1
                """,
                payload.user_id,
                payload.course_id,
            )
            if not license_id:
                raise HTTPException(
                    status_code=403,
                    detail="must own an active license to review",
                )

            # Upsert review (unique on (course_id, user_id))
            row = await conn.fetchrow(
                """
                INSERT INTO academy_reviews (course_id, user_id, rating, comment_he)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (course_id, user_id)
                DO UPDATE SET rating = EXCLUDED.rating,
                              comment_he = EXCLUDED.comment_he,
                              created_at = NOW()
                RETURNING id, created_at
                """,
                payload.course_id,
                payload.user_id,
                payload.rating,
                payload.comment_he,
            )
            return {
                "id": row["id"],
                "created_at": _iso(row["created_at"]),
                "message": "תודה על הביקורת!",
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] post_review failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENDPOINTS — EARNINGS
# ============================================================

@router.get("/earnings/{instructor_user_id}")
async def get_earnings(instructor_user_id: int):
    """Lifetime + unpaid earnings for an instructor (by their telegram user_id)."""
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            instr = await _get_instructor_by_user(conn, instructor_user_id)
            if not instr:
                raise HTTPException(status_code=404, detail="instructor not found")

            agg = await conn.fetchrow(
                """
                SELECT
                    COALESCE(SUM(gross_ils), 0)            AS gross_ils,
                    COALESCE(SUM(platform_cut_ils), 0)     AS platform_cut,
                    COALESCE(SUM(instructor_cut_ils), 0)   AS instructor_cut,
                    COALESCE(SUM(instructor_cut_ils) FILTER (WHERE paid_out = FALSE), 0) AS unpaid,
                    COALESCE(SUM(instructor_cut_ils) FILTER (WHERE paid_out = TRUE), 0)  AS paid,
                    COUNT(*) AS sales
                FROM academy_earnings
                WHERE instructor_id = $1
                """,
                instr["id"],
            )

            recent = await conn.fetch(
                """
                SELECT id, course_id, license_id, gross_ils, platform_cut_ils,
                       instructor_cut_ils, paid_out, payout_tx, created_at
                FROM academy_earnings
                WHERE instructor_id = $1
                ORDER BY id DESC
                LIMIT 50
                """,
                instr["id"],
            )

            return {
                "instructor_id": instr["id"],
                "instructor_user_id": instructor_user_id,
                "totals": {
                    "gross_ils": _to_float(agg["gross_ils"]),
                    "platform_cut_ils": _to_float(agg["platform_cut"]),
                    "instructor_cut_ils": _to_float(agg["instructor_cut"]),
                    "unpaid_ils": _to_float(agg["unpaid"]),
                    "paid_ils": _to_float(agg["paid"]),
                    "sales_count": int(agg["sales"] or 0),
                },
                "split": {
                    "platform_pct": PLATFORM_CUT_PCT,
                    "instructor_pct": INSTRUCTOR_CUT_PCT,
                },
                "recent": [
                    {
                        "id": r["id"],
                        "course_id": r["course_id"],
                        "license_id": r["license_id"],
                        "gross_ils": _to_float(r["gross_ils"]),
                        "platform_cut_ils": _to_float(r["platform_cut_ils"]),
                        "instructor_cut_ils": _to_float(r["instructor_cut_ils"]),
                        "paid_out": bool(r["paid_out"]),
                        "payout_tx": r["payout_tx"],
                        "created_at": _iso(r["created_at"]),
                    }
                    for r in recent
                ],
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] get_earnings failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings/trigger-split")
async def trigger_split(
    payload: EarningsTriggerIn,
    x_admin_key: Optional[str] = Header(None),
):
    """Internal admin: compute 70/30 split for a license_id and insert ledger row.

    Idempotent: if an earnings row already exists for that license_id, returns
    {already_processed: true} without inserting again. The unique index on
    license_id is the hard guarantee.
    """
    _require_admin(x_admin_key)
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            # Idempotency check
            existing_id = await conn.fetchval(
                "SELECT id FROM academy_earnings WHERE license_id = $1",
                payload.license_id,
            )
            if existing_id:
                return {
                    "already_processed": True,
                    "earnings_id": existing_id,
                    "license_id": payload.license_id,
                }

            # Resolve license -> course -> instructor + price
            row = await conn.fetchrow(
                """
                SELECT l.id AS license_id, l.course_id,
                       c.instructor_id, c.price_ils
                FROM academy_licenses l
                JOIN academy_courses c ON c.id = l.course_id
                WHERE l.id = $1
                """,
                payload.license_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="license not found")
            if not row["instructor_id"]:
                raise HTTPException(
                    status_code=400,
                    detail="course has no instructor assigned (legacy course)",
                )

            gross = float(payload.gross_ils) if payload.gross_ils is not None else _to_float(row["price_ils"])
            if gross <= 0:
                raise HTTPException(status_code=400, detail="gross_ils must be > 0")

            platform_cut = round(gross * PLATFORM_CUT_PCT / 100.0, 2)
            instructor_cut = round(gross - platform_cut, 2)

            inserted = await conn.fetchrow(
                """
                INSERT INTO academy_earnings
                    (instructor_id, course_id, license_id,
                     gross_ils, platform_cut_ils, instructor_cut_ils, paid_out)
                VALUES ($1, $2, $3, $4, $5, $6, FALSE)
                ON CONFLICT (license_id) DO NOTHING
                RETURNING id, created_at
                """,
                row["instructor_id"],
                row["course_id"],
                row["license_id"],
                gross,
                platform_cut,
                instructor_cut,
            )
            if not inserted:
                # Race — someone inserted between our check and insert
                existing_id = await conn.fetchval(
                    "SELECT id FROM academy_earnings WHERE license_id = $1",
                    payload.license_id,
                )
                return {
                    "already_processed": True,
                    "earnings_id": existing_id,
                    "license_id": payload.license_id,
                }

            # Update instructor's cached total_earned_ils + total_students
            await conn.execute(
                """
                UPDATE academy_instructors
                   SET total_earned_ils = (
                       SELECT COALESCE(SUM(instructor_cut_ils), 0)
                         FROM academy_earnings WHERE instructor_id = $1
                   ),
                   total_students = (
                       SELECT COUNT(DISTINCT l.user_id)
                         FROM academy_licenses l
                         JOIN academy_courses c ON c.id = l.course_id
                        WHERE c.instructor_id = $1
                   )
                 WHERE id = $1
                """,
                row["instructor_id"],
            )

            return {
                "already_processed": False,
                "earnings_id": inserted["id"],
                "license_id": payload.license_id,
                "gross_ils": gross,
                "platform_cut_ils": platform_cut,
                "instructor_cut_ils": instructor_cut,
                "created_at": _iso(inserted["created_at"]),
            }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] trigger_split failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/earnings/mark-paid")
async def mark_earnings_paid(
    payload: EarningsPayoutIn,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin: mark an earnings row as paid_out with payout_tx reference.
    Emits `academy.payout_made` event.

    Idempotent: calling twice with the same earnings_id + payout_tx is a no-op."""
    _require_admin(x_admin_key)
    await _require_pool()
    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, instructor_id, license_id, instructor_cut_ils, paid_out, payout_tx "
                "FROM academy_earnings WHERE id = $1",
                payload.earnings_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="earnings row not found")
            if row["paid_out"]:
                # Idempotent — same tx is a no-op; different tx is a 409
                if (row["payout_tx"] or "") == payload.payout_tx:
                    return {
                        "already_paid": True,
                        "earnings_id": payload.earnings_id,
                        "payout_tx": row["payout_tx"],
                    }
                raise HTTPException(
                    status_code=409,
                    detail=f"already paid out with different tx ({row['payout_tx']})",
                )
            await conn.execute(
                """UPDATE academy_earnings
                     SET paid_out = TRUE,
                         payout_tx = $1,
                         payout_note = COALESCE($2, payout_note)
                   WHERE id = $3""",
                payload.payout_tx,
                payload.note,
                payload.earnings_id,
            )
            # Ensure payout_note column exists (additive, idempotent)
            await conn.execute(
                "ALTER TABLE academy_earnings ADD COLUMN IF NOT EXISTS payout_note TEXT"
            )

        # Emit event (best-effort)
        try:
            from shared.events import emit as _emit
            await _emit(_pool, "academy.payout_made", {
                "earnings_id": payload.earnings_id,
                "instructor_id": row["instructor_id"],
                "license_id": row["license_id"],
                "amount_ils": float(row["instructor_cut_ils"] or 0),
                "payout_tx": payload.payout_tx,
            }, source="api.academy.earnings.mark-paid")
        except Exception as _e:
            logger.warning(f"[academia-ugc] emit academy.payout_made failed: {_e!r}")

        return {
            "ok": True,
            "earnings_id": payload.earnings_id,
            "instructor_id": row["instructor_id"],
            "amount_ils": float(row["instructor_cut_ils"] or 0),
            "payout_tx": payload.payout_tx,
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"[academia-ugc] mark_earnings_paid failed: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))
