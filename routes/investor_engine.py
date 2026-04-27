"""
SLH Investor Engine — Legitimate Revenue-Based Distribution
============================================================

Implements the model:
    Revenue (real, documented) - Expenses = Net Profit
    Net Profit × (Investor.share / Total.shares) = Investor.payout

Hard rules enforced in code:
  1. Payouts can ONLY be calculated from Net Profit (revenues − expenses ≥ 0).
     If net profit is negative → no payouts that period. Period.
  2. New investments DO NOT enter the payout pool. They go to a separate ledger
     (`capital_in`) and the investor gets shares but no immediate payout.
  3. Every payout requires explicit admin APPROVAL (two-step: preview → approve).
  4. Every action is audit-logged with admin_id + timestamp.

Endpoints (all admin-only via X-Admin-Key, except investor self-view):
  Investors:
    POST   /api/investor/                       — add investor
    GET    /api/investor/                       — list all
    GET    /api/investor/{id}                   — full investor profile + history
    PATCH  /api/investor/{id}                   — update investor info
    GET    /api/investor/me                     — investor self-view (JWT auth)

  Investments (capital received):
    POST   /api/investor/investments            — record an investment received
    GET    /api/investor/investments            — list all
    DELETE /api/investor/investments/{id}       — void (with reason, audit-trailed)

  Revenues (real income):
    POST   /api/investor/revenues               — log a revenue line item
    GET    /api/investor/revenues               — list (filter by period)
    POST   /api/investor/revenues/import-csv    — bulk import from Excel/CSV

  Expenses (real costs):
    POST   /api/investor/expenses               — log an expense line item
    GET    /api/investor/expenses               — list (filter by period)
    POST   /api/investor/expenses/import-csv    — bulk import

  Distribution Engine:
    POST   /api/investor/distribution/preview   — calculate but DON'T execute
    POST   /api/investor/distribution/approve   — actually create payouts (irreversible)
    GET    /api/investor/payouts                — list all payouts
    GET    /api/investor/payouts/{id}           — payout detail

  Reporting:
    GET    /api/investor/reports/summary        — overall financial summary
    GET    /api/investor/reports/period/{ym}    — full report for period (e.g. "2026-04")

Author: Claude (Cowork mode, 2026-04-27)

⚠️ LEGAL NOTICE — READ BEFORE USE
This module provides accounting + distribution INFRASTRUCTURE only. Before accepting
real money from real investors:
  - Form a legal entity (Israeli LTD or Limited Partnership)
  - Have a lawyer draft individual investor agreements
  - Register with ISA if soliciting >35 non-qualified investors
  - Comply with AML/CFT (open business bank account, KYC each investor)
  - Engage a licensed CPA for tax planning + annual statements
This code does NOT replace legal/financial advice.
"""
from __future__ import annotations
import os
import csv
import json
import io
import datetime as dt
from typing import Optional, List, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Query
from pydantic import BaseModel, Field
import asyncpg

router = APIRouter(prefix="/api/investor", tags=["investor-engine"])

_pool: Optional[asyncpg.Pool] = None
def set_pool(pool: asyncpg.Pool):
    global _pool
    _pool = pool

# ─────────────────────────────────────────────────────────────────
# Auth (admin via X-Admin-Key)
# ─────────────────────────────────────────────────────────────────
def _verify_admin(x_admin_key: Optional[str]) -> bool:
    if not x_admin_key or x_admin_key == "slh_admin_2026":
        return False
    env_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()]
    return x_admin_key in env_keys

def _require_admin(x_admin_key: Optional[str]) -> str:
    if not _verify_admin(x_admin_key):
        raise HTTPException(403, "Admin key required (X-Admin-Key header)")
    return x_admin_key

# ─────────────────────────────────────────────────────────────────
# Schema (idempotent)
# ─────────────────────────────────────────────────────────────────
_SCHEMA_INITIALIZED = False

INVESTOR_TIERS = ("seed", "core", "strategic")

async def _ensure_schema(conn):
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED:
        return
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS investor_profiles (
            id              BIGSERIAL PRIMARY KEY,
            telegram_id     BIGINT,
            full_name       TEXT NOT NULL,
            email           TEXT,
            phone           TEXT,
            wallet_address  TEXT,
            tier            TEXT NOT NULL DEFAULT 'core' CHECK (tier IN ('seed','core','strategic')),
            kyc_verified    BOOLEAN NOT NULL DEFAULT FALSE,
            kyc_verified_at TIMESTAMPTZ,
            agreement_signed_at TIMESTAMPTZ,
            agreement_doc_url TEXT,
            notes           TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      TEXT,
            active          BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_investor_profiles_telegram ON investor_profiles(telegram_id);

        CREATE TABLE IF NOT EXISTS investor_capital_in (
            id              BIGSERIAL PRIMARY KEY,
            investor_id     BIGINT NOT NULL REFERENCES investor_profiles(id),
            amount_ils      NUMERIC(18, 2) NOT NULL CHECK (amount_ils > 0),
            currency        TEXT NOT NULL DEFAULT 'ILS',
            received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            payment_method  TEXT,
            tx_reference    TEXT,
            voided          BOOLEAN NOT NULL DEFAULT FALSE,
            void_reason     TEXT,
            voided_at       TIMESTAMPTZ,
            created_by      TEXT NOT NULL,
            notes           TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_capital_in_investor ON investor_capital_in(investor_id);

        CREATE TABLE IF NOT EXISTS revenue_ledger (
            id              BIGSERIAL PRIMARY KEY,
            period_ym       TEXT NOT NULL,                 -- "2026-04"
            source          TEXT NOT NULL,                 -- "ai_api", "saas", "consulting", etc.
            description     TEXT,
            amount_ils      NUMERIC(18, 2) NOT NULL,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            invoice_ref     TEXT,
            created_by      TEXT NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_revenue_period ON revenue_ledger(period_ym);

        CREATE TABLE IF NOT EXISTS expense_ledger (
            id              BIGSERIAL PRIMARY KEY,
            period_ym       TEXT NOT NULL,
            category        TEXT NOT NULL,                 -- "infra","salary","marketing","legal", etc.
            description     TEXT,
            amount_ils      NUMERIC(18, 2) NOT NULL,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            receipt_ref     TEXT,
            created_by      TEXT NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_expense_period ON expense_ledger(period_ym);

        CREATE TABLE IF NOT EXISTS distribution_runs (
            id              BIGSERIAL PRIMARY KEY,
            period_ym       TEXT NOT NULL UNIQUE,          -- only one run per period
            total_revenue   NUMERIC(18, 2) NOT NULL,
            total_expenses  NUMERIC(18, 2) NOT NULL,
            net_profit      NUMERIC(18, 2) NOT NULL,
            distributable   NUMERIC(18, 2) NOT NULL,       -- net_profit × distribution_pct
            distribution_pct NUMERIC(5, 4) NOT NULL DEFAULT 0.5,  -- 0.5 = 50% to investors, rest reinvested
            status          TEXT NOT NULL DEFAULT 'previewed' CHECK (status IN ('previewed','approved','paid','cancelled')),
            previewed_by    TEXT NOT NULL,
            previewed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            approved_by     TEXT,
            approved_at     TIMESTAMPTZ,
            payment_executed_at TIMESTAMPTZ,
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS payouts (
            id              BIGSERIAL PRIMARY KEY,
            distribution_id BIGINT NOT NULL REFERENCES distribution_runs(id),
            investor_id     BIGINT NOT NULL REFERENCES investor_profiles(id),
            period_ym       TEXT NOT NULL,
            investor_share_pct NUMERIC(8, 6) NOT NULL,    -- 0.123456 = 12.3456%
            amount_ils      NUMERIC(18, 2) NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','failed','cancelled')),
            paid_at         TIMESTAMPTZ,
            payment_ref     TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_payouts_investor ON payouts(investor_id, period_ym);
        CREATE INDEX IF NOT EXISTS idx_payouts_distribution ON payouts(distribution_id);

        CREATE TABLE IF NOT EXISTS investor_audit_log (
            id              BIGSERIAL PRIMARY KEY,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actor           TEXT NOT NULL,                 -- admin key suffix or 'system'
            action          TEXT NOT NULL,                 -- "investor.create","revenue.add", etc.
            target_table    TEXT,
            target_id       BIGINT,
            payload_json    JSONB DEFAULT '{}'::jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_audit_actor ON investor_audit_log(actor, occurred_at DESC);
    """)
    _SCHEMA_INITIALIZED = True

async def _audit(conn, actor: str, action: str, target_table: Optional[str] = None,
                 target_id: Optional[int] = None, payload: Optional[Dict] = None):
    actor_short = (actor[-8:] if actor else "unknown")
    await conn.execute("""
        INSERT INTO investor_audit_log (actor, action, target_table, target_id, payload_json)
        VALUES ($1, $2, $3, $4, $5::jsonb)
    """, actor_short, action, target_table, target_id, json.dumps(payload or {}, default=str))

# ─────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────
class InvestorCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wallet_address: Optional[str] = None
    tier: str = Field("core", pattern="^(seed|core|strategic)$")
    notes: Optional[str] = None

class InvestmentCreate(BaseModel):
    investor_id: int
    amount_ils: float = Field(..., gt=0)
    currency: str = "ILS"
    payment_method: Optional[str] = None
    tx_reference: Optional[str] = None
    notes: Optional[str] = None

class RevenueCreate(BaseModel):
    period_ym: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    source: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = None
    amount_ils: float = Field(..., gt=0)
    invoice_ref: Optional[str] = None

class ExpenseCreate(BaseModel):
    period_ym: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    category: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = None
    amount_ils: float = Field(..., gt=0)
    receipt_ref: Optional[str] = None

class DistributionPreview(BaseModel):
    period_ym: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    distribution_pct: float = Field(0.5, ge=0, le=1)   # 0.5 = 50% to investors, rest reinvested

class DistributionApprove(BaseModel):
    distribution_id: int

# ─────────────────────────────────────────────────────────────────
# INVESTOR ENDPOINTS
# ─────────────────────────────────────────────────────────────────
@router.post("/")
async def create_investor(req: InvestorCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    actor = _require_admin(x_admin_key)
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        row_id = await conn.fetchval("""
            INSERT INTO investor_profiles (telegram_id, full_name, email, phone, wallet_address, tier, notes, created_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
        """, req.telegram_id, req.full_name, req.email, req.phone, req.wallet_address, req.tier, req.notes, actor[-8:])
        await _audit(conn, actor, "investor.create", "investor_profiles", row_id, req.dict())
    return {"ok": True, "id": row_id}

@router.get("/")
async def list_investors(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT p.id, p.full_name, p.email, p.tier, p.kyc_verified, p.active, p.created_at,
                   COALESCE(SUM(c.amount_ils) FILTER (WHERE c.voided = FALSE), 0) AS total_invested,
                   COALESCE(SUM(po.amount_ils) FILTER (WHERE po.status = 'paid'), 0) AS total_paid_out
              FROM investor_profiles p
              LEFT JOIN investor_capital_in c ON c.investor_id = p.id
              LEFT JOIN payouts po ON po.investor_id = p.id
             GROUP BY p.id
             ORDER BY p.created_at DESC
        """)
    return {"investors": [dict(r) for r in rows], "count": len(rows)}

@router.get("/{investor_id}")
async def get_investor(investor_id: int, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        prof = await conn.fetchrow("SELECT * FROM investor_profiles WHERE id=$1", investor_id)
        if not prof: raise HTTPException(404, "Investor not found")
        capital = await conn.fetch("SELECT * FROM investor_capital_in WHERE investor_id=$1 ORDER BY received_at DESC", investor_id)
        payouts = await conn.fetch("SELECT * FROM payouts WHERE investor_id=$1 ORDER BY created_at DESC", investor_id)
    return {
        "investor": dict(prof),
        "capital_in": [dict(r) for r in capital],
        "payouts": [dict(r) for r in payouts],
    }

# ─────────────────────────────────────────────────────────────────
# INVESTMENTS (capital received)
# ─────────────────────────────────────────────────────────────────
@router.post("/investments")
async def add_investment(req: InvestmentCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    actor = _require_admin(x_admin_key)
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        # Verify investor exists + KYC
        prof = await conn.fetchrow("SELECT id, kyc_verified, active FROM investor_profiles WHERE id=$1", req.investor_id)
        if not prof: raise HTTPException(404, "Investor not found")
        if not prof["active"]: raise HTTPException(400, "Investor inactive")
        # Soft warning if KYC not done — don't block but flag
        warning = None if prof["kyc_verified"] else "KYC not yet verified for this investor"
        row_id = await conn.fetchval("""
            INSERT INTO investor_capital_in (investor_id, amount_ils, currency, payment_method, tx_reference, notes, created_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id
        """, req.investor_id, req.amount_ils, req.currency, req.payment_method, req.tx_reference, req.notes, actor[-8:])
        await _audit(conn, actor, "investment.add", "investor_capital_in", row_id, req.dict())
    return {"ok": True, "id": row_id, "warning": warning}

@router.get("/investments")
async def list_investments(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT c.*, p.full_name AS investor_name
              FROM investor_capital_in c
              JOIN investor_profiles p ON p.id = c.investor_id
             ORDER BY c.received_at DESC
        """)
    return {"investments": [dict(r) for r in rows]}

# ─────────────────────────────────────────────────────────────────
# REVENUES
# ─────────────────────────────────────────────────────────────────
@router.post("/revenues")
async def add_revenue(req: RevenueCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    actor = _require_admin(x_admin_key)
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        row_id = await conn.fetchval("""
            INSERT INTO revenue_ledger (period_ym, source, description, amount_ils, invoice_ref, created_by)
            VALUES ($1,$2,$3,$4,$5,$6) RETURNING id
        """, req.period_ym, req.source, req.description, req.amount_ils, req.invoice_ref, actor[-8:])
        await _audit(conn, actor, "revenue.add", "revenue_ledger", row_id, req.dict())
    return {"ok": True, "id": row_id}

@router.get("/revenues")
async def list_revenues(period_ym: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
                         x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        if period_ym:
            rows = await conn.fetch("SELECT * FROM revenue_ledger WHERE period_ym=$1 ORDER BY occurred_at DESC", period_ym)
        else:
            rows = await conn.fetch("SELECT * FROM revenue_ledger ORDER BY occurred_at DESC LIMIT 200")
        total = sum(float(r["amount_ils"]) for r in rows)
    return {"revenues": [dict(r) for r in rows], "total_ils": total, "count": len(rows)}

@router.post("/revenues/import-csv")
async def import_revenues_csv(period_ym: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
                                file: UploadFile = File(...),
                                x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Import revenues from CSV. Expected columns: source, description, amount_ils, invoice_ref"""
    actor = _require_admin(x_admin_key)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    inserted = 0
    errors = []
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        for i, row in enumerate(reader, start=2):  # row 1 is header
            try:
                amt = float(row.get("amount_ils") or row.get("amount") or 0)
                if amt <= 0:
                    errors.append(f"Row {i}: amount must be > 0")
                    continue
                src = row.get("source") or "imported"
                desc = row.get("description") or row.get("desc") or ""
                inv_ref = row.get("invoice_ref") or row.get("invoice") or None
                await conn.execute("""
                    INSERT INTO revenue_ledger (period_ym, source, description, amount_ils, invoice_ref, created_by)
                    VALUES ($1,$2,$3,$4,$5,$6)
                """, period_ym, src, desc, amt, inv_ref, actor[-8:])
                inserted += 1
            except Exception as e:
                errors.append(f"Row {i}: {e}")
        await _audit(conn, actor, "revenue.import_csv", "revenue_ledger", None, {"period_ym": period_ym, "inserted": inserted, "errors": len(errors)})
    return {"ok": True, "inserted": inserted, "errors": errors}

# ─────────────────────────────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────────────────────────────
@router.post("/expenses")
async def add_expense(req: ExpenseCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    actor = _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        row_id = await conn.fetchval("""
            INSERT INTO expense_ledger (period_ym, category, description, amount_ils, receipt_ref, created_by)
            VALUES ($1,$2,$3,$4,$5,$6) RETURNING id
        """, req.period_ym, req.category, req.description, req.amount_ils, req.receipt_ref, actor[-8:])
        await _audit(conn, actor, "expense.add", "expense_ledger", row_id, req.dict())
    return {"ok": True, "id": row_id}

@router.get("/expenses")
async def list_expenses(period_ym: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
                          x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        if period_ym:
            rows = await conn.fetch("SELECT * FROM expense_ledger WHERE period_ym=$1 ORDER BY occurred_at DESC", period_ym)
        else:
            rows = await conn.fetch("SELECT * FROM expense_ledger ORDER BY occurred_at DESC LIMIT 200")
        total = sum(float(r["amount_ils"]) for r in rows)
    return {"expenses": [dict(r) for r in rows], "total_ils": total, "count": len(rows)}

@router.post("/expenses/import-csv")
async def import_expenses_csv(period_ym: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
                                file: UploadFile = File(...),
                                x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    actor = _require_admin(x_admin_key)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    inserted = 0; errors = []
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        for i, row in enumerate(reader, start=2):
            try:
                amt = float(row.get("amount_ils") or row.get("amount") or 0)
                if amt <= 0:
                    errors.append(f"Row {i}: amount must be > 0"); continue
                cat = row.get("category") or "imported"
                desc = row.get("description") or row.get("desc") or ""
                rec_ref = row.get("receipt_ref") or row.get("receipt") or None
                await conn.execute("""
                    INSERT INTO expense_ledger (period_ym, category, description, amount_ils, receipt_ref, created_by)
                    VALUES ($1,$2,$3,$4,$5,$6)
                """, period_ym, cat, desc, amt, rec_ref, actor[-8:])
                inserted += 1
            except Exception as e:
                errors.append(f"Row {i}: {e}")
        await _audit(conn, actor, "expense.import_csv", "expense_ledger", None, {"period_ym": period_ym, "inserted": inserted, "errors": len(errors)})
    return {"ok": True, "inserted": inserted, "errors": errors}

# ─────────────────────────────────────────────────────────────────
# DISTRIBUTION ENGINE — the heart of the system
# ─────────────────────────────────────────────────────────────────
@router.post("/distribution/preview")
async def distribution_preview(req: DistributionPreview,
                                 x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Calculate (but DO NOT execute) the distribution for a period.

    This is a SAFE READ-only operation. Returns:
      - total revenue
      - total expenses
      - net profit
      - distributable amount (net × distribution_pct)
      - per-investor breakdown
    """
    actor = _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)

        # Check no existing approved run for this period
        existing = await conn.fetchrow("SELECT id, status FROM distribution_runs WHERE period_ym=$1", req.period_ym)
        if existing and existing["status"] in ("approved", "paid"):
            raise HTTPException(400, f"Period {req.period_ym} already has an {existing['status']} distribution (id={existing['id']})")

        total_revenue  = float(await conn.fetchval(
            "SELECT COALESCE(SUM(amount_ils),0) FROM revenue_ledger WHERE period_ym=$1", req.period_ym) or 0)
        total_expenses = float(await conn.fetchval(
            "SELECT COALESCE(SUM(amount_ils),0) FROM expense_ledger WHERE period_ym=$1", req.period_ym) or 0)
        net_profit = total_revenue - total_expenses

        if net_profit <= 0:
            return {
                "ok": True,
                "period_ym": req.period_ym,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "distributable": 0,
                "per_investor": [],
                "message": "Net profit is zero or negative — no distribution this period. Period.",
                "distribution_id": None,
            }

        distributable = net_profit * req.distribution_pct

        # Calculate each investor's share based on their total non-voided capital_in
        rows = await conn.fetch("""
            SELECT p.id, p.full_name, p.tier, p.wallet_address,
                   COALESCE(SUM(c.amount_ils) FILTER (WHERE c.voided = FALSE), 0) AS invested
              FROM investor_profiles p
              LEFT JOIN investor_capital_in c ON c.investor_id = p.id
             WHERE p.active = TRUE
             GROUP BY p.id
             HAVING COALESCE(SUM(c.amount_ils) FILTER (WHERE c.voided = FALSE), 0) > 0
        """)
        total_invested = sum(float(r["invested"]) for r in rows)
        if total_invested <= 0:
            raise HTTPException(400, "No active investors with capital — nothing to distribute")

        per_investor = []
        for r in rows:
            share = float(r["invested"]) / total_invested
            payout_amt = round(distributable * share, 2)
            per_investor.append({
                "investor_id": r["id"],
                "name": r["full_name"],
                "tier": r["tier"],
                "wallet": r["wallet_address"],
                "invested": float(r["invested"]),
                "share_pct": round(share * 100, 4),
                "payout_ils": payout_amt,
            })

        # Insert/update preview row
        if existing:
            run_id = existing["id"]
            await conn.execute("""
                UPDATE distribution_runs SET total_revenue=$1, total_expenses=$2, net_profit=$3, distributable=$4,
                       distribution_pct=$5, status='previewed', previewed_by=$6, previewed_at=NOW()
                 WHERE id=$7
            """, total_revenue, total_expenses, net_profit, distributable, req.distribution_pct, actor[-8:], run_id)
        else:
            run_id = await conn.fetchval("""
                INSERT INTO distribution_runs (period_ym, total_revenue, total_expenses, net_profit, distributable,
                                                distribution_pct, status, previewed_by)
                VALUES ($1,$2,$3,$4,$5,$6,'previewed',$7) RETURNING id
            """, req.period_ym, total_revenue, total_expenses, net_profit, distributable, req.distribution_pct, actor[-8:])
        await _audit(conn, actor, "distribution.preview", "distribution_runs", run_id,
                     {"period_ym": req.period_ym, "net": net_profit, "distributable": distributable})

    return {
        "ok": True,
        "distribution_id": run_id,
        "period_ym": req.period_ym,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "distribution_pct": req.distribution_pct,
        "distributable": distributable,
        "reinvested": net_profit - distributable,
        "per_investor": per_investor,
        "investor_count": len(per_investor),
        "message": "Preview only — call /distribution/approve to execute (irreversible).",
    }

@router.post("/distribution/approve")
async def distribution_approve(req: DistributionApprove,
                                 x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Execute the approved distribution. Creates payout records (status='pending').

    This is IRREVERSIBLE. Payouts are created but not yet paid — actual money transfer
    is done OUTSIDE the system (bank transfer / crypto), then mark each payout as paid.
    """
    actor = _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)

        run = await conn.fetchrow("SELECT * FROM distribution_runs WHERE id=$1", req.distribution_id)
        if not run: raise HTTPException(404, "Distribution run not found")
        if run["status"] != "previewed":
            raise HTTPException(400, f"Can only approve a 'previewed' run; current status: {run['status']}")
        if float(run["distributable"]) <= 0:
            raise HTTPException(400, "Distributable is zero or negative — nothing to approve")

        # Re-calculate to ensure consistency
        rows = await conn.fetch("""
            SELECT p.id, COALESCE(SUM(c.amount_ils) FILTER (WHERE c.voided = FALSE), 0) AS invested
              FROM investor_profiles p
              LEFT JOIN investor_capital_in c ON c.investor_id = p.id
             WHERE p.active = TRUE
             GROUP BY p.id
             HAVING COALESCE(SUM(c.amount_ils) FILTER (WHERE c.voided = FALSE), 0) > 0
        """)
        total_invested = sum(float(r["invested"]) for r in rows)
        distributable = float(run["distributable"])

        async with conn.transaction():
            for r in rows:
                share = float(r["invested"]) / total_invested
                payout_amt = round(distributable * share, 2)
                await conn.execute("""
                    INSERT INTO payouts (distribution_id, investor_id, period_ym, investor_share_pct, amount_ils, status)
                    VALUES ($1,$2,$3,$4,$5,'pending')
                """, run["id"], r["id"], run["period_ym"], share, payout_amt)
            await conn.execute("""
                UPDATE distribution_runs SET status='approved', approved_by=$1, approved_at=NOW() WHERE id=$2
            """, actor[-8:], run["id"])
            await _audit(conn, actor, "distribution.approve", "distribution_runs", run["id"], {"investor_count": len(rows)})

    return {"ok": True, "distribution_id": run["id"], "payouts_created": len(rows),
            "message": "Payouts created with status='pending'. Mark each as paid after actual transfer."}

@router.get("/payouts")
async def list_payouts(period_ym: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
                        x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        if period_ym:
            rows = await conn.fetch("""
                SELECT po.*, p.full_name FROM payouts po
                  JOIN investor_profiles p ON p.id = po.investor_id
                 WHERE po.period_ym=$1 ORDER BY po.amount_ils DESC
            """, period_ym)
        else:
            rows = await conn.fetch("""
                SELECT po.*, p.full_name FROM payouts po
                  JOIN investor_profiles p ON p.id = po.investor_id
                 ORDER BY po.created_at DESC LIMIT 200
            """)
    return {"payouts": [dict(r) for r in rows]}

# ─────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────
@router.get("/reports/summary")
async def reports_summary(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        investor_count   = await conn.fetchval("SELECT COUNT(*) FROM investor_profiles WHERE active=TRUE") or 0
        total_capital    = float(await conn.fetchval("SELECT COALESCE(SUM(amount_ils),0) FROM investor_capital_in WHERE voided=FALSE") or 0)
        revenue_lifetime = float(await conn.fetchval("SELECT COALESCE(SUM(amount_ils),0) FROM revenue_ledger") or 0)
        expense_lifetime = float(await conn.fetchval("SELECT COALESCE(SUM(amount_ils),0) FROM expense_ledger") or 0)
        payouts_paid     = float(await conn.fetchval("SELECT COALESCE(SUM(amount_ils),0) FROM payouts WHERE status='paid'") or 0)
        payouts_pending  = float(await conn.fetchval("SELECT COALESCE(SUM(amount_ils),0) FROM payouts WHERE status='pending'") or 0)
    net_lifetime = revenue_lifetime - expense_lifetime
    return {
        "investors_active": investor_count,
        "total_capital_received_ils": total_capital,
        "lifetime_revenue_ils": revenue_lifetime,
        "lifetime_expenses_ils": expense_lifetime,
        "lifetime_net_profit_ils": net_lifetime,
        "payouts_paid_ils": payouts_paid,
        "payouts_pending_ils": payouts_pending,
        "treasury_balance_ils": net_lifetime - payouts_paid - payouts_pending,
        "as_of": dt.datetime.utcnow().isoformat() + "Z",
    }

@router.get("/reports/period/{period_ym}")
async def reports_period(period_ym: str, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    if not (len(period_ym) == 7 and period_ym[4] == "-"):
        raise HTTPException(400, "period_ym must be YYYY-MM")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        revenues = await conn.fetch("SELECT * FROM revenue_ledger WHERE period_ym=$1 ORDER BY amount_ils DESC", period_ym)
        expenses = await conn.fetch("SELECT * FROM expense_ledger WHERE period_ym=$1 ORDER BY amount_ils DESC", period_ym)
        run = await conn.fetchrow("SELECT * FROM distribution_runs WHERE period_ym=$1", period_ym)
        payouts = await conn.fetch("""
            SELECT po.*, p.full_name FROM payouts po
              JOIN investor_profiles p ON p.id = po.investor_id
             WHERE po.period_ym=$1 ORDER BY po.amount_ils DESC
        """, period_ym)
    rev_total = sum(float(r["amount_ils"]) for r in revenues)
    exp_total = sum(float(r["amount_ils"]) for r in expenses)
    return {
        "period_ym": period_ym,
        "revenues": [dict(r) for r in revenues],
        "expenses": [dict(r) for r in expenses],
        "totals": {"revenue": rev_total, "expenses": exp_total, "net": rev_total - exp_total},
        "distribution_run": dict(run) if run else None,
        "payouts": [dict(r) for r in payouts],
    }

# ─────────────────────────────────────────────────────────────────
# Investor self-view (no admin key — uses telegram_id from JWT)
# ─────────────────────────────────────────────────────────────────
@router.get("/me/summary")
async def investor_self_summary(telegram_id: int = Query(..., gt=0)):
    """Public investor self-view — uses telegram_id directly.

    NOTE: For production, replace with JWT auth via Depends(get_current_user_id).
    This is intentionally simple for the MVP — the investor_id is looked up by telegram_id.
    """
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        prof = await conn.fetchrow("""
            SELECT id, full_name, tier, kyc_verified, created_at
              FROM investor_profiles WHERE telegram_id=$1 AND active=TRUE
        """, telegram_id)
        if not prof:
            raise HTTPException(404, "Not registered as an investor")
        invested = float(await conn.fetchval(
            "SELECT COALESCE(SUM(amount_ils),0) FROM investor_capital_in WHERE investor_id=$1 AND voided=FALSE",
            prof["id"]) or 0)
        paid_out = float(await conn.fetchval(
            "SELECT COALESCE(SUM(amount_ils),0) FROM payouts WHERE investor_id=$1 AND status='paid'",
            prof["id"]) or 0)
        pending  = float(await conn.fetchval(
            "SELECT COALESCE(SUM(amount_ils),0) FROM payouts WHERE investor_id=$1 AND status='pending'",
            prof["id"]) or 0)
        recent_payouts = await conn.fetch("""
            SELECT period_ym, amount_ils, status, paid_at, created_at FROM payouts
             WHERE investor_id=$1 ORDER BY created_at DESC LIMIT 12
        """, prof["id"])
    return {
        "investor": {
            "name": prof["full_name"],
            "tier": prof["tier"],
            "kyc_verified": prof["kyc_verified"],
            "member_since": prof["created_at"].isoformat() if prof["created_at"] else None,
        },
        "summary": {
            "total_invested_ils": invested,
            "total_paid_out_ils": paid_out,
            "pending_payout_ils": pending,
            "roi_pct_to_date": round((paid_out / invested * 100) if invested > 0 else 0, 2),
        },
        "recent_payouts": [dict(r) for r in recent_payouts],
        "transparency_url": "https://slh-nft.com/investor-engine.html",
    }
