"""SLH Expense Tracker — personal cashflow management for the owner + family.

Built after Osif raised:
  'אולי בשלב זה כדאי שנכנסי למערכת את טבלאת ההוצאות שלי? זה יכול להיות צעד חכם
   נגיד שכ"ד אני משלם 6900 ארנונה אם אני לא טועה כרגע 2300 דלק והוצאות שוטפות כ 600 ש"ח
   מוסכים וטיפולים כ 5000 ש"ח. יש לנו ארנקים אז אולי כשירות נוסיף גם תחשיבים
   וניהול הוצאות ותזרים וכו?'

Phase 1 scope (this commit):
  - expenses table: per-user, per-category, ILS amounts, recurring flag
  - 7 endpoints under /api/expenses/*
  - Monthly summary + category breakdown
  - Recurring detection (manual flag for now; auto-detection in Phase 2)

NOT in this phase (deliberate):
  - Auto-categorization (needs LLM call — Phase 2)
  - OCR receipt upload (needs Tesseract/cloud OCR — Phase 2)
  - SLH/MNH/ZVK conversion (price feed integration — Phase 2)
  - Tax estimation for עוסק עצמאי (needs accounting rules — Phase 2)

All endpoints require X-Admin-Key for now (single-user phase). Phase 2 will
move to per-user auth via the Telegram Gateway.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query, Request
from pydantic import BaseModel, Field

log = logging.getLogger("slh.expenses")

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


# Predefined categories Osif mentioned + extras a personal finance flow needs.
DEFAULT_CATEGORIES = [
    "rent",        # שכ"ד
    "property_tax", # ארנונה
    "fuel",        # דלק
    "auto_repair", # מוסכים, טיפולים
    "groceries",   # מזון
    "utilities",   # תקשורת, חשמל, מים
    "insurance",   # ביטוחים
    "subscriptions", # מנויים (Netflix, Spotify, AWS, etc.)
    "health",      # בריאות
    "education",   # חינוך
    "business",    # הוצאות עסקיות
    "tax",         # מס הכנסה / מע"מ
    "savings",     # חיסכון / השקעה
    "other",       # אחר
]


# ─── Models ────────────────────────────────────────────────────────────────


class ExpenseIn(BaseModel):
    user_id: int
    amount_ils: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=40)
    description: Optional[str] = Field(None, max_length=200)
    date: Optional[str] = None  # ISO date; defaults to today
    recurring: Optional[str] = Field(None, pattern=r"^(monthly|yearly|weekly|none)$")
    source: Optional[str] = Field(None, max_length=40)  # 'manual' | 'bot' | 'ocr' | 'import'


class ExpenseUpdate(BaseModel):
    amount_ils: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=40)
    description: Optional[str] = Field(None, max_length=200)
    date: Optional[str] = None
    recurring: Optional[str] = Field(None, pattern=r"^(monthly|yearly|weekly|none)$")


# ─── Auth ──────────────────────────────────────────────────────────────────


def _admin(authorization: Optional[str], x_admin_key: Optional[str]) -> int:
    try:
        from main import _require_admin
        return _require_admin(authorization, x_admin_key)
    except Exception:
        env_keys = {k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()}
        if x_admin_key and x_admin_key in env_keys:
            return 0
        raise HTTPException(403, "Admin authentication required")


# ─── Schema ────────────────────────────────────────────────────────────────

_SCHEMA_READY = False


async def _ensure_schema(pool) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id           BIGSERIAL PRIMARY KEY,
                user_id      BIGINT NOT NULL,
                amount_ils   NUMERIC(12,2) NOT NULL CHECK (amount_ils > 0),
                category     TEXT NOT NULL,
                description  TEXT,
                date         DATE NOT NULL DEFAULT CURRENT_DATE,
                recurring    TEXT NOT NULL DEFAULT 'none'
                              CHECK (recurring IN ('monthly','yearly','weekly','none')),
                source       TEXT NOT NULL DEFAULT 'manual',
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_expenses_user_date ON expenses (user_id, date DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_expenses_category_date ON expenses (category, date DESC)"
        )
    _SCHEMA_READY = True


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


def _row_to_dict(r) -> dict:
    return {
        "id": r["id"],
        "user_id": r["user_id"],
        "amount_ils": float(r["amount_ils"]),
        "category": r["category"],
        "description": r["description"],
        "date": r["date"].isoformat() if r["date"] else None,
        "recurring": r["recurring"],
        "source": r["source"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────


@router.get("/categories")
async def list_categories():
    """Public — list of predefined categories. No auth needed."""
    return {
        "categories": [
            {"key": c, "label": _CATEGORY_LABELS.get(c, c)} for c in DEFAULT_CATEGORIES
        ],
    }


_CATEGORY_LABELS = {
    "rent": "שכ\"ד",
    "property_tax": "ארנונה",
    "fuel": "דלק",
    "auto_repair": "מוסכים וטיפולי רכב",
    "groceries": "מזון",
    "utilities": "תקשורת / חשמל / מים",
    "insurance": "ביטוחים",
    "subscriptions": "מנויים",
    "health": "בריאות",
    "education": "חינוך",
    "business": "עסקי",
    "tax": "מס",
    "savings": "חיסכון / השקעה",
    "other": "אחר",
}


@router.post("")
async def create_expense(
    body: ExpenseIn,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    # Parse date if given
    date_val = None
    if body.date:
        try:
            date_val = datetime.fromisoformat(body.date).date()
        except Exception:
            raise HTTPException(400, "invalid date format (use YYYY-MM-DD)")

    async with pool.acquire() as conn:
        if date_val:
            row = await conn.fetchrow(
                """
                INSERT INTO expenses (user_id, amount_ils, category, description, date, recurring, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                body.user_id, body.amount_ils, body.category, body.description,
                date_val, body.recurring or "none", body.source or "manual",
            )
        else:
            row = await conn.fetchrow(
                """
                INSERT INTO expenses (user_id, amount_ils, category, description, recurring, source)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                body.user_id, body.amount_ils, body.category, body.description,
                body.recurring or "none", body.source or "manual",
            )

    # Emit public event for activity feed (sanitized — no description)
    try:
        from shared.events import emit as _emit
        await _emit(pool, "expense.recorded", {
            "user_id": body.user_id,
            "amount_ils": float(body.amount_ils),
            "category": body.category,
            "recurring": body.recurring or "none",
        }, source="api.expenses")
    except Exception:
        pass

    return {"ok": True, "expense": _row_to_dict(row)}


@router.get("/{user_id}")
async def list_expenses(
    user_id: int,
    request: Request,
    limit: int = Query(100, le=500),
    category: Optional[str] = None,
    days: int = Query(90, ge=1, le=3650),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        if category:
            rows = await conn.fetch(
                """
                SELECT * FROM expenses
                 WHERE user_id = $1 AND category = $2
                   AND date >= CURRENT_DATE - ($3 || ' days')::interval
                 ORDER BY date DESC, id DESC LIMIT $4
                """,
                user_id, category, str(days), limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM expenses
                 WHERE user_id = $1
                   AND date >= CURRENT_DATE - ($2 || ' days')::interval
                 ORDER BY date DESC, id DESC LIMIT $3
                """,
                user_id, str(days), limit,
            )
    return {"count": len(rows), "expenses": [_row_to_dict(r) for r in rows]}


@router.patch("/item/{expense_id}")
async def update_expense(
    expense_id: int,
    body: ExpenseUpdate,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    fields = []
    values = []
    for k in ("amount_ils", "category", "description", "recurring"):
        v = getattr(body, k)
        if v is not None:
            fields.append(f"{k} = ${len(values) + 1}")
            values.append(v)
    if body.date is not None:
        try:
            d = datetime.fromisoformat(body.date).date()
        except Exception:
            raise HTTPException(400, "invalid date")
        fields.append(f"date = ${len(values) + 1}")
        values.append(d)
    if not fields:
        raise HTTPException(400, "nothing to update")

    fields.append("updated_at = NOW()")
    values.append(expense_id)
    sql = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ${len(values)} RETURNING *"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)
    if not row:
        raise HTTPException(404, "expense not found")
    return {"ok": True, "expense": _row_to_dict(row)}


@router.delete("/item/{expense_id}")
async def delete_expense(
    expense_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM expenses WHERE id = $1", expense_id)
    if result.endswith("DELETE 0"):
        raise HTTPException(404, "expense not found")
    return {"ok": True}


@router.get("/{user_id}/summary")
async def expenses_summary(
    user_id: int,
    request: Request,
    months: int = Query(6, ge=1, le=24),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Monthly totals + category breakdown + recurring vs ad-hoc split.

    The shape is shaped for direct rendering in /miniapp/expenses.html — one
    fetch gives the page everything it needs.
    """
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        # Monthly totals (last N months)
        monthly = await conn.fetch(
            """
            SELECT to_char(date_trunc('month', date), 'YYYY-MM') AS month,
                   SUM(amount_ils)::float AS total,
                   COUNT(*)::int AS count
              FROM expenses
             WHERE user_id = $1
               AND date >= (CURRENT_DATE - ($2 || ' months')::interval)
             GROUP BY month
             ORDER BY month ASC
            """,
            user_id, str(months),
        )
        # Category breakdown for current month
        by_category = await conn.fetch(
            """
            SELECT category,
                   SUM(amount_ils)::float AS total,
                   COUNT(*)::int AS count
              FROM expenses
             WHERE user_id = $1
               AND date >= date_trunc('month', CURRENT_DATE)
             GROUP BY category
             ORDER BY total DESC
            """,
            user_id,
        )
        # Recurring summary (the "fixed costs" you can budget against)
        recurring = await conn.fetch(
            """
            SELECT category, recurring,
                   AVG(amount_ils)::float AS avg_amount,
                   MAX(date) AS last_seen
              FROM expenses
             WHERE user_id = $1 AND recurring IN ('monthly', 'yearly', 'weekly')
             GROUP BY category, recurring
             ORDER BY avg_amount DESC
            """,
            user_id,
        )
        # Burn rate — average monthly total over last 3 months
        burn = await conn.fetchval(
            """
            SELECT COALESCE(AVG(monthly_total), 0)::float
              FROM (
                SELECT SUM(amount_ils) AS monthly_total
                  FROM expenses
                 WHERE user_id = $1
                   AND date >= (CURRENT_DATE - INTERVAL '3 months')
                 GROUP BY date_trunc('month', date)
              ) m
            """,
            user_id,
        )

    return {
        "monthly": [
            {"month": r["month"], "total": r["total"], "count": r["count"]}
            for r in monthly
        ],
        "by_category": [
            {
                "category": r["category"],
                "label": _CATEGORY_LABELS.get(r["category"], r["category"]),
                "total": r["total"],
                "count": r["count"],
            }
            for r in by_category
        ],
        "recurring": [
            {
                "category": r["category"],
                "label": _CATEGORY_LABELS.get(r["category"], r["category"]),
                "recurring": r["recurring"],
                "avg_amount": r["avg_amount"],
                "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
            }
            for r in recurring
        ],
        "burn_rate_monthly_avg": float(burn or 0),
    }


@router.post("/{user_id}/seed")
async def seed_initial(
    user_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """One-time seed of Osif's monthly fixed costs. Idempotent — checks if any
    expenses exist for this user this month before inserting."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    seed_data = [
        {"category": "rent",         "amount_ils": 6900, "recurring": "monthly", "description": "שכ\"ד דירה"},
        {"category": "property_tax", "amount_ils": 2300, "recurring": "monthly", "description": "ארנונה"},
        {"category": "fuel",         "amount_ils":  600, "recurring": "monthly", "description": "דלק חודשי"},
        {"category": "auto_repair",  "amount_ils": 5000, "recurring": "yearly",  "description": "מוסכים וטיפולים (אומדן שנתי)"},
    ]

    async with pool.acquire() as conn:
        existing = await conn.fetchval(
            """
            SELECT COUNT(*) FROM expenses
             WHERE user_id = $1 AND source = 'seed'
               AND date >= date_trunc('month', CURRENT_DATE)
            """,
            user_id,
        )
        if (existing or 0) > 0:
            return {"ok": False, "skipped": True, "reason": "user already seeded this month"}

        inserted = []
        for s in seed_data:
            row = await conn.fetchrow(
                """
                INSERT INTO expenses (user_id, amount_ils, category, description, recurring, source)
                VALUES ($1, $2, $3, $4, $5, 'seed')
                RETURNING *
                """,
                user_id, s["amount_ils"], s["category"], s["description"], s["recurring"],
            )
            inserted.append(_row_to_dict(row))
    return {"ok": True, "inserted": len(inserted), "expenses": inserted}
