"""
Ledger Event Listener — polls the `event_log` table and fans interesting events
out to Telegram (Workers group + DM to user).

Only started when BOT_KEY=ledger (checked in bot_template.main()).

Events handled:
    payment.cleared       → DM buyer + post to Workers group
    stake.opened          → DM user + post to Workers group
    stake.unlocked        → DM user + post to Workers group
    device.registered     → DM user (TG-linked via users_by_phone.telegram_id)
    device.heartbeat      → silent (counted only for chain-status page)
    academy.payout_made   → DM instructor + post to Workers group
    guardian.alert        → post to Workers group (urgent)

Env:
    LEDGER_WORKERS_CHAT_ID   — required, the TG chat where ops updates go
    DATABASE_URL             — shared with the API; listener reads event_log + users_by_phone
    EVENT_POLL_INTERVAL_S    — default 3.0
    LEDGER_CURSOR_FILE       — default /app/data/ledger_cursor.json
"""
from __future__ import annotations

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional

import asyncpg

logger = logging.getLogger("slh.ledger_listener")

WORKERS_CHAT_ID = os.getenv("LEDGER_WORKERS_CHAT_ID", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
POLL_INTERVAL = float(os.getenv("EVENT_POLL_INTERVAL_S", "3.0"))
CURSOR_FILE = Path(os.getenv("LEDGER_CURSOR_FILE", "/app/data/ledger_cursor.json"))

HANDLED_TYPES = [
    "payment.cleared",
    "stake.opened",
    "stake.unlocked",
    "device.registered",
    "academy.payout_made",
    "guardian.alert",
]


def _load_cursor() -> int:
    try:
        if CURSOR_FILE.exists():
            data = json.loads(CURSOR_FILE.read_text())
            return int(data.get("cursor", 0))
    except Exception as e:
        logger.warning("cursor load failed: %s", e)
    return 0


def _save_cursor(cursor: int) -> None:
    try:
        CURSOR_FILE.parent.mkdir(parents=True, exist_ok=True)
        CURSOR_FILE.write_text(json.dumps({"cursor": cursor}))
    except Exception as e:
        logger.warning("cursor save failed: %s", e)


async def _lookup_tg_id(pool, user_id: int) -> Optional[int]:
    """Map slh user_id → telegram_id via users_by_phone (if linked)."""
    try:
        async with pool.acquire() as conn:
            tg_id = await conn.fetchval(
                "SELECT telegram_id FROM users_by_phone WHERE user_id = $1 AND telegram_id IS NOT NULL",
                user_id
            )
            return int(tg_id) if tg_id else None
    except Exception:
        return None


async def _safe_dm(bot, chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id, text, disable_web_page_preview=True)
    except Exception as e:
        logger.warning("send_message to %s failed: %s", chat_id, e)


async def _handle_payment_cleared(bot, pool, evt: dict) -> None:
    p = evt.get("payload", {}) or {}
    user_id = p.get("user_id")
    amount = p.get("amount")
    currency = p.get("currency", "ILS")
    method = p.get("method", "?")
    workers_msg = (
        f"💰 תשלום אומת\n"
        f"User: {user_id}\n"
        f"Amount: {amount} {currency}\n"
        f"Method: {method}\n"
        f"Ref: {p.get('reference','-')}"
    )
    if WORKERS_CHAT_ID:
        await _safe_dm(bot, int(WORKERS_CHAT_ID), workers_msg)
    if user_id:
        tg = await _lookup_tg_id(pool, user_id)
        if tg:
            await _safe_dm(bot, tg, f"✅ התשלום שלך אומת\n{amount} {currency} · {method}\nתודה על הרכישה!")


async def _handle_stake(bot, pool, evt: dict) -> None:
    p = evt.get("payload", {}) or {}
    tag = evt["type"].split(".")[-1]  # opened / unlocked
    user_id = p.get("user_id")
    amt = p.get("amount")
    cur = p.get("currency", "TON")
    plan = p.get("plan", "?")
    verb = "נפתחה" if tag == "opened" else "שוחררה"
    icon = "🔒" if tag == "opened" else "🔓"
    workers_msg = (
        f"{icon} הפקדה {verb}\n"
        f"User: {user_id}\n"
        f"Plan: {plan}\n"
        f"Amount: {amt} {cur}\n"
        f"Status: {p.get('status','?')}"
    )
    if WORKERS_CHAT_ID:
        await _safe_dm(bot, int(WORKERS_CHAT_ID), workers_msg)
    if user_id:
        tg = await _lookup_tg_id(pool, user_id)
        if tg:
            await _safe_dm(bot, tg, f"{icon} הפקדת סטייקינג {verb}: {amt} {cur} ({plan})")


async def _handle_device_registered(bot, pool, evt: dict) -> None:
    p = evt.get("payload", {}) or {}
    user_id = p.get("user_id")
    device_id = p.get("device_id", "?")
    if WORKERS_CHAT_ID:
        await _safe_dm(bot, int(WORKERS_CHAT_ID),
                       f"📟 מכשיר חדש נרשם\nUser: {user_id}\nDevice: {device_id}")
    if user_id:
        tg = await _lookup_tg_id(pool, user_id)
        if tg:
            await _safe_dm(bot, tg,
                           f"📟 מכשיר נקשר בהצלחה\nDevice ID: {device_id}\n"
                           f"אם לא אתה קישרת, שלח /revoke מיידית.")


async def _handle_payout_made(bot, pool, evt: dict) -> None:
    p = evt.get("payload", {}) or {}
    amt = p.get("amount_ils", 0)
    instructor_id = p.get("instructor_id")
    if WORKERS_CHAT_ID:
        await _safe_dm(bot, int(WORKERS_CHAT_ID),
                       f"🎓 תשלום למרצה בוצע\n"
                       f"Instructor: {instructor_id}\n"
                       f"Amount: ₪{amt:.2f}\n"
                       f"TX: {p.get('payout_tx','?')}")


async def _handle_guardian_alert(bot, pool, evt: dict) -> None:
    p = evt.get("payload", {}) or {}
    level = p.get("level", "info").upper()
    msg = p.get("message", "Guardian alert")
    user_id = p.get("user_id", "?")
    if WORKERS_CHAT_ID:
        await _safe_dm(bot, int(WORKERS_CHAT_ID),
                       f"🛡 GUARDIAN [{level}]\nUser: {user_id}\n{msg}")


DISPATCH = {
    "payment.cleared": _handle_payment_cleared,
    "stake.opened": _handle_stake,
    "stake.unlocked": _handle_stake,
    "device.registered": _handle_device_registered,
    "academy.payout_made": _handle_payout_made,
    "guardian.alert": _handle_guardian_alert,
}


async def run(bot) -> None:
    """Main loop. Call via `asyncio.create_task(run(bot))` from the bot startup."""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set — ledger listener disabled")
        return
    if not WORKERS_CHAT_ID:
        logger.warning("LEDGER_WORKERS_CHAT_ID not set — listener will run silently (no workers fanout)")

    # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
    # Falls back to direct create_pool if shared_db_core unavailable (e.g. in a
    # bot container that didn't copy the file).
    try:
        from shared_db_core import init_db_pool as _shared_init_db_pool
        pool = await _shared_init_db_pool(DATABASE_URL)
    except Exception as _shared_err:
        logger.warning("shared_db_core unavailable, direct pool: %s", _shared_err)
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    cursor = _load_cursor()
    logger.info("ledger_listener started: cursor=%s workers_chat=%s", cursor, WORKERS_CHAT_ID or "(none)")

    while True:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, event_type, payload FROM event_log "
                    "WHERE id > $1 AND event_type = ANY($2::text[]) "
                    "ORDER BY id ASC LIMIT 50",
                    cursor, HANDLED_TYPES
                )
            for r in rows:
                evt = {
                    "id": r["id"],
                    "type": r["event_type"],
                    "payload": r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"]),
                }
                try:
                    handler = DISPATCH.get(evt["type"])
                    if handler:
                        await handler(bot, pool, evt)
                except Exception as e:
                    logger.exception("handler failed for event %s: %s", evt["id"], e)
                cursor = evt["id"]
                _save_cursor(cursor)
        except Exception as e:
            logger.exception("ledger_listener loop error: %s", e)
        await asyncio.sleep(POLL_INTERVAL)
