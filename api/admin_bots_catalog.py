"""SLH Bot Catalog — persistent management of the 25+ Telegram bots in the fleet.

Replaces the hardcoded `BOTS = [...]` array previously duplicated in
website/admin/tokens.html and website/admin/rotate-token.html with a real DB
table + 6 endpoints. Tokens themselves are NOT stored here (only metadata:
name / handle / env_var / service / last_rotated / status / notes).

Schema is created on first hit. On startup, we ALSO seed the catalog with the
known 31 bots if the table is empty so existing UIs keep working without
manual import.

All endpoints under /api/admin/bots are X-Admin-Key gated.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query, Request
from pydantic import BaseModel, Field

log = logging.getLogger("slh.bots_catalog")

router = APIRouter(prefix="/api/admin/bots", tags=["admin", "bots"])


# ─── Models ────────────────────────────────────────────────────────────────


class BotIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    handle: str = Field(..., min_length=2, max_length=64)  # @SLH_xxx_bot
    env_var: str = Field(..., min_length=1, max_length=64)  # XXX_BOT_TOKEN
    service: Optional[str] = Field(None, max_length=64)  # slh-xxx (docker-compose service)
    notes: Optional[str] = Field(None, max_length=400)
    status: Optional[str] = Field("active", pattern=r"^(active|paused|deprecated|swap-target)$")
    tier: Optional[str] = Field("medium", pattern=r"^(critical|high|medium|low)$")


class BotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    handle: Optional[str] = Field(None, min_length=2, max_length=64)
    env_var: Optional[str] = Field(None, min_length=1, max_length=64)
    service: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = Field(None, max_length=400)
    status: Optional[str] = Field(None, pattern=r"^(active|paused|deprecated|swap-target)$")
    tier: Optional[str] = Field(None, pattern=r"^(critical|high|medium|low)$")


class MarkRotated(BaseModel):
    bot_id: Optional[int] = None  # Telegram bot id, NOT the token


# ─── Auth (reuses main.py canonical _require_admin if available) ───────────


def _admin(authorization: Optional[str], x_admin_key: Optional[str]) -> int:
    try:
        from main import _require_admin
        return _require_admin(authorization, x_admin_key)
    except Exception:
        env_keys = {k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()}
        if x_admin_key and x_admin_key in env_keys:
            return 0
        raise HTTPException(403, "Admin authentication required")


# ─── Schema bootstrap + seed ────────────────────────────────────────────────


_SCHEMA_READY = False


# Initial catalog — mirrors the hardcoded list previously embedded in HTML.
# Used ONLY on first run when the table is empty. After that the DB is canonical.
_INITIAL_SEED = [
    {"name": "SLH Core Bot",       "handle": "@SLH_Spark_bot",       "env_var": "CORE_BOT_TOKEN",       "service": "slh-core-bot"},
    {"name": "Guardian",           "handle": "@Grdian_bot",          "env_var": "GUARDIAN_BOT_TOKEN",   "service": "slh-guardian-bot", "notes": "rotated per memory K-25"},
    {"name": "BotShop",            "handle": "@SLH_BotShop_bot",     "env_var": "BOTSHOP_BOT_TOKEN",    "service": "slh-botshop"},
    {"name": "Wallet",             "handle": "@SLH_Wallet_bot",      "env_var": "WALLET_BOT_TOKEN",     "service": "slh-wallet"},
    {"name": "Factory",            "handle": "@SLH_Factory_bot",     "env_var": "FACTORY_BOT_TOKEN",    "service": "slh-factory"},
    {"name": "Fun / Game",         "handle": "@SLH_Fun_bot",         "env_var": "FUN_BOT_TOKEN",        "service": "slh-fun"},
    {"name": "Admin",              "handle": "@SLH_Admin_bot",       "env_var": "ADMIN_BOT_TOKEN",      "service": "slh-admin"},
    {"name": "Airdrop",            "handle": "@SLH_Airdrop_bot",     "env_var": "AIRDROP_BOT_TOKEN",    "service": "slh-airdrop"},
    {"name": "Campaign",           "handle": "@SLH_Campaign_bot",    "env_var": "CAMPAIGN_TOKEN",       "service": "slh-campaign"},
    {"name": "Game Bot",           "handle": "@SLH_Game_bot",        "env_var": "GAME_BOT_TOKEN",       "service": "slh-game"},
    {"name": "TON-MNH",            "handle": "@TonMNH_bot",          "env_var": "TON_MNH_TOKEN",        "service": "slh-ton-mnh"},
    {"name": "SLH TON",            "handle": "@SLH_Ton_bot",         "env_var": "SLH_TON_TOKEN",        "service": "slh-ton"},
    {"name": "Ledger",             "handle": "@SLH_Ledger_bot",      "env_var": "SLH_LEDGER_TOKEN",     "service": "slh-ledger", "notes": "K-8 crash loop"},
    {"name": "Osif Shop",          "handle": "@osif_shop_bot",       "env_var": "OSIF_SHOP_TOKEN",      "service": "slh-osif-shop"},
    {"name": "Nifti Publisher",    "handle": "@Nifti_Publisher_bot", "env_var": "NIFTI_PUBLISHER_TOKEN","service": "slh-nifti"},
    {"name": "Chance Pais",        "handle": "@Chance_Pais_bot",     "env_var": "CHANCE_PAIS_TOKEN",    "service": "slh-chance"},
    {"name": "NFTY Madness",       "handle": "@NFTY_Madness_bot",    "env_var": "NFTY_MADNESS_TOKEN",   "service": "slh-nfty"},
    {"name": "TS Set",             "handle": "@TS_Set_bot",          "env_var": "TS_SET_TOKEN",         "service": "slh-ts-set"},
    {"name": "Crazy Panel",        "handle": "@Crazy_Panel_bot",     "env_var": "CRAZY_PANEL_TOKEN",    "service": "slh-crazy-panel"},
    {"name": "My NFT Shop",        "handle": "@MyNFTShop_bot",       "env_var": "MY_NFT_SHOP_TOKEN",    "service": "slh-nft-shop"},
    {"name": "Beynonibank",        "handle": "@Beynonibank_bot",     "env_var": "BEYNONIBANK_TOKEN",    "service": "slh-beynonibank"},
    {"name": "Test",               "handle": "@SLH_Test_bot",        "env_var": "TEST_BOT_TOKEN",       "service": "slh-test-bot", "status": "swap-target"},
    {"name": "Academia",           "handle": "@WEWORK_teamviwer_bot","env_var": "ACADEMIA_BOT_TOKEN",   "service": "slh-academia-bot"},
    {"name": "ExpertNet",          "handle": "@ExpertNet_bot",       "env_var": "EXPERTNET_BOT_TOKEN",  "service": "slh-expertnet", "notes": "K-25 shares ID with SLH_AIR"},
    {"name": "SLH Air",            "handle": "@SLH_AIR_bot",         "env_var": "SLH_AIR_TOKEN",        "service": "slh-air", "notes": "K-25 shares ID with EXPERTNET"},
    {"name": "Match",              "handle": "@SLH_Match_bot",       "env_var": "MATCH_BOT_TOKEN",      "service": "slh-match", "status": "swap-target"},
    {"name": "Wellness",           "handle": "@SLH_Wellness_bot",    "env_var": "WELLNESS_BOT_TOKEN",   "service": "slh-wellness", "status": "swap-target"},
    {"name": "User Info",          "handle": "@SLH_UserInfo_bot",    "env_var": "USERINFO_BOT_TOKEN",   "service": "slh-userinfo", "status": "swap-target"},
    {"name": "Claude Executor",    "handle": "@SLH_Claude_bot",      "env_var": "SLH_CLAUDE_BOT_TOKEN", "service": "slh-claude-bot"},
    {"name": "G4me Bot",           "handle": "@G4meb0t_bot",         "env_var": "G4ME_BOT_TOKEN",       "service": "slh-g4me", "notes": "DATING bot — separate group"},
    {"name": "Macro (SLH.co.il)",  "handle": "@SLH_macro_bot",       "env_var": "TELEGRAM_BOT_TOKEN",   "service": "n/a", "status": "deprecated", "notes": "Separate project D:\\SLH.co.il"},
]


async def _ensure_schema(pool) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_catalog (
                id              BIGSERIAL PRIMARY KEY,
                name            TEXT NOT NULL,
                handle          TEXT NOT NULL UNIQUE,
                env_var         TEXT NOT NULL,
                service         TEXT,
                telegram_bot_id BIGINT,
                last_rotated_at TIMESTAMPTZ,
                last_verified_at TIMESTAMPTZ,
                status          TEXT NOT NULL DEFAULT 'active',
                tier            TEXT NOT NULL DEFAULT 'medium',
                notes           TEXT,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        # Migration for pre-tier rows: add column if missing, then enforce check.
        await conn.execute(
            "ALTER TABLE bot_catalog ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'medium'"
        )
        # CHECK constraint added separately so the migration is idempotent on
        # existing tables that already have the column without a check.
        await conn.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'bot_catalog_tier_chk'
                ) THEN
                    ALTER TABLE bot_catalog
                    ADD CONSTRAINT bot_catalog_tier_chk
                    CHECK (tier IN ('critical', 'high', 'medium', 'low'));
                END IF;
            END $$;
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_bot_catalog_status ON bot_catalog (status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_bot_catalog_tier ON bot_catalog (tier)"
        )
        # Tier seeds — idempotent: only annotates rows whose tier is still the
        # default 'medium', so manual edits via PATCH are preserved.
        await conn.execute(
            """
            UPDATE bot_catalog SET tier = 'critical'
            WHERE tier = 'medium' AND handle IN
                ('@SLH_Claude_bot', '@WEWORK_teamviwer_bot')
            """
        )
        await conn.execute(
            """
            UPDATE bot_catalog SET tier = 'high'
            WHERE tier = 'medium' AND handle IN
                ('@SLH_BotShop_bot', '@SLH_Wallet_bot', '@SLH_Spark_bot',
                 '@SLH_Admin_bot', '@SLH_macro_bot')
            """
        )
        await conn.execute(
            """
            UPDATE bot_catalog SET tier = 'low'
            WHERE tier = 'medium' AND
                (handle = '@SLH_Test_bot' OR status = 'swap-target')
            """
        )
        # Seed if empty — preserves the existing fleet definition without
        # forcing the operator to re-enter 31 rows.
        existing = await conn.fetchval("SELECT COUNT(*) FROM bot_catalog")
        if (existing or 0) == 0:
            for b in _INITIAL_SEED:
                try:
                    await conn.execute(
                        """
                        INSERT INTO bot_catalog (name, handle, env_var, service, status, notes)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (handle) DO NOTHING
                        """,
                        b["name"], b["handle"], b["env_var"], b.get("service"),
                        b.get("status", "active"), b.get("notes"),
                    )
                except Exception as e:
                    log.warning("seed failed for %s: %s", b.get("handle"), e)
            log.info("bot_catalog seeded with %d initial rows", len(_INITIAL_SEED))
    _SCHEMA_READY = True


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


def _row_to_dict(r) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "handle": r["handle"],
        "env_var": r["env_var"],
        "service": r["service"],
        "telegram_bot_id": r["telegram_bot_id"],
        "last_rotated_at": r["last_rotated_at"].isoformat() if r["last_rotated_at"] else None,
        "last_verified_at": r["last_verified_at"].isoformat() if r["last_verified_at"] else None,
        "status": r["status"],
        "tier": r["tier"] if "tier" in r else "medium",
        "notes": r["notes"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────


@router.get("")
async def list_bots(
    request: Request,
    status: Optional[str] = Query(None, pattern=r"^(active|paused|deprecated|swap-target)$"),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """List all bots in the catalog. Admin-gated (mirrors the page that uses it)."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM bot_catalog WHERE status = $1 ORDER BY name", status
            )
        else:
            rows = await conn.fetch("SELECT * FROM bot_catalog ORDER BY name")
    return {"count": len(rows), "bots": [_row_to_dict(r) for r in rows]}


@router.post("")
async def add_bot(
    body: BotIn,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Add a new bot to the catalog. Token is NOT stored — only metadata."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    handle = body.handle if body.handle.startswith("@") else "@" + body.handle
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO bot_catalog (name, handle, env_var, service, status, tier, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                body.name, handle, body.env_var, body.service,
                body.status or "active", body.tier or "medium", body.notes,
            )
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise HTTPException(409, f"bot with handle {handle} already exists")
            raise HTTPException(500, f"insert failed: {e}")
    return {"ok": True, "bot": _row_to_dict(row)}


@router.patch("/{bot_id}")
async def update_bot(
    bot_id: int,
    body: BotUpdate,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Edit name / handle / env_var / service / notes / status."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    fields = []
    values = []
    for k in ("name", "handle", "env_var", "service", "notes", "status", "tier"):
        v = getattr(body, k)
        if v is not None:
            if k == "handle" and not v.startswith("@"):
                v = "@" + v
            fields.append(f"{k} = ${len(values) + 1}")
            values.append(v)
    if not fields:
        raise HTTPException(400, "nothing to update")

    fields.append(f"updated_at = NOW()")
    values.append(bot_id)
    sql = f"UPDATE bot_catalog SET {', '.join(fields)} WHERE id = ${len(values)} RETURNING *"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)
    if not row:
        raise HTTPException(404, "bot not found")
    return {"ok": True, "bot": _row_to_dict(row)}


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Remove a bot from the catalog (does not touch .env or BotFather)."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM bot_catalog WHERE id = $1", bot_id)
    if result.endswith("DELETE 0"):
        raise HTTPException(404, "bot not found")
    return {"ok": True, "deleted_id": bot_id}


@router.post("/{bot_id}/mark-rotated")
async def mark_rotated(
    bot_id: int,
    body: MarkRotated,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Record a rotation timestamp. Optionally store the Telegram bot_id (NOT the token).

    Called by the rotate-token.html page after the user successfully runs the
    PowerShell command + Telegram getMe returns ok.
    """
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        if body.bot_id is not None:
            row = await conn.fetchrow(
                """
                UPDATE bot_catalog
                   SET last_rotated_at = NOW(),
                       last_verified_at = NOW(),
                       telegram_bot_id = $2,
                       updated_at = NOW()
                 WHERE id = $1
                 RETURNING *
                """,
                bot_id, body.bot_id,
            )
        else:
            row = await conn.fetchrow(
                """
                UPDATE bot_catalog
                   SET last_rotated_at = NOW(),
                       last_verified_at = NOW(),
                       updated_at = NOW()
                 WHERE id = $1
                 RETURNING *
                """,
                bot_id,
            )
    if not row:
        raise HTTPException(404, "bot not found")

    # Emit public event so /api/events/public reflects rotation activity
    try:
        from shared.events import emit as _emit
        await _emit(
            pool,
            "admin.bot_token_rotated",
            {"bot_id_internal": bot_id, "handle": row["handle"], "telegram_bot_id": body.bot_id},
            source="api.admin.bots_catalog",
        )
    except Exception:
        pass

    return {"ok": True, "bot": _row_to_dict(row)}


@router.get("/stats")
async def stats(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Aggregate stats for dashboards (count by status, oldest rotation, etc.)."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        s = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'active')        AS active,
                COUNT(*) FILTER (WHERE status = 'paused')        AS paused,
                COUNT(*) FILTER (WHERE status = 'deprecated')    AS deprecated,
                COUNT(*) FILTER (WHERE status = 'swap-target')   AS swap_targets,
                COUNT(*) FILTER (WHERE last_rotated_at IS NULL)  AS never_rotated,
                COUNT(*) FILTER (WHERE last_rotated_at < NOW() - INTERVAL '90 days') AS stale_90d,
                COUNT(*) FILTER (WHERE last_rotated_at < NOW() - INTERVAL '180 days') AS stale_180d,
                COUNT(*) FILTER (WHERE tier = 'critical')        AS tier_critical,
                COUNT(*) FILTER (WHERE tier = 'high')            AS tier_high,
                COUNT(*) FILTER (WHERE tier = 'medium')          AS tier_medium,
                COUNT(*) FILTER (WHERE tier = 'low')             AS tier_low,
                COUNT(*)                                          AS total
            FROM bot_catalog
            """
        )
    return {
        "total": int(s["total"] or 0),
        "active": int(s["active"] or 0),
        "paused": int(s["paused"] or 0),
        "deprecated": int(s["deprecated"] or 0),
        "swap_targets": int(s["swap_targets"] or 0),
        "never_rotated": int(s["never_rotated"] or 0),
        "stale_90d": int(s["stale_90d"] or 0),
        "stale_180d": int(s["stale_180d"] or 0),
        "by_tier": {
            "critical": int(s["tier_critical"] or 0),
            "high":     int(s["tier_high"] or 0),
            "medium":   int(s["tier_medium"] or 0),
            "low":      int(s["tier_low"] or 0),
        },
    }
