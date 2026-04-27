"""
SLH Content Marketplace — Courses + Premium Content + Creator Revenue Share
============================================================================

A creator marketplace where:
  - Creators (Osif + friends/family) upload content (courses, videos, images)
  - Buyers pay → revenue automatically logged to revenue_ledger
  - Platform takes its cut (default 25%); creator keeps the rest (default 75%)
  - The platform's cut feeds the Distribution Engine → goes to investors per existing rules

Why this matters legally:
  This is COMMERCE, not securities. Selling courses/content is plain business.
  The platform keeps a cut (like Etsy/Gumroad/Teachable). Investor returns come
  from the platform's commission, NOT from a guarantee.

Endpoints:
  Catalog:
    GET    /api/courses/                       — public catalog of available items
    GET    /api/courses/{slug}                 — public item detail
    POST   /api/courses/                       — admin: create new item
    PATCH  /api/courses/{id}                   — admin: edit item

  Creators:
    POST   /api/courses/creators               — admin: register a creator (friend/family)
    GET    /api/courses/creators               — list all creators

  Sales:
    POST   /api/courses/checkout               — start a checkout session (returns payment instructions)
    POST   /api/courses/confirm-payment        — admin: confirm a payment was received → triggers revenue split
    GET    /api/courses/sales                  — admin: list all sales

  My library (per buyer):
    GET    /api/courses/my-library             — what the buyer purchased

Author: Claude (Cowork mode, 2026-04-27)
"""
from __future__ import annotations
import os
import json
import secrets
import datetime as dt
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
import asyncpg

router = APIRouter(prefix="/api/courses", tags=["courses"])

_pool: Optional[asyncpg.Pool] = None
def set_pool(pool: asyncpg.Pool):
    global _pool
    _pool = pool

# ─────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────
def _verify_admin(k: Optional[str]) -> bool:
    if not k or k == "slh_admin_2026": return False
    return k in [x.strip() for x in os.getenv("ADMIN_API_KEYS", "").split(",") if x.strip()]

def _require_admin(k: Optional[str]) -> str:
    if not _verify_admin(k):
        raise HTTPException(403, "Admin key required (X-Admin-Key)")
    return k

# ─────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────
_INIT = False
async def _ensure_schema(conn):
    global _INIT
    if _INIT: return
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS course_creators (
            id              BIGSERIAL PRIMARY KEY,
            telegram_id     BIGINT,
            display_name    TEXT NOT NULL,
            email           TEXT,
            bio             TEXT,
            payout_method   TEXT,
            payout_details  TEXT,
            default_split_pct NUMERIC(5,4) NOT NULL DEFAULT 0.75,
            active          BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS course_items (
            id              BIGSERIAL PRIMARY KEY,
            slug            TEXT UNIQUE NOT NULL,
            creator_id      BIGINT REFERENCES course_creators(id),
            kind            TEXT NOT NULL DEFAULT 'course' CHECK (kind IN ('course','video','image_pack','ebook','dataset','nft_card','bundle')),
            title           TEXT NOT NULL,
            subtitle        TEXT,
            description     TEXT,
            price_ils       NUMERIC(10,2) NOT NULL CHECK (price_ils > 0),
            currency        TEXT NOT NULL DEFAULT 'ILS',
            cover_image_url TEXT,
            content_url     TEXT,
            preview_url     TEXT,
            tags            TEXT[],
            language        TEXT DEFAULT 'he',
            duration_minutes INTEGER,
            creator_split_pct NUMERIC(5,4),
            published       BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            sales_count     INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_course_items_slug ON course_items(slug);
        CREATE INDEX IF NOT EXISTS idx_course_items_published ON course_items(published) WHERE published = TRUE;

        CREATE TABLE IF NOT EXISTS course_sales (
            id              BIGSERIAL PRIMARY KEY,
            order_ref       TEXT UNIQUE NOT NULL,
            item_id         BIGINT NOT NULL REFERENCES course_items(id),
            buyer_telegram_id BIGINT,
            buyer_name      TEXT,
            buyer_email     TEXT,
            amount_ils      NUMERIC(10,2) NOT NULL,
            payment_method  TEXT,
            payment_ref     TEXT,
            status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','refunded','cancelled')),
            paid_at         TIMESTAMPTZ,
            creator_split_ils NUMERIC(10,2),
            platform_split_ils NUMERIC(10,2),
            revenue_ledger_id BIGINT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_course_sales_buyer ON course_sales(buyer_telegram_id);
        CREATE INDEX IF NOT EXISTS idx_course_sales_item ON course_sales(item_id);
    """)
    _INIT = True

# ─────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────
class CreatorCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    payout_method: Optional[str] = None
    payout_details: Optional[str] = None
    default_split_pct: float = Field(0.75, ge=0, le=1)

class ItemCreate(BaseModel):
    slug: str = Field(..., min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    creator_id: Optional[int] = None
    kind: str = Field("course", pattern=r"^(course|video|image_pack|ebook|dataset|nft_card|bundle)$")
    title: str = Field(..., min_length=3, max_length=200)
    subtitle: Optional[str] = None
    description: Optional[str] = None
    price_ils: float = Field(..., gt=0)
    currency: str = "ILS"
    cover_image_url: Optional[str] = None
    content_url: Optional[str] = None
    preview_url: Optional[str] = None
    tags: Optional[List[str]] = None
    language: str = "he"
    duration_minutes: Optional[int] = None
    creator_split_pct: Optional[float] = Field(None, ge=0, le=1)
    published: bool = False

class CheckoutRequest(BaseModel):
    item_slug: str
    buyer_telegram_id: Optional[int] = None
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    payment_method: str = Field(..., pattern=r"^(bank_transfer|crypto_bsc|crypto_ton|paypal|cash|other)$")

class ConfirmPaymentRequest(BaseModel):
    order_ref: str
    payment_ref: Optional[str] = None

# ─────────────────────────────────────────────────────────────────
# CREATORS
# ─────────────────────────────────────────────────────────────────
@router.post("/creators")
async def create_creator(req: CreatorCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        cid = await conn.fetchval("""
            INSERT INTO course_creators (telegram_id, display_name, email, bio, payout_method, payout_details, default_split_pct)
            VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id
        """, req.telegram_id, req.display_name, req.email, req.bio, req.payout_method, req.payout_details, req.default_split_pct)
    return {"ok": True, "creator_id": cid}

@router.get("/creators")
async def list_creators(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT c.*, COUNT(i.id) AS item_count
              FROM course_creators c
              LEFT JOIN course_items i ON i.creator_id = c.id
             GROUP BY c.id ORDER BY c.created_at DESC
        """)
    return {"creators": [dict(r) for r in rows]}

# ─────────────────────────────────────────────────────────────────
# ITEMS (catalog)
# ─────────────────────────────────────────────────────────────────
@router.get("/")
async def public_catalog(kind: Optional[str] = Query(None), language: Optional[str] = Query(None)):
    """Public catalog — only published items. No auth required."""
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        q = """
            SELECT i.id, i.slug, i.kind, i.title, i.subtitle, i.description, i.price_ils, i.currency,
                   i.cover_image_url, i.preview_url, i.tags, i.language, i.duration_minutes, i.sales_count,
                   c.display_name AS creator_name
              FROM course_items i
              LEFT JOIN course_creators c ON c.id = i.creator_id
             WHERE i.published = TRUE
        """
        params = []
        if kind:
            params.append(kind); q += f" AND i.kind = ${len(params)}"
        if language:
            params.append(language); q += f" AND i.language = ${len(params)}"
        q += " ORDER BY i.sales_count DESC, i.created_at DESC"
        rows = await conn.fetch(q, *params)
    return {"items": [dict(r) for r in rows], "count": len(rows)}

@router.get("/{slug}")
async def item_detail(slug: str):
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        row = await conn.fetchrow("""
            SELECT i.*, c.display_name AS creator_name, c.bio AS creator_bio
              FROM course_items i
              LEFT JOIN course_creators c ON c.id = i.creator_id
             WHERE i.slug = $1 AND i.published = TRUE
        """, slug)
    if not row: raise HTTPException(404, "Item not found")
    # Don't expose content_url to public — only after purchase
    out = dict(row)
    out.pop("content_url", None)
    return out

@router.post("/")
async def create_item(req: ItemCreate, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        try:
            iid = await conn.fetchval("""
                INSERT INTO course_items (slug, creator_id, kind, title, subtitle, description, price_ils, currency,
                                          cover_image_url, content_url, preview_url, tags, language,
                                          duration_minutes, creator_split_pct, published)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16) RETURNING id
            """, req.slug, req.creator_id, req.kind, req.title, req.subtitle, req.description,
                 req.price_ils, req.currency, req.cover_image_url, req.content_url, req.preview_url,
                 req.tags, req.language, req.duration_minutes, req.creator_split_pct, req.published)
        except asyncpg.UniqueViolationError:
            raise HTTPException(400, f"Slug '{req.slug}' already exists")
    return {"ok": True, "item_id": iid, "slug": req.slug}

# ─────────────────────────────────────────────────────────────────
# CHECKOUT + PAYMENT FLOW
# ─────────────────────────────────────────────────────────────────
@router.post("/checkout")
async def checkout(req: CheckoutRequest):
    """Start a checkout. Returns order_ref + payment instructions.

    Payment is OUT-OF-BAND (bank transfer / crypto / cash). The buyer pays,
    sends the proof, then admin confirms via /confirm-payment.
    """
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        item = await conn.fetchrow("SELECT id, price_ils, title FROM course_items WHERE slug=$1 AND published=TRUE", req.item_slug)
        if not item: raise HTTPException(404, "Item not found or not published")
        order_ref = "SLH-" + secrets.token_hex(6).upper()
        await conn.execute("""
            INSERT INTO course_sales (order_ref, item_id, buyer_telegram_id, buyer_name, buyer_email,
                                      amount_ils, payment_method, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,'pending')
        """, order_ref, item["id"], req.buyer_telegram_id, req.buyer_name, req.buyer_email,
             item["price_ils"], req.payment_method)

    # Build payment instructions per method
    instructions = _payment_instructions(req.payment_method, float(item["price_ils"]), order_ref)
    return {
        "ok": True,
        "order_ref": order_ref,
        "item_title": item["title"],
        "amount_ils": float(item["price_ils"]),
        "payment_method": req.payment_method,
        "instructions": instructions,
        "next_steps": [
            "1. Complete payment using the instructions above",
            "2. Send proof of payment to @osifeu_prog (Telegram) with order_ref",
            "3. Admin confirms → access granted",
        ],
    }

def _payment_instructions(method: str, amount: float, order_ref: str) -> Dict[str, Any]:
    """Returns method-specific payment instructions. Customize with real details."""
    common = {"order_ref": order_ref, "amount_ils": amount}
    if method == "crypto_bsc":
        return {**common,
                "address": "0xD0617B54FB4b6b66307846f217b4D685800E3dA4",
                "network": "BSC (BEP-20)",
                "accepts": ["BNB", "BUSD", "USDT", "SLH"],
                "memo": f"Include order ref in tx memo: {order_ref}"}
    if method == "crypto_ton":
        return {**common,
                "address": "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp",
                "network": "TON",
                "accepts": ["TON", "MNH"],
                "memo": f"Include {order_ref} in comment"}
    if method == "bank_transfer":
        return {**common,
                "instructions": "Contact @osifeu_prog for bank details",
                "memo": f"Include order ref: {order_ref}"}
    if method == "paypal":
        return {**common, "instructions": "Contact @osifeu_prog for PayPal email"}
    return {**common, "instructions": "Contact @osifeu_prog to arrange payment"}

@router.post("/confirm-payment")
async def confirm_payment(req: ConfirmPaymentRequest, x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Admin confirms a payment was received → splits revenue + logs to revenue_ledger."""
    actor = _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        sale = await conn.fetchrow("SELECT * FROM course_sales WHERE order_ref=$1", req.order_ref)
        if not sale: raise HTTPException(404, "Order not found")
        if sale["status"] == "paid": raise HTTPException(400, "Already confirmed")
        if sale["status"] in ("refunded", "cancelled"): raise HTTPException(400, f"Order is {sale['status']}")

        item = await conn.fetchrow("SELECT * FROM course_items WHERE id=$1", sale["item_id"])

        # Determine split
        creator_split = float(item["creator_split_pct"]) if item["creator_split_pct"] is not None else None
        if creator_split is None and item["creator_id"]:
            creator_default = await conn.fetchval(
                "SELECT default_split_pct FROM course_creators WHERE id=$1", item["creator_id"])
            creator_split = float(creator_default) if creator_default else 0.75
        if creator_split is None:
            creator_split = 0.0  # No external creator → 100% to platform

        amount = float(sale["amount_ils"])
        creator_amt = round(amount * creator_split, 2)
        platform_amt = round(amount - creator_amt, 2)

        # Log platform revenue to the revenue_ledger (so it flows to investor distribution)
        period_ym = dt.datetime.utcnow().strftime("%Y-%m")
        revenue_id = None
        try:
            revenue_id = await conn.fetchval("""
                INSERT INTO revenue_ledger (period_ym, source, description, amount_ils, invoice_ref, created_by)
                VALUES ($1, 'course_sale', $2, $3, $4, $5) RETURNING id
            """, period_ym, f"{item['title']} (sale {sale['order_ref']})", platform_amt,
                 sale["order_ref"], actor[-8:])
        except Exception as e:
            # If revenue_ledger doesn't exist yet (investor_engine not initialized), continue without
            print(f"[courses] Could not log to revenue_ledger: {e}")

        await conn.execute("""
            UPDATE course_sales SET status='paid', paid_at=NOW(),
                                    creator_split_ils=$1, platform_split_ils=$2,
                                    revenue_ledger_id=$3, payment_ref=COALESCE($4, payment_ref)
            WHERE id=$5
        """, creator_amt, platform_amt, revenue_id, req.payment_ref, sale["id"])
        await conn.execute("UPDATE course_items SET sales_count = sales_count + 1 WHERE id=$1", sale["item_id"])

    return {
        "ok": True,
        "order_ref": req.order_ref,
        "amount_ils": amount,
        "creator_share_ils": creator_amt,
        "platform_share_ils": platform_amt,
        "creator_split_pct": creator_split,
        "revenue_ledger_id": revenue_id,
        "message": f"Payment confirmed. Creator gets ₪{creator_amt}, platform gets ₪{platform_amt} (logged to {period_ym} revenue).",
    }

@router.get("/sales")
async def list_sales(status: Optional[str] = Query(None), x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    _require_admin(x_admin_key)
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        if status:
            rows = await conn.fetch("""
                SELECT s.*, i.title AS item_title, i.slug FROM course_sales s
                  JOIN course_items i ON i.id = s.item_id
                 WHERE s.status=$1 ORDER BY s.created_at DESC LIMIT 200
            """, status)
        else:
            rows = await conn.fetch("""
                SELECT s.*, i.title AS item_title, i.slug FROM course_sales s
                  JOIN course_items i ON i.id = s.item_id
                 ORDER BY s.created_at DESC LIMIT 200
            """)
    return {"sales": [dict(r) for r in rows]}

@router.get("/my-library")
async def my_library(telegram_id: int = Query(..., gt=0)):
    """Return paid items for a buyer (their library)."""
    if not _pool: raise HTTPException(503, "DB pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_schema(conn)
        rows = await conn.fetch("""
            SELECT s.order_ref, s.amount_ils, s.paid_at,
                   i.id AS item_id, i.slug, i.title, i.kind, i.cover_image_url, i.content_url
              FROM course_sales s
              JOIN course_items i ON i.id = s.item_id
             WHERE s.buyer_telegram_id = $1 AND s.status = 'paid'
             ORDER BY s.paid_at DESC
        """, telegram_id)
    return {"library": [dict(r) for r in rows], "count": len(rows)}
