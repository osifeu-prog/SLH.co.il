"""Cross-bot coordination via shared Telegram group.

INTERNAL USE ONLY. The coordination group is NOT for commercial sale.
It is the single channel where all SLH bots and AI agents post status events
and (optionally) receive commands.

Activation: set COORDINATION_GROUP_CHAT_ID env to the numeric chat_id of the
group. If unset/zero, every function in this module becomes a safe no-op.

Outbound (aiogram bot instance available):

    from shared.coordination import post_event
    await post_event(bot, "claude-bot", "ready", "polling started")

Outbound (raw token, e.g. for python-telegram-bot or sync code):

    from shared.coordination import post_event_via_token
    await post_event_via_token(BOT_TOKEN, "campaign-bot", "deploy", "v1.4 live")

Inbound (aiogram dispatcher):

    from shared.coordination import register_inbound
    register_inbound(dp, bot_username="SLH_Claude_bot", handlers={
        "ping": lambda msg: msg.reply("pong"),
        "status": handle_status,
    })

Auth model: anyone in the coordination group can call any registered command.
Group membership IS the authorization boundary — keep the group locked down.
"""

from __future__ import annotations

import logging
import os
from typing import Awaitable, Callable, Dict, Optional

logger = logging.getLogger("shared.coordination")


def _read_chat_id() -> Optional[int]:
    raw = os.getenv("COORDINATION_GROUP_CHAT_ID", "").strip()
    if not raw:
        return None
    try:
        v = int(raw)
        return v if v != 0 else None
    except ValueError:
        logger.warning("COORDINATION_GROUP_CHAT_ID not numeric: %r", raw)
        return None


# Cached at import time. Bots are restarted on config changes so this is fine.
COORDINATION_GROUP_CHAT_ID: Optional[int] = _read_chat_id()

# One-character prefix per event type so noise is easy to filter visually.
EVENT_ICON: Dict[str, str] = {
    "ready":  "OK",
    "deploy": "->",
    "error":  "X!",
    "alert":  "!!",
    "info":   "i",
    "task":   "T",
    "ping":   "..",
}


def is_enabled() -> bool:
    """True iff a coordination chat_id is configured."""
    return COORDINATION_GROUP_CHAT_ID is not None


def is_coordination_group(chat_id) -> bool:
    """True iff `chat_id` matches the configured coordination group."""
    if COORDINATION_GROUP_CHAT_ID is None:
        return False
    try:
        return int(chat_id) == COORDINATION_GROUP_CHAT_ID
    except (TypeError, ValueError):
        return False


def _format(source: str, event_type: str, message: str) -> str:
    icon = EVENT_ICON.get(event_type, "*")
    return f"[{icon}] [{source}] {message}"[:4000]


async def post_event(bot, source: str, event_type: str, message: str) -> bool:
    """Post a status event to the coordination group via an aiogram bot instance.

    Returns True on success, False if disabled or send failed. Never raises.
    """
    if COORDINATION_GROUP_CHAT_ID is None:
        return False
    text = _format(source, event_type, message)
    try:
        await bot.send_message(
            chat_id=COORDINATION_GROUP_CHAT_ID,
            text=text,
            disable_notification=event_type not in ("error", "alert"),
        )
        return True
    except Exception as e:
        logger.warning("post_event failed (%s/%s): %s", source, event_type, e)
        return False


async def post_event_via_token(
    token: str, source: str, event_type: str, message: str
) -> bool:
    """Variant for callers without an aiogram bot instance.

    Uses raw HTTP. Useful for python-telegram-bot, plain scripts, or one-off
    pushes from the API layer. Never raises.
    """
    if COORDINATION_GROUP_CHAT_ID is None:
        return False
    text = _format(source, event_type, message)
    try:
        import httpx
    except ImportError:
        logger.warning("post_event_via_token: httpx not installed")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": COORDINATION_GROUP_CHAT_ID,
                    "text": text,
                    "disable_notification": event_type not in ("error", "alert"),
                },
            )
            return r.status_code == 200
    except Exception as e:
        logger.warning("post_event_via_token failed (%s/%s): %s", source, event_type, e)
        return False


def register_inbound(
    dispatcher,
    bot_username: str,
    handlers: Dict[str, Callable[..., Awaitable]],
) -> None:
    """Register aiogram inbound message handlers on the coordination group.

    Listens for messages in the coordination group whose text mentions
    `@bot_username`. The first word AFTER the mention is treated as a command
    name and routed to `handlers[command]`. Unknown commands receive a short
    reply listing available ones.

    No-op when COORDINATION_GROUP_CHAT_ID is unset.
    """
    if COORDINATION_GROUP_CHAT_ID is None:
        logger.info(
            "register_inbound skipped for %s (COORDINATION_GROUP_CHAT_ID unset)",
            bot_username,
        )
        return

    try:
        from aiogram import F
        from aiogram.types import Message
    except ImportError:
        logger.warning(
            "register_inbound: aiogram not installed; skipping for %s", bot_username
        )
        return

    handle = bot_username.lstrip("@").lower()

    @dispatcher.message(F.chat.id == COORDINATION_GROUP_CHAT_ID)
    async def _coordination_router(msg: Message):  # type: ignore[no-redef]
        text = (msg.text or "").strip()
        if not text:
            return
        # Must mention this specific bot
        if f"@{handle}" not in text.lower():
            return
        # Find next word after the mention
        words = text.split()
        cmd: Optional[str] = None
        for i, w in enumerate(words):
            if w.lower().lstrip("@") == handle and i + 1 < len(words):
                cmd = words[i + 1].lower().lstrip("/")
                break
        if cmd is None:
            return
        h = handlers.get(cmd)
        if h is None:
            try:
                available = ", ".join(sorted(handlers.keys())) or "(none)"
                await msg.reply(
                    f"Unknown command `{cmd}`. Available: {available}"
                )
            except Exception:
                pass
            return
        try:
            await h(msg)
        except Exception as e:
            logger.exception("coordination handler %s/%s failed", handle, cmd)
            try:
                await msg.reply(f"[X!] {type(e).__name__}: {e}")
            except Exception:
                pass

    logger.info(
        "register_inbound: %s wired with %d handler(s): %s",
        bot_username,
        len(handlers),
        ", ".join(sorted(handlers.keys())),
    )
