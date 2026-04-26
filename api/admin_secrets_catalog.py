"""SLH Secrets Vault — unified inventory of every credential the system uses.

The system has 12+ different secret types scattered across:
  - Railway env vars (ADMIN_API_KEYS, JWT_SECRET, ENCRYPTION_KEY, AI provider keys, etc.)
  - Local .env files (per-bot tokens, ANTHROPIC_API_KEY)
  - localStorage (admin login cache)
  - External dashboards (BotFather, Anthropic console, BSCScan, Inforu)

This module provides a single source of truth for METADATA only — names, where
they live, rotation URLs, last-rotated timestamps, status. The actual secret
values NEVER touch this DB or this API. We only know about them, not their
contents.

Design mirrors api/admin_bots_catalog.py — same fail-safe import pattern,
same CRUD shape, same X-Admin-Key gating.

Endpoints (all under /api/admin/secrets, X-Admin-Key gated):
    GET    /api/admin/secrets                — list (filter by category/status)
    POST   /api/admin/secrets                — add new entry to vault
    PATCH  /api/admin/secrets/{id}           — edit
    DELETE /api/admin/secrets/{id}           — remove
    POST   /api/admin/secrets/{id}/mark-rotated  — record rotation timestamp
    POST   /api/admin/secrets/{id}/check-health  — best-effort probe (where possible)
    GET    /api/admin/secrets/stats          — counts by category + staleness
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

log = logging.getLogger("slh.secrets_vault")

router = APIRouter(prefix="/api/admin/secrets", tags=["admin", "secrets"])


# ─── Models ────────────────────────────────────────────────────────────────


class SecretIn(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=80)
    display_name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., pattern=r"^(admin|api_key|ai_provider|external|database|bot|other)$")
    storage_location: str = Field(..., pattern=r"^(railway_env|local_env|localstorage|external|hardware|github)$")
    rotation_url: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=300)
    rotation_cadence_days: Optional[int] = Field(90, ge=1, le=730)
    notes: Optional[str] = Field(None, max_length=400)
    status: Optional[str] = Field("unknown", pattern=r"^(configured|default|missing|unknown|deprecated)$")


class SecretUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=120)
    category: Optional[str] = Field(None, pattern=r"^(admin|api_key|ai_provider|external|database|bot|other)$")
    storage_location: Optional[str] = Field(None, pattern=r"^(railway_env|local_env|localstorage|external|hardware|github)$")
    rotation_url: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=300)
    rotation_cadence_days: Optional[int] = Field(None, ge=1, le=730)
    notes: Optional[str] = Field(None, max_length=400)
    status: Optional[str] = Field(None, pattern=r"^(configured|default|missing|unknown|deprecated)$")


# ─── Auth (reuses canonical _require_admin from main when available) ───────


def _admin(authorization: Optional[str], x_admin_key: Optional[str]) -> int:
    try:
        from main import _require_admin
        return _require_admin(authorization, x_admin_key)
    except Exception:
        env_keys = {k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()}
        if x_admin_key and x_admin_key in env_keys:
            return 0
        raise HTTPException(403, "Admin authentication required")


# ─── Schema + initial seed ──────────────────────────────────────────────────


_SCHEMA_READY = False


# Initial seed — the 12 secret types we know about as of 2026-04-25.
# Status is computed at runtime by inspecting the actual env: configured (set),
# default (matches a known placeholder), missing (env var empty), unknown
# (we can't determine without more context).
_INITIAL_SEED = [
    # --- Admin auth ---
    {
        "key_name": "ADMIN_API_KEYS",
        "display_name": "Admin API Keys",
        "category": "admin",
        "storage_location": "railway_env",
        "rotation_url": "https://railway.com/project/slh-api/service/api?settings=variables",
        "description": "Comma-separated list of valid X-Admin-Key headers. Every /api/admin/* endpoint validates against this.",
        "rotation_cadence_days": 90,
    },
    {
        "key_name": "ADMIN_BROADCAST_KEY",
        "display_name": "Broadcast Admin Key",
        "category": "admin",
        "storage_location": "railway_env",
        "rotation_url": "https://railway.com/project/slh-api/service/api?settings=variables",
        "description": "Separate auth for /api/broadcast/send and /api/ops/* endpoints.",
        "rotation_cadence_days": 90,
        "notes": "If still 'slh-broadcast-2026-change-me' — that's the default placeholder. Rotate it.",
    },
    {
        "key_name": "JWT_SECRET",
        "display_name": "JWT Signing Secret",
        "category": "admin",
        "storage_location": "railway_env",
        "rotation_url": "https://railway.com/project/slh-api/service/api?settings=variables",
        "description": "HMAC secret for signing user session JWTs. Rotation invalidates all active sessions.",
        "rotation_cadence_days": 365,
    },
    {
        "key_name": "ENCRYPTION_KEY",
        "display_name": "AES-GCM Encryption Key",
        "category": "admin",
        "storage_location": "railway_env",
        "rotation_url": "https://railway.com/project/slh-api/service/api?settings=variables",
        "description": "AES-GCM key for encrypting CEX API keys at rest. Rotation requires re-encrypting existing rows.",
        "rotation_cadence_days": 365,
        "notes": "CRITICAL — losing this key locks out access to encrypted CEX keys.",
    },

    # --- AI providers ---
    {
        "key_name": "ANTHROPIC_API_KEY",
        "display_name": "Anthropic Claude API",
        "category": "ai_provider",
        "storage_location": "local_env",
        "rotation_url": "https://console.anthropic.com/settings/keys",
        "description": "Claude API key for @SLH_Claude_bot anthropic-tools mode. Lives in slh-claude-bot/.env locally.",
        "rotation_cadence_days": 180,
    },
    {
        "key_name": "OPENAI_API_KEY",
        "display_name": "OpenAI GPT API",
        "category": "ai_provider",
        "storage_location": "railway_env",
        "rotation_url": "https://platform.openai.com/api-keys",
        "description": "GPT-4 fallback in /api/ai/chat router.",
        "rotation_cadence_days": 180,
    },
    {
        "key_name": "GEMINI_API_KEY",
        "display_name": "Google Gemini API",
        "category": "ai_provider",
        "storage_location": "railway_env",
        "rotation_url": "https://aistudio.google.com/apikey",
        "description": "Gemini 1.5 Pro for free-tier AI in /api/ai/chat.",
        "rotation_cadence_days": 180,
    },
    {
        "key_name": "GROQ_API_KEY",
        "display_name": "Groq Llama API",
        "category": "ai_provider",
        "storage_location": "railway_env",
        "rotation_url": "https://console.groq.com/keys",
        "description": "Free fallback for /api/ai/chat — Llama 3.3 70B at ~500 tokens/sec.",
        "rotation_cadence_days": 180,
    },

    # --- External services ---
    {
        "key_name": "BSCSCAN_API_KEY",
        "display_name": "BSCScan Explorer API",
        "category": "external",
        "storage_location": "railway_env",
        "rotation_url": "https://bscscan.com/myapikey",
        "description": "Used by /api/network/slh-holders + chain-status.html for on-chain SLH balances.",
        "rotation_cadence_days": 365,
    },
    {
        "key_name": "INFORU_API_TOKEN",
        "display_name": "Inforu SMS Provider",
        "category": "external",
        "storage_location": "railway_env",
        "rotation_url": "https://capi.inforu.co.il",
        "description": "Israeli SMS provider for /api/device/register OTPs. Pair with INFORU_USERNAME + INFORU_SENDER.",
        "rotation_cadence_days": 365,
    },
    {
        "key_name": "TWILIO_AUTH_TOKEN",
        "display_name": "Twilio SMS (alt)",
        "category": "external",
        "storage_location": "railway_env",
        "rotation_url": "https://console.twilio.com/account/keys-credentials",
        "description": "Alternative SMS provider — global, more expensive. Pair with TWILIO_ACCOUNT_SID + TWILIO_FROM.",
        "rotation_cadence_days": 365,
        "status": "missing",  # we know Twilio is not configured today
    },

    # --- Database ---
    {
        "key_name": "DATABASE_URL",
        "display_name": "Postgres Connection",
        "category": "database",
        "storage_location": "railway_env",
        "rotation_url": "https://railway.com/project/slh-api/service/postgres?settings=variables",
        "description": "Auto-managed by Railway Postgres. Rotation = Railway 'Rotate Password' button.",
        "rotation_cadence_days": 365,
    },
]


def _detect_status(key_name: str, declared_status: Optional[str]) -> str:
    """Best-effort status detection from local env. Runs only on seed/refresh.

    Note: we only see Railway env vars if THIS process IS running on Railway.
    From a local machine the seed will mostly say 'unknown'. That's intentional —
    the secrets vault is informational, not authoritative.
    """
    if declared_status and declared_status != "unknown":
        return declared_status
    val = os.getenv(key_name)
    if not val:
        return "missing"
    # Check for known default placeholders
    defaults = {
        "ADMIN_API_KEYS": ("slh_admin_2026", "slh2026admin"),
        "ADMIN_BROADCAST_KEY": ("slh-broadcast-2026-change-me",),
        "ADMIN_API_KEY": ("slh_admin_2026",),
        "ENCRYPTION_KEY": ("slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026",),
    }
    placeholders = defaults.get(key_name, ())
    if any(p in val for p in placeholders):
        return "default"
    return "configured"


async def _ensure_schema(pool) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secrets_catalog (
                id              BIGSERIAL PRIMARY KEY,
                key_name        TEXT NOT NULL UNIQUE,
                display_name    TEXT NOT NULL,
                category        TEXT NOT NULL,
                storage_location TEXT NOT NULL,
                rotation_url    TEXT,
                description     TEXT,
                status          TEXT NOT NULL DEFAULT 'unknown',
                rotation_cadence_days INT NOT NULL DEFAULT 90,
                last_rotated_at TIMESTAMPTZ,
                last_verified_at TIMESTAMPTZ,
                last_health_check_at TIMESTAMPTZ,
                last_health_result TEXT,
                notes           TEXT,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_secrets_category ON secrets_catalog (category)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_secrets_status ON secrets_catalog (status)"
        )
        # ── Phase 2: alerts schema (additive, idempotent) ─────────────────────
        # Adds cooldown + alert tracking columns + secret_alerts table for
        # the scheduled health sweep and Telegram digest.
        await conn.execute(
            "ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS last_alert_at TIMESTAMPTZ"
        )
        await conn.execute(
            "ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS last_alert_result TEXT"
        )
        await conn.execute(
            "ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS alert_cooldown_hours INT NOT NULL DEFAULT 24"
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secret_alerts (
                id          BIGSERIAL PRIMARY KEY,
                secret_id   BIGINT REFERENCES secrets_catalog(id) ON DELETE CASCADE,
                alert_type  TEXT NOT NULL,
                prev_status TEXT,
                new_status  TEXT,
                detail      TEXT,
                notified_via TEXT,
                fired_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_secret_alerts_fired ON secret_alerts (fired_at DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_secret_alerts_secret ON secret_alerts (secret_id)"
        )
        # Seed if empty
        existing = await conn.fetchval("SELECT COUNT(*) FROM secrets_catalog")
        if (existing or 0) == 0:
            for s in _INITIAL_SEED:
                detected = _detect_status(s["key_name"], s.get("status"))
                try:
                    await conn.execute(
                        """
                        INSERT INTO secrets_catalog
                            (key_name, display_name, category, storage_location,
                             rotation_url, description, status, rotation_cadence_days, notes)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (key_name) DO NOTHING
                        """,
                        s["key_name"], s["display_name"], s["category"], s["storage_location"],
                        s.get("rotation_url"), s.get("description"), detected,
                        s.get("rotation_cadence_days", 90), s.get("notes"),
                    )
                except Exception as e:
                    log.warning("seed failed for %s: %s", s.get("key_name"), e)
            log.info("secrets_catalog seeded with %d initial rows", len(_INITIAL_SEED))
    _SCHEMA_READY = True


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


def _row_to_dict(r) -> dict:
    return {
        "id": r["id"],
        "key_name": r["key_name"],
        "display_name": r["display_name"],
        "category": r["category"],
        "storage_location": r["storage_location"],
        "rotation_url": r["rotation_url"],
        "description": r["description"],
        "status": r["status"],
        "rotation_cadence_days": r["rotation_cadence_days"],
        "last_rotated_at": r["last_rotated_at"].isoformat() if r["last_rotated_at"] else None,
        "last_verified_at": r["last_verified_at"].isoformat() if r["last_verified_at"] else None,
        "last_health_check_at": r["last_health_check_at"].isoformat() if r["last_health_check_at"] else None,
        "last_health_result": r["last_health_result"],
        "notes": r["notes"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────


@router.get("")
async def list_secrets(
    request: Request,
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        # Refresh status for entries we can detect (run-time check on Railway)
        rows = await conn.fetch("SELECT * FROM secrets_catalog ORDER BY category, display_name")
        # Refresh status of each row (best-effort) — only if status is 'unknown' or stale
        for r in rows:
            current_status = _detect_status(r["key_name"], None)
            if current_status != r["status"] and current_status != "unknown":
                await conn.execute(
                    "UPDATE secrets_catalog SET status = $1, updated_at = NOW() WHERE id = $2",
                    current_status, r["id"],
                )
        # Re-fetch with updated statuses
        if category and status:
            rows = await conn.fetch(
                "SELECT * FROM secrets_catalog WHERE category = $1 AND status = $2 ORDER BY display_name",
                category, status,
            )
        elif category:
            rows = await conn.fetch(
                "SELECT * FROM secrets_catalog WHERE category = $1 ORDER BY display_name",
                category,
            )
        elif status:
            rows = await conn.fetch(
                "SELECT * FROM secrets_catalog WHERE status = $1 ORDER BY display_name",
                status,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM secrets_catalog ORDER BY category, display_name"
            )
    return {"count": len(rows), "secrets": [_row_to_dict(r) for r in rows]}


@router.post("")
async def add_secret(
    body: SecretIn,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO secrets_catalog
                    (key_name, display_name, category, storage_location, rotation_url,
                     description, status, rotation_cadence_days, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                body.key_name, body.display_name, body.category, body.storage_location,
                body.rotation_url, body.description, body.status or "unknown",
                body.rotation_cadence_days or 90, body.notes,
            )
        except Exception as e:
            if "unique" in str(e).lower():
                raise HTTPException(409, f"secret with key_name {body.key_name} already exists")
            raise HTTPException(500, f"insert failed: {e}")
    return {"ok": True, "secret": _row_to_dict(row)}


@router.patch("/{secret_id}")
async def update_secret(
    secret_id: int,
    body: SecretUpdate,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    fields = []
    values = []
    for k in ("display_name", "category", "storage_location", "rotation_url",
              "description", "status", "rotation_cadence_days", "notes"):
        v = getattr(body, k)
        if v is not None:
            fields.append(f"{k} = ${len(values) + 1}")
            values.append(v)
    if not fields:
        raise HTTPException(400, "nothing to update")
    fields.append("updated_at = NOW()")
    values.append(secret_id)
    sql = f"UPDATE secrets_catalog SET {', '.join(fields)} WHERE id = ${len(values)} RETURNING *"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)
    if not row:
        raise HTTPException(404, "secret not found")
    return {"ok": True, "secret": _row_to_dict(row)}


@router.delete("/{secret_id}")
async def delete_secret(
    secret_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM secrets_catalog WHERE id = $1", secret_id)
    if result.endswith("DELETE 0"):
        raise HTTPException(404, "secret not found")
    return {"ok": True}


@router.post("/{secret_id}/mark-rotated")
async def mark_rotated(
    secret_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Record that this secret was rotated NOW. Audit trail to event_log."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE secrets_catalog
               SET last_rotated_at = NOW(),
                   status = 'configured',
                   updated_at = NOW()
             WHERE id = $1
             RETURNING *
            """,
            secret_id,
        )
    if not row:
        raise HTTPException(404, "secret not found")

    # Audit trail
    try:
        from shared.events import emit as _emit
        await _emit(
            pool,
            "admin.secret_rotated",
            {"secret_id": secret_id, "key_name": row["key_name"], "category": row["category"]},
            source="api.admin.secrets_vault",
        )
    except Exception:
        pass

    return {"ok": True, "secret": _row_to_dict(row)}


async def _run_probe(key_name: str) -> tuple[str, Optional[str]]:
    """Probe the actual provider to verify the secret currently works.

    Reads the secret from THIS process's env vars (never from DB / never
    accepts as argument), issues a no-op API call, and returns a status
    tuple. The secret value itself never leaves this process.

    Result codes (small closed set so callers can branch reliably):
        ok            — provider accepted the key
        bad_key       — provider rejected the key (401/403)
        missing       — env var is not set on this process
        service_error — provider returned 5xx
        unknown       — provider returned something we couldn't classify
        skipped       — no probe implemented for this key_name
        error         — exception while probing (network etc)

    Reused by /check-health (single-secret) and /sweep (batch). Pure HTTP,
    no DB access — sweep handles persistence + alerts on top.
    """
    result: str = "skipped"
    detail: Optional[str] = None

    try:
        if key_name == "ANTHROPIC_API_KEY":
            tok = os.getenv("ANTHROPIC_API_KEY")
            if not tok:
                result, detail = "missing", "env var not set on this process"
            else:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    r = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": tok,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={"model": "claude-haiku-4-5", "max_tokens": 1, "messages": [{"role": "user", "content": "x"}]},
                    )
                # 401 = bad key; 200 = ok; 4xx other = key valid but request bad (still ok auth-wise)
                if r.status_code == 401:
                    result, detail = "bad_key", "401 Unauthorized"
                elif r.status_code < 500:
                    result, detail = "ok", f"HTTP {r.status_code}"
                else:
                    result, detail = "service_error", f"HTTP {r.status_code}"
        elif key_name == "OPENAI_API_KEY":
            tok = os.getenv("OPENAI_API_KEY")
            if not tok:
                result, detail = "missing", "env var not set"
            else:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    r = await client.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {tok}"})
                if r.status_code == 401:
                    result, detail = "bad_key", "401"
                elif r.status_code < 400:
                    result, detail = "ok", f"HTTP {r.status_code}"
                else:
                    result, detail = "service_error", f"HTTP {r.status_code}"
        elif key_name == "GROQ_API_KEY":
            tok = os.getenv("GROQ_API_KEY")
            if not tok:
                result, detail = "missing", "env var not set"
            else:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    r = await client.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {tok}"})
                if r.status_code == 401:
                    result, detail = "bad_key", "401"
                elif r.status_code < 400:
                    result, detail = "ok", f"HTTP {r.status_code}"
                else:
                    result, detail = "service_error", f"HTTP {r.status_code}"
        elif key_name == "GEMINI_API_KEY":
            tok = os.getenv("GEMINI_API_KEY")
            if not tok:
                result, detail = "missing", "env var not set"
            else:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    r = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={tok}")
                if r.status_code == 403 or r.status_code == 400:
                    result, detail = "bad_key", str(r.status_code)
                elif r.status_code < 400:
                    result, detail = "ok", f"HTTP {r.status_code}"
                else:
                    result, detail = "service_error", f"HTTP {r.status_code}"
        elif key_name == "BSCSCAN_API_KEY":
            tok = os.getenv("BSCSCAN_API_KEY")
            if not tok:
                result, detail = "missing", "env var not set"
            else:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    r = await client.get(f"https://api.bscscan.com/api?module=stats&action=ethsupply&apikey={tok}")
                j = r.json() if r.status_code == 200 else {}
                if j.get("status") == "1":
                    result, detail = "ok", "200"
                elif "Invalid API Key" in str(j):
                    result, detail = "bad_key", "invalid"
                else:
                    result, detail = "unknown", str(j)[:100]
        else:
            # No probe defined for this secret type — that's fine, mark skipped.
            result, detail = "skipped", "no probe implemented"
    except Exception as e:
        result, detail = "error", f"{type(e).__name__}: {e}"

    return result, detail


@router.post("/{secret_id}/check-health")
async def check_health(
    secret_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Best-effort health probe — try to actually use the secret to verify it works.

    For each provider we know, attempts a no-op API call (free / lightweight)
    and reports whether the credential is currently accepted. The ACTUAL secret
    value never leaves the server (it's read from env, used in the request,
    and the response is parsed but never stored).

    Probe logic lives in `_run_probe(key_name)` so the scheduled sweep
    (api/admin_secret_alerts.py) can reuse the same code path.
    """
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM secrets_catalog WHERE id = $1", secret_id)
    if not row:
        raise HTTPException(404, "secret not found")

    result, detail = await _run_probe(row["key_name"])

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE secrets_catalog
               SET last_health_check_at = NOW(),
                   last_health_result = $2,
                   last_verified_at = CASE WHEN $2 = 'ok' THEN NOW() ELSE last_verified_at END
             WHERE id = $1
            """,
            secret_id, result,
        )
    return {"ok": result == "ok", "result": result, "detail": detail}


@router.get("/stats")
async def stats(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        s = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                                                  AS total,
                COUNT(*) FILTER (WHERE status = 'configured')                             AS configured,
                COUNT(*) FILTER (WHERE status = 'default')                                AS using_defaults,
                COUNT(*) FILTER (WHERE status = 'missing')                                AS missing,
                COUNT(*) FILTER (WHERE status = 'unknown')                                AS unknown,
                COUNT(*) FILTER (WHERE last_rotated_at IS NULL)                           AS never_rotated,
                COUNT(*) FILTER (
                    WHERE last_rotated_at IS NOT NULL
                      AND last_rotated_at < (NOW() - (rotation_cadence_days || ' days')::interval)
                )                                                                         AS overdue,
                COUNT(DISTINCT category)                                                  AS categories
            FROM secrets_catalog
            """
        )
    return {
        "total": int(s["total"] or 0),
        "configured": int(s["configured"] or 0),
        "using_defaults": int(s["using_defaults"] or 0),
        "missing": int(s["missing"] or 0),
        "unknown": int(s["unknown"] or 0),
        "never_rotated": int(s["never_rotated"] or 0),
        "overdue": int(s["overdue"] or 0),
        "categories": int(s["categories"] or 0),
    }
