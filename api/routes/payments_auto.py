"""
SLH Auto-verify Payment Endpoints
==================================
On-chain verification for TON + BSC transfers.
Replaces the manual 24h approve flow with sub-60s automatic verification.

Endpoints:
  POST /api/payment/ton/auto-verify     — verify TON tx, grant premium
  POST /api/payment/bsc/auto-verify     — verify BSC/BNB tx, grant premium
  GET  /api/payment/status/{user_id}    — check user premium + last deposit
  GET  /api/payment/config              — public config (addresses, min amounts)
  POST /api/payment/external/record     — record a 3rd-party fiat payment (Stripe/PayBox/Bit)
  POST /api/payment/receipt              — issue a SLH digital receipt
  GET  /api/payment/geography/summary   — dashboard: payments by country/currency

Added 2026-04-17 morning (ship-all session).
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional

import aiohttp
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/payment", tags=["Payments"])

TON_PAY_ADDRESS = os.getenv("TON_PAY_ADDRESS", "").strip()
BSC_GENESIS_ADDRESS = os.getenv(
    "BSC_GENESIS_ADDRESS", "0xd061de73B06d5E91bfA46b35EfB7B08b16903da4"
).lower()
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "").strip()
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY", "").strip()
PREMIUM_MIN_BNB = float(os.getenv("PREMIUM_MIN_BNB", "0.05"))
PREMIUM_MIN_TON = float(os.getenv("PREMIUM_MIN_TON", "1.5"))
PREMIUM_MIN_ILS = float(os.getenv("PREMIUM_MIN_ILS", "41"))


# Pool is injected by main.py via set_pool()
_pool = None


def set_pool(pool):
    global _pool
    _pool = pool


async def _ensure_payment_tables(conn):
    """Idempotent table setup for external payments + receipts + geo."""
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS external_payments (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            provider TEXT NOT NULL,
            provider_tx_id TEXT UNIQUE,
            amount NUMERIC(18,4) NOT NULL,
            currency TEXT NOT NULL,
            status TEXT DEFAULT 'approved',
            country_code TEXT,
            ip_address TEXT,
            plan_key TEXT DEFAULT 'premium',
            bot_name TEXT DEFAULT 'ecosystem',
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ext_pay_user ON external_payments(user_id);
        CREATE INDEX IF NOT EXISTS idx_ext_pay_provider ON external_payments(provider);
        CREATE INDEX IF NOT EXISTS idx_ext_pay_country ON external_payments(country_code);

        CREATE TABLE IF NOT EXISTS payment_receipts (
            id BIGSERIAL PRIMARY KEY,
            receipt_number TEXT UNIQUE NOT NULL,
            user_id BIGINT NOT NULL,
            source_type TEXT NOT NULL,
            source_id BIGINT,
            amount NUMERIC(18,4) NOT NULL,
            currency TEXT NOT NULL,
            tokens_granted NUMERIC(18,6) DEFAULT 0,
            tokens_currency TEXT DEFAULT 'SLH',
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pdf_url TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_receipt_user ON payment_receipts(user_id);
        """
    )


async def _grant_premium(conn, user_id: int, bot_name: str, tx_hash: str, amount: float, currency: str, plan_key: str) -> dict:
    """Record deposit + flip premium to approved. Idempotent by tx_hash."""
    existing = await conn.fetchval("SELECT id FROM deposits WHERE tx_hash = $1", tx_hash)
    if existing:
        return {"already_processed": True, "deposit_id": existing}

    dep_id = await conn.fetchval(
        """
        INSERT INTO deposits (user_id, amount, currency, tx_hash, status, plan_key)
        VALUES ($1, $2, $3, $4, 'approved', $5) RETURNING id
        """,
        user_id, amount, currency, tx_hash, plan_key,
    )
    await conn.execute(
        """
        INSERT INTO premium_users (user_id, bot_name, payment_status)
        VALUES ($1, $2, 'approved')
        ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'approved'
        """,
        user_id, bot_name,
    )
    return {"deposit_id": dep_id, "already_processed": False}


async def _issue_receipt(conn, user_id: int, source_type: str, source_id: int, amount: float, currency: str, tokens_granted: float = 0, tokens_currency: str = "SLH") -> dict:
    """Emit a digital receipt. receipt_number format: SLH-YYYYMMDD-{id}."""
    today = datetime.utcnow().strftime("%Y%m%d")
    row = await conn.fetchrow(
        """
        INSERT INTO payment_receipts (receipt_number, user_id, source_type, source_id, amount, currency, tokens_granted, tokens_currency)
        VALUES ('SLH-' || $1 || '-TMP-' || FLOOR(RANDOM()*1000000)::TEXT, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id, receipt_number, issued_at
        """,
        today, user_id, source_type, source_id, amount, currency, tokens_granted, tokens_currency,
    )
    final_number = f"SLH-{today}-{row['id']:06d}"
    await conn.execute("UPDATE payment_receipts SET receipt_number = $1 WHERE id = $2", final_number, row["id"])
    return {
        "id": row["id"],
        "receipt_number": final_number,
        "issued_at": row["issued_at"].isoformat(),
    }


def _client_country(request: Request) -> Optional[str]:
    """Extract country code from standard proxy headers (Cloudflare, Railway, etc)."""
    for h in ("cf-ipcountry", "x-vercel-ip-country", "x-country-code"):
        v = request.headers.get(h)
        if v and v != "XX":
            return v.upper()
    return None


def _client_ip(request: Request) -> str:
    for h in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        v = request.headers.get(h)
        if v:
            return v.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============================================================
# TON auto-verify
# ============================================================

class TonVerifyReq(BaseModel):
    user_id: int
    tx_hash: str
    expected_amount_ton: Optional[float] = None
    plan_key: str = "premium"
    bot_name: str = "ecosystem"
    issue_receipt: bool = True


@router.post("/ton/auto-verify")
async def ton_auto_verify(req: TonVerifyReq, request: Request):
    if not TON_PAY_ADDRESS:
        raise HTTPException(503, "TON_PAY_ADDRESS env var not configured")

    tx_hash = (req.tx_hash or "").strip()
    if not tx_hash or len(tx_hash) < 40:
        raise HTTPException(400, "invalid tx_hash")

    expected = req.expected_amount_ton or PREMIUM_MIN_TON
    key_q = f"&api_key={TONCENTER_API_KEY}" if TONCENTER_API_KEY else ""
    url = f"https://toncenter.com/api/v2/getTransactions?address={TON_PAY_ADDRESS}&limit=50{key_q}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise HTTPException(502, f"toncenter returned {resp.status}")
                data = await resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(504, f"toncenter fetch failed: {e}")

    match = None
    for tx in data.get("result", []) or []:
        tid = tx.get("transaction_id", {}) or {}
        if tid.get("hash") == tx_hash:
            match = tx
            break
        in_msg = tx.get("in_msg", {}) or {}
        if in_msg.get("body_hash") == tx_hash or in_msg.get("hash") == tx_hash:
            match = tx
            break

    if not match:
        raise HTTPException(404, "TX not found on TON yet. Wait 30 seconds and retry.")

    in_msg = match.get("in_msg", {}) or {}
    amount_nano = int(in_msg.get("value", 0) or 0)
    amount_ton = amount_nano / 1e9

    if amount_ton < expected * 0.98:
        raise HTTPException(400, f"amount too low: got {amount_ton:.4f} TON, expected {expected} TON")

    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    async with _pool.acquire() as conn:
        await _ensure_payment_tables(conn)
        result = await _grant_premium(conn, req.user_id, req.bot_name, tx_hash, amount_ton, "TON", req.plan_key)
        receipt = None
        if req.issue_receipt and not result.get("already_processed"):
            receipt = await _issue_receipt(conn, req.user_id, "ton_deposit", result.get("deposit_id"), amount_ton, "TON")

    return {
        "ok": True,
        "verified": True,
        "amount_ton": amount_ton,
        "tx_hash": tx_hash,
        "country_code": _client_country(request),
        "receipt": receipt,
        **result,
        "message": "תשלום אומת ב-TON. Premium הופעל.",
    }


# ============================================================
# BSC auto-verify
# ============================================================

class BscVerifyReq(BaseModel):
    user_id: int
    tx_hash: str
    expected_min_bnb: Optional[float] = None
    plan_key: str = "premium"
    bot_name: str = "ecosystem"
    issue_receipt: bool = True


@router.post("/bsc/auto-verify")
async def bsc_auto_verify(req: BscVerifyReq, request: Request):
    tx_hash = (req.tx_hash or "").strip()
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise HTTPException(400, "invalid BSC tx_hash (expected 0x + 64 hex)")

    expected_min = req.expected_min_bnb or PREMIUM_MIN_BNB
    base = "https://api.bscscan.com/api"
    key_suffix = f"&apikey={BSCSCAN_API_KEY}" if BSCSCAN_API_KEY else ""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base}?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}{key_suffix}",
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                tx_data = await resp.json()
            async with session.get(
                f"{base}?module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}{key_suffix}",
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                rc_data = await resp.json()
    except Exception as e:
        raise HTTPException(504, f"bscscan fetch failed: {e}")

    tx = tx_data.get("result")
    receipt_raw = rc_data.get("result")
    if not tx:
        raise HTTPException(404, "TX not found on BSC yet. Wait ~15s and retry.")
    if not receipt_raw:
        raise HTTPException(400, "TX not yet confirmed")
    if receipt_raw.get("status") != "0x1":
        raise HTTPException(400, "TX failed on-chain")

    to_addr = (tx.get("to") or "").lower()
    value_bnb = int(tx.get("value", "0x0"), 16) / 1e18

    if to_addr != BSC_GENESIS_ADDRESS:
        raise HTTPException(400, f"TX was sent to {to_addr}, not to Genesis {BSC_GENESIS_ADDRESS}")

    if value_bnb < expected_min:
        raise HTTPException(400, f"amount too low: got {value_bnb:.6f} BNB, expected >= {expected_min} BNB")

    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    async with _pool.acquire() as conn:
        await _ensure_payment_tables(conn)
        result = await _grant_premium(conn, req.user_id, req.bot_name, tx_hash, value_bnb, "BNB", req.plan_key)
        rcpt = None
        if req.issue_receipt and not result.get("already_processed"):
            rcpt = await _issue_receipt(conn, req.user_id, "bsc_deposit", result.get("deposit_id"), value_bnb, "BNB")

    return {
        "ok": True,
        "verified": True,
        "amount_bnb": value_bnb,
        "tx_hash": tx_hash,
        "country_code": _client_country(request),
        "receipt": rcpt,
        **result,
        "message": "תשלום אומת ב-BSC. Premium הופעל.",
    }


# ============================================================
# External providers (Stripe, PayBox, Bit, PayPal, GrowClub, ICount)
# Record-only — the actual card processing happens on the provider side,
# we just ingest the confirmed webhook/return and grant premium + issue receipt.
# ============================================================

class ExternalPaymentRecord(BaseModel):
    user_id: int
    provider: str
    provider_tx_id: str
    amount: float
    currency: str = "ILS"
    plan_key: str = "premium"
    bot_name: str = "ecosystem"
    country_code: Optional[str] = None
    issue_receipt: bool = True
    grant_premium: bool = True
    metadata: Optional[dict] = None


SUPPORTED_PROVIDERS = {"stripe", "paybox", "bit", "paypal", "growclub", "icount", "isracard", "cardcom", "meshulam", "manual_bank"}


@router.post("/external/record")
async def external_payment_record(req: ExternalPaymentRecord, request: Request):
    provider = req.provider.lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(400, f"unsupported provider '{provider}'. allowed: {sorted(SUPPORTED_PROVIDERS)}")
    if not req.provider_tx_id.strip():
        raise HTTPException(400, "provider_tx_id required")

    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    country = req.country_code or _client_country(request)
    ip = _client_ip(request)

    async with _pool.acquire() as conn:
        await _ensure_payment_tables(conn)

        existing = await conn.fetchval(
            "SELECT id FROM external_payments WHERE provider = $1 AND provider_tx_id = $2",
            provider, req.provider_tx_id,
        )
        if existing:
            return {"ok": True, "already_processed": True, "external_payment_id": existing}

        ext_id = await conn.fetchval(
            """
            INSERT INTO external_payments
                (user_id, provider, provider_tx_id, amount, currency, country_code, ip_address, plan_key, bot_name, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
            RETURNING id
            """,
            req.user_id, provider, req.provider_tx_id, req.amount, req.currency.upper(),
            country, ip, req.plan_key, req.bot_name, json.dumps(req.metadata or {}),
        )

        if req.grant_premium:
            await conn.execute(
                """
                INSERT INTO premium_users (user_id, bot_name, payment_status)
                VALUES ($1, $2, 'approved')
                ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'approved'
                """,
                req.user_id, req.bot_name,
            )

        rcpt = None
        if req.issue_receipt:
            rcpt = await _issue_receipt(conn, req.user_id, f"external_{provider}", ext_id, req.amount, req.currency.upper())

    return {
        "ok": True,
        "external_payment_id": ext_id,
        "provider": provider,
        "country_code": country,
        "receipt": rcpt,
        "message": f"תשלום {provider} נרשם" + (" ו-Premium הופעל" if req.grant_premium else ""),
    }


# ============================================================
# Status + config + geography dashboard
# ============================================================

@router.get("/status/{user_id}")
async def payment_status(user_id: int, bot_name: str = "ecosystem"):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        prem = await conn.fetchrow(
            """
            SELECT payment_status, created_at FROM premium_users
            WHERE user_id = $1 AND bot_name = $2
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id, bot_name,
        )
        last_dep = await conn.fetchrow(
            "SELECT id, amount, currency, tx_hash, status, created_at FROM deposits WHERE user_id = $1 ORDER BY id DESC LIMIT 1",
            user_id,
        )
        last_ext = await conn.fetchrow(
            "SELECT id, provider, amount, currency, status, country_code, created_at FROM external_payments WHERE user_id = $1 ORDER BY id DESC LIMIT 1",
            user_id,
        )
        receipts = await conn.fetch(
            "SELECT id, receipt_number, amount, currency, issued_at FROM payment_receipts WHERE user_id = $1 ORDER BY id DESC LIMIT 10",
            user_id,
        )

    return {
        "user_id": user_id,
        "bot_name": bot_name,
        "has_premium": bool(prem and prem["payment_status"] == "approved"),
        "status": prem["payment_status"] if prem else "none",
        "approved_at": prem["created_at"].isoformat() if prem and prem["created_at"] else None,
        "last_deposit": dict(last_dep) if last_dep else None,
        "last_external": dict(last_ext) if last_ext else None,
        "receipts": [dict(r) for r in receipts],
    }


@router.get("/config")
async def payment_config():
    return {
        "ton_address": TON_PAY_ADDRESS or None,
        "bsc_genesis_address": BSC_GENESIS_ADDRESS,
        "premium_min_bnb": PREMIUM_MIN_BNB,
        "premium_min_ton": PREMIUM_MIN_TON,
        "premium_min_ils": PREMIUM_MIN_ILS,
        "bscscan_configured": bool(BSCSCAN_API_KEY),
        "toncenter_configured": bool(TON_PAY_ADDRESS),
        "supported_providers": sorted(SUPPORTED_PROVIDERS),
    }


@router.get("/geography/summary")
async def payment_geography(x_admin_key: Optional[str] = Header(None)):
    """Admin: breakdown of payments by country + currency + provider."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "slh2026admin").split(",") if k.strip()]
    if x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")

    async with _pool.acquire() as conn:
        by_country = await conn.fetch(
            """
            SELECT COALESCE(country_code, 'UNKNOWN') AS country,
                   COUNT(*) AS count,
                   SUM(amount) AS total_amount,
                   currency
            FROM external_payments GROUP BY country, currency ORDER BY total_amount DESC LIMIT 100
            """
        )
        by_provider = await conn.fetch(
            """
            SELECT provider, COUNT(*) AS count, SUM(amount) AS total_amount, currency
            FROM external_payments GROUP BY provider, currency ORDER BY total_amount DESC
            """
        )
        by_crypto = await conn.fetch(
            """
            SELECT currency, COUNT(*) AS count, SUM(amount) AS total_amount
            FROM deposits WHERE status = 'approved' AND tx_hash IS NOT NULL
            GROUP BY currency ORDER BY total_amount DESC
            """
        )
        totals = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM external_payments) AS external_count,
                (SELECT COUNT(*) FROM deposits WHERE status='approved' AND tx_hash IS NOT NULL) AS crypto_count,
                (SELECT COUNT(*) FROM payment_receipts) AS receipts_count,
                (SELECT COUNT(*) FROM premium_users WHERE payment_status='approved') AS premium_active
            """
        )

    return {
        "totals": dict(totals) if totals else {},
        "by_country": [dict(r) for r in by_country],
        "by_provider": [dict(r) for r in by_provider],
        "by_crypto": [dict(r) for r in by_crypto],
    }


@router.get("/receipts/{user_id}")
async def user_receipts(user_id: int, limit: int = 50):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, receipt_number, source_type, source_id, amount, currency,
                   tokens_granted, tokens_currency, issued_at, metadata
            FROM payment_receipts WHERE user_id = $1
            ORDER BY id DESC LIMIT $2
            """,
            user_id, max(1, min(limit, 500)),
        )
    return {"user_id": user_id, "receipts": [dict(r) for r in rows]}
