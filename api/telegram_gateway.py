"""Telegram Gateway Layer â€” Mini App initData validation + user resolution.

This is the standardized entry point for ALL Telegram-originated requests
(bots and Mini Apps) into the SLH Core API. Bot handlers stay thin:
  parse -> call gateway.verify() -> call business API -> render.

The gateway does four things:
  1. Validates Telegram Mini App initData (HMAC-SHA256 per Telegram spec).
  2. Resolves Telegram user_id -> SLH user_id from Postgres.
  3. Resolves role (admin / user / guest) from env + DB.
  4. Writes an audit entry to event_log (when available).

Nothing here mutates business state. Mutations go through existing /api/* routes.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Request

log = logging.getLogger("slh.gateway")

# Token used to sign Mini App initData. Same token that runs the bot.
# The Mini App is opened from a specific bot, so each bot has its own token.
# For multi-bot Mini Apps, look up the token by bot username from initData.
MINI_APP_BOT_TOKENS: dict[str, str] = {}


def _load_bot_tokens() -> None:
    """Populate MINI_APP_BOT_TOKENS from env.

    Expected env var pattern: BOT_TOKEN_<username_upper> = <token>
    Example:                  BOT_TOKEN_SLH_CLAUDE_BOT   = 123:ABC
    Falls back to TELEGRAM_BOT_TOKEN (primary bot) if nothing else is set.
    """
    MINI_APP_BOT_TOKENS.clear()
    for key, value in os.environ.items():
        if key.startswith("BOT_TOKEN_") and value:
            username = key[len("BOT_TOKEN_") :].lower().replace("_", "")
            MINI_APP_BOT_TOKENS[username] = value
    primary = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("SLH_CLAUDE_BOT_TOKEN")
    if primary:
        MINI_APP_BOT_TOKENS.setdefault("_primary", primary)


_load_bot_tokens()

# Admin Telegram IDs (comma-separated env var). Osif is default.
ADMIN_TELEGRAM_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_TELEGRAM_IDS", "224223270").split(",")
    if x.strip().isdigit()
}

# How old initData can be (Telegram recommends 24h; we use 1h for sensitive ops).
INIT_DATA_MAX_AGE_SECONDS = int(os.getenv("MINIAPP_INIT_DATA_MAX_AGE", "3600"))


@dataclass
class TelegramUser:
    """Resolved identity after gateway verification."""

    telegram_id: int
    slh_user_id: Optional[int]
    username: Optional[str]
    first_name: Optional[str]
    is_admin: bool
    auth_date: int
    source: str  # "miniapp" | "bot"


class GatewayError(HTTPException):
    """Gateway-level failure. Returns 401 with a specific code."""

    def __init__(self, code: str, detail: str, status: int = 401):
        super().__init__(status_code=status, detail={"code": code, "detail": detail})
        self.code = code


def _bot_token_for(bot_username: Optional[str]) -> str:
    """Pick the right bot token for signature verification.

    Telegram Mini Apps don't explicitly carry the bot username in initData,
    but the frontend knows which bot opened it (tg.initDataUnsafe.start_param
    or the URL path). Callers can pass the hint; otherwise we fall back to
    the primary bot.
    """
    if bot_username:
        key = bot_username.lower().replace("_", "").replace("@", "")
        token = MINI_APP_BOT_TOKENS.get(key)
        if token:
            return token
    primary = MINI_APP_BOT_TOKENS.get("_primary")
    if not primary:
        raise GatewayError(
            "no_bot_token",
            "No bot token configured on server. Set TELEGRAM_BOT_TOKEN or BOT_TOKEN_<name>.",
            status=500,
        )
    return primary


def verify_init_data(init_data: str, bot_username: Optional[str] = None) -> dict:
    """Validate a Telegram Mini App initData string.

    Returns the parsed data dict if valid. Raises GatewayError otherwise.

    Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    Algorithm:
      1. Parse the query string.
      2. Extract `hash`, sort the rest as `key=value\\n...`.
      3. secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
      4. check_hash = HMAC_SHA256(key=secret_key, msg=data_check_string)
      5. Compare in constant time.
    """
    if not init_data:
        raise GatewayError("empty_init_data", "initData missing")

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError as e:
        raise GatewayError("bad_init_data", f"Malformed initData: {e}")

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise GatewayError("missing_hash", "initData has no hash field")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    bot_token = _bot_token_for(bot_username)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise GatewayError("bad_signature", "initData hash mismatch")

    # Freshness check
    auth_date = int(pairs.get("auth_date", "0"))
    age = int(time.time()) - auth_date
    if age > INIT_DATA_MAX_AGE_SECONDS:
        raise GatewayError(
            "stale_init_data",
            f"initData is {age}s old (max {INIT_DATA_MAX_AGE_SECONDS}s)",
        )
    if auth_date <= 0:
        raise GatewayError("missing_auth_date", "initData missing auth_date")

    return pairs


def parse_user_from_init_data(parsed: dict) -> dict:
    """Extract the user object from verified initData."""
    user_json = parsed.get("user")
    if not user_json:
        raise GatewayError("no_user", "initData has no user payload")
    try:
        return json.loads(user_json)
    except json.JSONDecodeError as e:
        raise GatewayError("bad_user_json", f"user field not JSON: {e}")


async def _resolve_slh_user_id(telegram_id: int, db_pool) -> Optional[int]:
    """Look up the SLH user id for a Telegram id. Returns None if not registered."""
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE telegram_id = $1 LIMIT 1", telegram_id
            )
            return row["id"] if row else None
    except Exception as e:
        log.warning("user resolution failed for %s: %s", telegram_id, e)
        return None


async def verify_miniapp_request(
    request: Request,
    x_telegram_init_data: Optional[str] = Header(None),
    x_bot_username: Optional[str] = Header(None),
) -> TelegramUser:
    """FastAPI dependency for Mini App endpoints.

    Usage:
        @app.get("/api/miniapp/dashboard")
        async def dashboard(user: TelegramUser = Depends(verify_miniapp_request)):
            ...
    """
    parsed = verify_init_data(x_telegram_init_data or "", x_bot_username)
    user = parse_user_from_init_data(parsed)
    telegram_id = int(user["id"])

    db_pool = getattr(request.app.state, "db_pool", None)
    slh_user_id = await _resolve_slh_user_id(telegram_id, db_pool)

    resolved = TelegramUser(
        telegram_id=telegram_id,
        slh_user_id=slh_user_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
        is_admin=telegram_id in ADMIN_TELEGRAM_IDS,
        auth_date=int(parsed["auth_date"]),
        source="miniapp",
    )
    await _audit(request, resolved, status="ok")
    return resolved


async def verify_bot_request(
    telegram_id: int,
    bot_username: Optional[str] = None,
    request: Optional[Request] = None,
) -> TelegramUser:
    """Non-Mini-App entry point. Used by bot handlers that already know the
    Telegram ID (aiogram has already authenticated the update via bot token).
    """
    db_pool = getattr(request.app.state, "db_pool", None) if request else None
    slh_user_id = await _resolve_slh_user_id(telegram_id, db_pool)
    resolved = TelegramUser(
        telegram_id=telegram_id,
        slh_user_id=slh_user_id,
        username=None,
        first_name=None,
        is_admin=telegram_id in ADMIN_TELEGRAM_IDS,
        auth_date=int(time.time()),
        source="bot",
    )
    if request:
        await _audit(request, resolved, status="ok")
    return resolved


async def _audit(request: Request, user: TelegramUser, status: str) -> None:
    """Write an event_log row when the table exists. Silent no-op otherwise."""
    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        return
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO event_log (event_type, telegram_id, slh_user_id, payload, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                """,
                f"gateway.{user.source}",
                user.telegram_id,
                user.slh_user_id,
                json.dumps(
                    {
                        "path": str(request.url.path) if request else None,
                        "is_admin": user.is_admin,
                        "status": status,
                    }
                ),
            )
    except Exception:
        pass


def require_admin(user: TelegramUser) -> TelegramUser:
    """Guard clause for admin-only endpoints."""
    if not user.is_admin:
        raise GatewayError(
            "not_admin", f"Telegram id {user.telegram_id} is not an admin", status=403
        )
    return user
