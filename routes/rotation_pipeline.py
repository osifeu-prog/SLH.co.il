"""Token Rotation Pipeline — atomic rotate→push→redeploy→verify→audit→broadcast.

Endpoint:  POST /api/admin/rotate-bot-token-pipeline
History:   GET  /api/admin/rotation-history

Single source of truth for token rotation across 3 surfaces (web admin pages,
Telegram bot inline panel, scripts). Each surface POSTs the same payload and
gets the same orchestrated outcome.

Security model:
- Token transits in HTTPS request body, lives in process memory only.
- Token is NEVER persisted, logged, or echoed in error messages.
- Audit log records `last4 + telegram_bot_id + actor + tier`, no full token.
- Critical-tier secrets require a confirm_token round-trip (60s TTL).

Failure model:
- Pre-Railway validation failure → no system change, audit `secret.rotate.failed`.
- Railway push failure → no system change, audit `secret.rotate.failed`.
- Railway redeploy failure → variable IS set; next deploy will pick it up.
  Audit `secret.rotate.failed`, broadcast to admins for manual recovery.
- Healthcheck failure → variable + deploy succeeded but bot not responding.
  Audit `secret.rotate.healthcheck_failed`, broadcast loud alert.
- setMyCommands failure → cosmetic only, best-effort, non-blocking.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from routes import railway_client

# Security headers stamped on every response from this router.
# - no-store: defeat any intermediary cache that might persist a token-bearing
#   request/response pair (Cloudflare, browser, reverse proxy).
# - X-Robots-Tag: belt-and-braces against accidental indexing.
# - Cross-Origin-Opener-Policy: harden if accessed from admin pages.
_SECURITY_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _secure(payload: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code, headers=_SECURITY_HEADERS)

log = logging.getLogger("slh.rotation_pipeline")

router = APIRouter(prefix="/api/admin", tags=["admin", "rotation"])

# ─── Constants ─────────────────────────────────────────────────────────────

CONFIRM_TTL_SECONDS = 60
HEALTHCHECK_DELAY_SECONDS = 8
COOLDOWN_BY_TIER = {"critical": 900, "high": 300, "medium": 60, "low": 0}

BOT_COMMANDS_PATH = Path(__file__).resolve().parent.parent / "config" / "bot_commands.json"

# ─── In-memory cooldown tracking ───────────────────────────────────────────
# Per-process. Resets on restart, which is fine — DB audit log is the
# durable source of truth. Maps env_var → unix timestamp of last successful rotation.
_LAST_ROTATION_TS: dict[str, float] = {}


# ─── Models ────────────────────────────────────────────────────────────────


class RotateRequest(BaseModel):
    env_var: str = Field(..., min_length=1, max_length=64)
    new_token: str = Field(..., min_length=10, max_length=512)
    expect_handle: Optional[str] = Field(None, max_length=64)  # @SLH_xxx_bot, optional
    swap_mode: bool = Field(False)
    confirm_token: Optional[str] = Field(None, max_length=64)
    skip_healthcheck: bool = Field(False)  # for non-bot secrets that have no getMe equivalent


# ─── Confirm-token table (for Critical tier) ──────────────────────────────


_CONFIRM_SCHEMA_READY = False


async def _ensure_confirm_schema(pool) -> None:
    global _CONFIRM_SCHEMA_READY
    if _CONFIRM_SCHEMA_READY:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rotation_confirm_tokens (
                confirm_token  TEXT PRIMARY KEY,
                env_var        TEXT NOT NULL,
                actor          TEXT NOT NULL,
                expires_at     TIMESTAMPTZ NOT NULL,
                used           BOOLEAN NOT NULL DEFAULT FALSE,
                created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_rotation_confirm_expires ON rotation_confirm_tokens (expires_at)"
        )
    _CONFIRM_SCHEMA_READY = True


async def _create_confirm_token(pool, env_var: str, actor: str) -> str:
    await _ensure_confirm_schema(pool)
    token = secrets.token_urlsafe(24)
    async with pool.acquire() as conn:
        # GC expired rows
        await conn.execute("DELETE FROM rotation_confirm_tokens WHERE expires_at < NOW()")
        await conn.execute(
            "INSERT INTO rotation_confirm_tokens (confirm_token, env_var, actor, expires_at) "
            f"VALUES ($1, $2, $3, NOW() + INTERVAL '{CONFIRM_TTL_SECONDS} seconds')",
            token, env_var, str(actor),
        )
    return token


async def _consume_confirm_token(pool, token: str, env_var: str, actor: str) -> bool:
    await _ensure_confirm_schema(pool)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE rotation_confirm_tokens
               SET used = TRUE
             WHERE confirm_token = $1
               AND env_var       = $2
               AND actor         = $3
               AND used          = FALSE
               AND expires_at   >= NOW()
             RETURNING confirm_token
            """,
            token, env_var, str(actor),
        )
    return row is not None


# ─── Helpers ───────────────────────────────────────────────────────────────


async def _telegram_get_me(token: str) -> dict:
    """Validate a bot token via Telegram getMe. Returns result dict on success."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise HTTPException(400, f"Telegram getMe HTTP {r.status_code}")
    j = r.json()
    if not j.get("ok"):
        raise HTTPException(400, f"Telegram rejected token: {j.get('description', 'unknown')}")
    return j["result"]


async def _telegram_get_me_quiet(token: str) -> Optional[dict]:
    """Like _telegram_get_me but returns None on failure instead of raising."""
    try:
        return await _telegram_get_me(token)
    except Exception:
        return None


async def _telegram_set_my_commands(token: str, commands: list[dict]) -> bool:
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json={"commands": commands})
    if r.status_code != 200:
        return False
    return bool(r.json().get("ok"))


def _load_bot_commands(handle: str) -> list[dict]:
    """Return the command list to register for `handle`. Falls back to default."""
    if not BOT_COMMANDS_PATH.exists():
        return [
            {"command": "start", "description": "התחל"},
            {"command": "help",  "description": "עזרה"},
        ]
    try:
        cfg = json.loads(BOT_COMMANDS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    base = cfg.get("default", [])
    extra = (cfg.get("per_bot") or {}).get(handle, [])
    return base + extra


async def _broadcast_admins(text: str) -> None:
    """Send a Telegram message to every admin in ADMIN_TELEGRAM_IDS via SLH_CLAUDE_BOT_TOKEN.

    Best-effort. Failures are logged but don't break the pipeline.
    """
    bot_token = os.getenv("SLH_CLAUDE_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        log.warning("rotation broadcast skipped — no admin bot token in env")
        return
    admin_ids = [
        x.strip() for x in (os.getenv("ADMIN_TELEGRAM_IDS", "224223270") or "").split(",")
        if x.strip()
    ]
    if not admin_ids:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        for tg_id in admin_ids:
            try:
                await client.post(url, json={"chat_id": tg_id, "text": text})
            except Exception as e:
                log.warning("rotation broadcast to %s failed: %s", tg_id, e)


def _redact(text: str) -> str:
    """Final safety net: strip token-shaped substrings before any string crosses
    into a log line or HTTPException detail."""
    return re.sub(r"\d{8,12}:[A-Za-z0-9_\-]{30,}", "<BOT_TOKEN>", text)


async def _lookup_bot_by_env(pool, env_var: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM bot_catalog WHERE env_var = $1 LIMIT 1", env_var
        )
    return dict(row) if row else None


async def _mark_rotated(pool, bot_id: int, tg_bot_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE bot_catalog
               SET last_rotated_at  = NOW(),
                   last_verified_at = NOW(),
                   telegram_bot_id  = $2,
                   updated_at       = NOW()
             WHERE id = $1
            """,
            bot_id, tg_bot_id,
        )


def _resolve_tier(env_var: str, bot_row: Optional[dict]) -> str:
    """Tier from bot_catalog if a bot row exists, otherwise from services config."""
    if bot_row and bot_row.get("tier"):
        return bot_row["tier"]
    try:
        svc = railway_client.lookup_service(env_var)
        return svc.get("tier", "medium")
    except Exception:
        return "medium"


async def _audit(pool, action: str, **kwargs) -> str:
    """Wrap audit_log_write — pulls a fresh connection. Returns entry_hash or ''."""
    try:
        from main import audit_log_write  # type: ignore
    except Exception:
        return ""
    async with pool.acquire() as conn:
        try:
            return await audit_log_write(conn, action, **kwargs)
        except Exception as e:
            log.warning("audit_log_write failed (%s): %s", action, e)
            return ""


def _lazy_require_admin():
    from main import _require_admin  # type: ignore
    return _require_admin


# ─── Endpoint ──────────────────────────────────────────────────────────────


@router.post("/rotate-bot-token-pipeline")
async def rotate_pipeline(
    body: RotateRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Atomic rotate-push-redeploy-verify-audit-broadcast.

    Returns one of:
        {ok: true, ...}                                  — success
        {ok: false, needs_confirm: true, confirm_token}  — Critical tier, awaiting confirm
        {ok: false, phase: "healthcheck_failed", ...}    — soft failure, recovery needed
    Raises 4xx on user errors, 502 on Railway failures.
    """
    actor_id = _lazy_require_admin()(authorization, x_admin_key)
    actor = str(actor_id)

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")

    # ── Phase 0: lookup + tier resolution ────────────────────────────────
    bot = await _lookup_bot_by_env(pool, body.env_var)
    tier = _resolve_tier(body.env_var, bot)
    is_bot = bot is not None
    skip_healthcheck = body.skip_healthcheck or not is_bot
    handle = (bot or {}).get("handle") or body.expect_handle or "(non-bot)"

    # ── Cooldown check ───────────────────────────────────────────────────
    cooldown = COOLDOWN_BY_TIER.get(tier, 0)
    last_ts = _LAST_ROTATION_TS.get(body.env_var, 0)
    if cooldown and (time.time() - last_ts) < cooldown:
        wait = int(cooldown - (time.time() - last_ts))
        raise HTTPException(429, f"cooldown active for {body.env_var} — wait {wait}s")

    # ── Phase 1: Critical tier confirm-token gate ────────────────────────
    if tier == "critical":
        if not body.confirm_token:
            ct = await _create_confirm_token(pool, body.env_var, actor)
            return _secure({
                "ok": False,
                "needs_confirm": True,
                "confirm_token": ct,
                "expires_in_seconds": CONFIRM_TTL_SECONDS,
                "tier": tier,
                "env_var": body.env_var,
                "handle": handle,
                "message_he": (
                    f"⚠️ פעולה רגישה (tier={tier}). שלח שוב את אותה הבקשה תוך "
                    f"{CONFIRM_TTL_SECONDS} שניות עם confirm_token כדי לאשר."
                ),
            })
        ok = await _consume_confirm_token(pool, body.confirm_token, body.env_var, actor)
        if not ok:
            raise HTTPException(403, "confirm_token invalid, expired, or for different env_var/actor")

    # ── Phase 2: validate token against Telegram (if it's a bot token) ───
    tg_info: dict = {}
    if not skip_healthcheck:
        try:
            tg_info = await _telegram_get_me(body.new_token)
        except HTTPException:
            await _audit(pool, "secret.rotate.failed",
                         actor_user_id=actor_id, resource_type="bot_token",
                         resource_id=body.env_var,
                         metadata={"phase": "validate", "tier": tier})
            raise
        if body.expect_handle and not body.swap_mode:
            expected = body.expect_handle.lstrip("@").lower()
            actual = (tg_info.get("username") or "").lower()
            if expected != actual:
                await _audit(pool, "secret.rotate.failed",
                             actor_user_id=actor_id, resource_type="bot_token",
                             resource_id=body.env_var,
                             metadata={"phase": "handle_mismatch", "expected": expected, "actual": actual})
                raise HTTPException(
                    400,
                    f"token belongs to @{actual} not @{expected}. "
                    "Set swap_mode=true to override (intentional bot replacement)."
                )

    # ── Phase 3: audit initiated ─────────────────────────────────────────
    last4 = body.new_token[-4:]
    initiated_hash = await _audit(
        pool, "secret.rotate.initiated",
        actor_user_id=actor_id,
        resource_type="bot_token" if is_bot else "system_secret",
        resource_id=body.env_var,
        before_state={
            "last_rotated_at": (bot or {}).get("last_rotated_at").isoformat()
                if (bot and bot.get("last_rotated_at")) else None,
            "handle": handle,
        },
        after_state={"last4": last4, "tg_bot_id": tg_info.get("id")},
        metadata={"tier": tier, "swap": body.swap_mode, "is_bot": is_bot},
    )

    # ── Phase 4: push to Railway ─────────────────────────────────────────
    try:
        await railway_client.variable_upsert(body.env_var, body.new_token, skip_deploys=True)
    except Exception as e:
        msg = _redact(str(e))[:300]
        await _audit(pool, "secret.rotate.failed",
                     actor_user_id=actor_id, resource_type="bot_token" if is_bot else "system_secret",
                     resource_id=body.env_var,
                     metadata={"phase": "railway_push", "tier": tier, "error": msg})
        raise HTTPException(502, f"Railway variable_upsert failed: {msg}")

    # ── Phase 5: trigger redeploy ────────────────────────────────────────
    deploy_id: Optional[str] = None
    try:
        result = await railway_client.service_redeploy(body.env_var)
        deploy_id = result.get("deploy_id")
    except Exception as e:
        msg = _redact(str(e))[:300]
        await _audit(pool, "secret.rotate.failed",
                     actor_user_id=actor_id, resource_type="bot_token" if is_bot else "system_secret",
                     resource_id=body.env_var,
                     metadata={"phase": "railway_redeploy", "tier": tier, "error": msg,
                               "note": "variable WAS pushed; manual redeploy required"})
        await _broadcast_admins(
            f"⚠️ סיבוב חלקי: {handle} ({body.env_var})\n"
            f"Variable עודכן ב-Railway אך redeploy נכשל. נדרש redeploy ידני."
        )
        raise HTTPException(502, f"Railway redeploy failed (variable WAS set): {msg}")

    # ── Phase 6: wait + healthcheck ──────────────────────────────────────
    if not skip_healthcheck:
        await asyncio.sleep(HEALTHCHECK_DELAY_SECONDS)
        healthy = await _telegram_get_me_quiet(body.new_token)
        if not healthy:
            await _audit(pool, "secret.rotate.healthcheck_failed",
                         actor_user_id=actor_id, resource_type="bot_token",
                         resource_id=body.env_var,
                         metadata={"tier": tier, "deploy_id": deploy_id, "delay_s": HEALTHCHECK_DELAY_SECONDS})
            await _broadcast_admins(
                f"🚨 ROTATION HEALTHCHECK נכשל: {handle} ({body.env_var})\n"
                f"Variable + redeploy הצליחו אך הבוט לא מגיב ל-getMe.\n"
                f"Deploy: {deploy_id}\n"
                f"דרושה התערבות ידנית."
            )
            return _secure({
                "ok": False,
                "phase": "healthcheck_failed",
                "deploy_id": deploy_id,
                "tier": tier,
                "env_var": body.env_var,
                "handle": handle,
            })

    # ── Phase 7: mark rotated in catalog ─────────────────────────────────
    if bot and tg_info:
        try:
            await _mark_rotated(pool, bot["id"], tg_info["id"])
        except Exception as e:
            log.warning("mark_rotated failed: %s", e)

    # ── Phase 8: setMyCommands sync (best-effort) ────────────────────────
    if is_bot and not skip_healthcheck:
        try:
            cmds = _load_bot_commands(handle)
            if cmds:
                ok = await _telegram_set_my_commands(body.new_token, cmds)
                if ok:
                    await _audit(pool, "secret.rotate.setmycommands_synced",
                                 actor_user_id=actor_id, resource_type="bot_token",
                                 resource_id=body.env_var,
                                 metadata={"command_count": len(cmds), "handle": handle})
        except Exception as e:
            log.warning("setMyCommands for %s failed: %s", handle, e)

    # ── Phase 9: audit pushed ────────────────────────────────────────────
    await _audit(
        pool, "secret.rotate.pushed",
        actor_user_id=actor_id,
        resource_type="bot_token" if is_bot else "system_secret",
        resource_id=body.env_var,
        after_state={"last4": last4, "tg_bot_id": tg_info.get("id"), "deploy_id": deploy_id},
        metadata={"tier": tier, "handle": handle},
    )

    # ── Phase 10: broadcast success ──────────────────────────────────────
    _LAST_ROTATION_TS[body.env_var] = time.time()
    await _broadcast_admins(
        f"✅ סיבוב טוקן הושלם: {handle}\n"
        f"env_var: {body.env_var}\n"
        f"tier: {tier}\n"
        f"last4: ...{last4}\n"
        f"deploy: {(deploy_id or '')[:16]}"
    )

    return _secure({
        "ok": True,
        "env_var": body.env_var,
        "handle": handle,
        "tier": tier,
        "deploy_id": deploy_id,
        "tg_bot_id": tg_info.get("id"),
        "tg_username": tg_info.get("username"),
        "last4": last4,
        "audit_initiated_hash": initiated_hash,
    })


# ─── Rotation history endpoint ─────────────────────────────────────────────


@router.get("/rotation-history")
async def rotation_history(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    env_var: Optional[str] = Query(None, max_length=64),
    action: Optional[str] = Query(None, max_length=64),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Returns audit-log rows for `secret.rotate.*` actions, newest first."""
    _lazy_require_admin()(authorization, x_admin_key)
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")

    where = ["action LIKE 'secret.rotate.%'"]
    params: list = []
    if env_var:
        params.append(env_var)
        where.append(f"resource_id = ${len(params)}")
    if action:
        params.append(action)
        where.append(f"action = ${len(params)}")
    params.append(limit)
    sql = (
        "SELECT id, action, actor_type, actor_user_id, resource_type, resource_id, "
        "       before_state, after_state, metadata, created_at, entry_hash "
        f"  FROM institutional_audit "
        f" WHERE {' AND '.join(where)} "
        f" ORDER BY id DESC LIMIT ${len(params)}"
    )
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception as e:
            log.warning("rotation_history query failed: %s", e)
            return {"count": 0, "events": [], "error": str(e)[:200]}

    def _serialize(r):
        d = dict(r)
        for k in ("before_state", "after_state", "metadata"):
            v = d.get(k)
            if isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except Exception:
                    pass
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        return d

    return {"count": len(rows), "events": [_serialize(r) for r in rows]}


# ─── Self-check endpoint ───────────────────────────────────────────────────


@router.get("/rotation-pipeline/health")
async def rotation_health(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Verify config + Railway API token + bot token are wired."""
    _lazy_require_admin()(authorization, x_admin_key)
    cfg_ok = False
    cfg_count = 0
    cfg_err = None
    try:
        cfg = railway_client.load_services_config()
        cfg_ok = True
        cfg_count = sum(1 for k in cfg.get("services", {}) if not k.startswith("_"))
    except Exception as e:
        cfg_err = str(e)[:200]
    rw = await railway_client.health_probe()
    return {
        "config_loaded": cfg_ok,
        "config_entries": cfg_count,
        "config_error": cfg_err,
        "railway_token_ok": rw.get("ok", False),
        "railway_me_email": rw.get("me_email"),
        "railway_error": rw.get("error"),
        "broadcast_bot_token_set": bool(
            os.getenv("SLH_CLAUDE_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        ),
        "admin_telegram_ids_count": len(
            [x for x in (os.getenv("ADMIN_TELEGRAM_IDS", "224223270") or "").split(",") if x.strip()]
        ),
    }
