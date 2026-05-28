"""SLH Token Rotation ׳’ג‚¬ג€ Telegram admin panel for @SLH_Claude_bot.

Mirrors /admin/tokens.html on Telegram with inline keyboards. Same backend
endpoint (POST /api/admin/rotate-bot-token-pipeline) ׳’ג‚¬ג€ bot is just a wrapper.

Commands:
    /admin              ׳’ג€ ג€™ main menu (Tokens / Railway / Status / Audit)

Callbacks (data prefixes):
    adm:home            ׳’ג€ ג€™ show main menu
    adm:tokens:<page>   ׳’ג€ ג€™ show paginated bot list
    adm:bot:<id>        ׳’ג€ ג€™ show bot detail card
    adm:rot:<id>        ׳’ג€ ג€™ start rotate flow for bot
    adm:swap:<id>       ׳’ג€ ג€™ start rotate flow with swap_mode=true
    adm:hist            ׳’ג€ ג€™ show last 10 audit events
    adm:status          ׳’ג€ ג€™ pipeline-health snapshot
    adm:railway         ׳’ג€ ג€™ bridge to railway_ops dashboard
    adm:cancel          ׳’ג€ ג€™ cancel pending token-input flow

Auth: shared with bot.py via auth.is_authorized ׳’ג‚¬ג€ only Osif's IDs reach here.

In-memory state: pending token-input requests per user (TTL 5 min). Resets on
restart, which is fine ׳’ג‚¬ג€ a stale flow just times out and the user retries.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Optional

import httpx
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

log = logging.getLogger("slh-rotation-panel")

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")

PAGE_SIZE = 8
TIER_EMOJI = {"critical": "׳ ֲֲֲ¨", "high": "׳’ֲֲ ׳ֲ¸ֲ", "medium": "׳ ֲג€ֲ¹", "low": "׳’ֲֳ—"}
TIER_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PENDING_TTL_SECONDS = 300  # 5 min for user to send the new token

# Per-user pending flow state. Cleared on success/cancel/timeout.
# Key: telegram_user_id, Value: {bot, swap, confirm_token, message_id, started_at}
_PENDING: dict[int, dict] = {}


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ HTTP helpers ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬


async def _api_get(path: str) -> dict:
    if not ADMIN_KEY:
        raise RuntimeError("ADMIN_API_KEY not set in slh-claude-bot/.env")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(API_BASE + path, headers={"X-Admin-Key": ADMIN_KEY})
        r.raise_for_status()
        return r.json()


async def _api_post(path: str, body: dict) -> tuple[int, dict]:
    if not ADMIN_KEY:
        return 0, {"error": "ADMIN_API_KEY not set in slh-claude-bot/.env"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            API_BASE + path,
            headers={"X-Admin-Key": ADMIN_KEY, "Content-Type": "application/json"},
            json=body,
        )
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {"raw": r.text[:300]}


def _days_since(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        diff = (datetime.now(timezone.utc) - dt).total_seconds()
        return int(diff // 86400)
    except Exception:
        return None


def _stale_label(days: Optional[int]) -> str:
    if days is None:
        return "׳’ֲג€ never"
    if days > 180:
        return f"׳ ֲֲֲ¨ {days}d"
    if days > 90:
        return f"׳’ֲֲ ׳ֲ¸ֲ {days}d"
    return f"׳’ֲג€¦ {days}d"


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Keyboards ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬


def _kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="׳ ֲג€ֲ Tokens",  callback_data="adm:tokens:0"),
         InlineKeyboardButton(text="׳ ֲֲג€ Railway", callback_data="adm:railway")],
        [InlineKeyboardButton(text="׳ ֲג€ֲ Pipeline status", callback_data="adm:status"),
         InlineKeyboardButton(text="׳ ֲג€ֲ Audit",   callback_data="adm:hist")],
    ])


def _kb_back_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="׳’ֲ¬ג€¦ ׳ֲ¿ֲ½-׳³ג€“׳³ֲ¨׳³ג€ ׳³ֲ׳³ֳ—׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ", callback_data="adm:home")],
    ])


def _kb_bot_detail(bot: dict) -> InlineKeyboardMarkup:
    bot_id = bot["id"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="׳ ֲג€ג€ ׳³ֲ¡׳³ג€¢׳³ג€˜׳³ג€˜ ׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ", callback_data=f"adm:rot:{bot_id}")],
        [InlineKeyboardButton(text="׳ ֲג€ֲ Swap mode (׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ ׳³ֲ©׳³ֲ ׳³ג€˜׳³ג€¢׳³ֻ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨)", callback_data=f"adm:swap:{bot_id}")],
        [InlineKeyboardButton(text="׳’ֲ¬ג€¦ ׳³ֲ׳³ֲ¨׳³ֲ©׳³ג„¢׳³ֲ׳³ֳ— ׳³ג€˜׳³ג€¢׳³ֻ׳³ג„¢׳³ֲ", callback_data="adm:tokens:0"),
         InlineKeyboardButton(text="׳ ֲֲֲ  ׳³ֳ—׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ", callback_data="adm:home")],
    ])


def _kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="׳’ֲֲ ׳³ג€˜׳³ֻ׳³ֲ", callback_data="adm:cancel")],
    ])


def _kb_confirm_critical(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="׳’ֲג€¦ ׳³ֲ׳³ֲ©׳³ֲ¨ ׳³ג€¢׳³ֲ¡׳³ג€¢׳³ג€˜׳³ג€˜ (60s)", callback_data=f"adm:confirm:{bot_id}")],
        [InlineKeyboardButton(text="׳’ֲֲ ׳³ג€˜׳³ֻ׳³ֲ", callback_data="adm:cancel")],
    ])


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Render helpers ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬


def _sort_bots(bots: list[dict]) -> list[dict]:
    """Critical׳’ג€ ג€™Low, then by stale-days desc (most stale first)."""
    def key(b):
        tier_rank = TIER_ORDER.get((b.get("tier") or "medium"), 9)
        days = _days_since(b.get("last_rotated_at")) or 9999
        return (tier_rank, -days)
    return sorted(bots, key=key)


def _render_bot_detail(bot: dict) -> str:
    tier = (bot.get("tier") or "medium").lower()
    emoji = TIER_EMOJI.get(tier, "")
    days = _days_since(bot.get("last_rotated_at"))
    stale = _stale_label(days)
    last_iso = (bot.get("last_rotated_at") or "")[:10] or "׳’ג‚¬ג€"
    note = bot.get("notes") or ""
    confirm_note = " (׳³ג„¢׳³ֲ© ׳³ֲ׳³ג€׳³ג€™׳³ג„¢׳³ג€˜ ׳³ֲ׳³ג€÷׳³ג‚×׳³ֳ—׳³ג€¢׳³ֲ¨ confirm 60s)" if tier == "critical" else ""
    return (
        f"׳ ֲג‚×ג€“ *{bot['name']}*\n"
        f"Handle: `{bot['handle']}`\n"
        f"Env: `{bot['env_var']}`\n"
        f"Service: `{bot.get('service') or '׳’ג‚¬ג€'}`\n"
        f"Tier: {emoji} *{tier.upper()}*{confirm_note}\n"
        f"Last rotated: `{last_iso}` ײ²ֲ· {stale}\n"
        + (f"Notes: _{note}_\n" if note else "")
    )


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Handlers ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬


def register(dp: Dispatcher, auth_module) -> None:

    @dp.message(Command("admin"))
    async def cmd_admin(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        await msg.answer(
            "׳ ֲֲג€÷ *׳³ג‚×׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ג€׳³ֲ׳³ג„¢׳³ֲ SLH Spark*\n_׳³ג€˜׳ֲ¿ֲ½-׳³ֲ¨ ׳³ֲ׳³ג€“׳³ג€¢׳³ֲ¨:_",
            reply_markup=_kb_main(),
        )

    @dp.callback_query(F.data == "adm:home")
    async def cb_home(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        try:
            await cb.message.edit_text("׳ ֲֲג€÷ *׳³ג‚×׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ג€׳³ֲ׳³ג„¢׳³ֲ SLH Spark*\n_׳³ג€˜׳ֲ¿ֲ½-׳³ֲ¨ ׳³ֲ׳³ג€“׳³ג€¢׳³ֲ¨:_",
                                       reply_markup=_kb_main())
        except Exception:
            await cb.message.answer("׳ ֲֲג€÷ *׳³ג‚×׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ג€׳³ֲ׳³ג„¢׳³ֲ SLH Spark*\n_׳³ג€˜׳ֲ¿ֲ½-׳³ֲ¨ ׳³ֲ׳³ג€“׳³ג€¢׳³ֲ¨:_",
                                    reply_markup=_kb_main())
        await cb.answer()

    @dp.callback_query(F.data.startswith("adm:tokens:"))
    async def cb_tokens(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        page = int(cb.data.split(":")[2]) if cb.data.count(":") >= 2 else 0
        try:
            j = await _api_get("/api/admin/bots")
        except Exception as e:
            await cb.message.edit_text(f"׳’ֲֲ ׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€ ׳³ג€˜׳³ֻ׳³ֲ¢׳³ג„¢׳³ֲ ׳³ֳ— ׳³ג€˜׳³ג€¢׳³ֻ׳³ג„¢׳³ֲ:\n`{str(e)[:300]}`",
                                       reply_markup=_kb_back_home())
            await cb.answer()
            return
        bots = _sort_bots(j.get("bots") or [])
        total = len(bots)
        start = page * PAGE_SIZE
        page_bots = bots[start:start + PAGE_SIZE]

        rows: list[list[InlineKeyboardButton]] = []
        for b in page_bots:
            tier = (b.get("tier") or "medium").lower()
            emoji = TIER_EMOJI.get(tier, "")
            days = _days_since(b.get("last_rotated_at"))
            stale = _stale_label(days)
            label = f"{emoji} {b['handle']} ײ²ֲ· {stale}"
            if len(label) > 60:
                label = label[:58] + "׳’ג‚¬ֲ¦"
            rows.append([InlineKeyboardButton(text=label, callback_data=f"adm:bot:{b['id']}")])
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="׳’ֲ¬ג€¦ prev", callback_data=f"adm:tokens:{page-1}"))
        if start + PAGE_SIZE < total:
            nav.append(InlineKeyboardButton(text="next ׳’ֲֲ¡", callback_data=f"adm:tokens:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton(text="׳ ֲֲֲ  ׳³ֳ—׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ", callback_data="adm:home")])

        last_page = max(0, (total - 1) // PAGE_SIZE)
        text = (
            f"׳ ֲג€ֲ *Bots {start+1}׳’ג‚¬ג€{min(start+PAGE_SIZE, total)} ׳³ֲ׳³ֳ—׳³ג€¢׳³ֲ {total}* "
            f"(׳³ֲ¢׳³ֲ׳³ג€¢׳³ג€ {page+1}/{last_page+1})\n"
            f"_׳³ֲ׳³ג„¢׳³ג€¢׳³ֲ: tier ׳’ג€ ג€ ׳³ג€¢׳³ֲ׳³ג€“ staleness ׳’ג€ ג€_"
        )
        try:
            await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        except Exception:
            await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        await cb.answer()

    @dp.callback_query(F.data.startswith("adm:bot:"))
    async def cb_bot(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        bot_id = int(cb.data.split(":")[2])
        try:
            j = await _api_get("/api/admin/bots")
        except Exception as e:
            await cb.message.edit_text(f"׳’ֲֲ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        bot = next((b for b in (j.get("bots") or []) if b.get("id") == bot_id), None)
        if not bot:
            await cb.answer("׳³ג€׳³ג€˜׳³ג€¢׳³ֻ ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ", show_alert=True)
            return
        await cb.message.edit_text(_render_bot_detail(bot), reply_markup=_kb_bot_detail(bot))
        await cb.answer()

    async def _start_rotate_flow(cb: CallbackQuery, swap: bool):
        bot_id = int(cb.data.split(":")[2])
        try:
            j = await _api_get("/api/admin/bots")
        except Exception as e:
            await cb.message.edit_text(f"׳’ֲֲ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        bot = next((b for b in (j.get("bots") or []) if b.get("id") == bot_id), None)
        if not bot:
            await cb.answer("׳³ג€׳³ג€˜׳³ג€¢׳³ֻ ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ", show_alert=True)
            return
        # GC stale pending
        now = time.time()
        for uid, st in list(_PENDING.items()):
            if now - st["started_at"] > PENDING_TTL_SECONDS:
                del _PENDING[uid]
        _PENDING[cb.from_user.id] = {
            "bot": bot,
            "swap": swap,
            "confirm_token": None,
            "started_at": now,
            "menu_msg_id": cb.message.message_id,
        }
        prompt = (
            f"׳ ֲג€ֲ¨ *׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜ {bot['handle']}*\n\n"
            f"׳³ֲ©׳³ֲ׳ֲ¿ֲ½- ׳³ֲ׳³ֳ— *׳³ג€׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ ׳³ג€׳ֲ¿ֲ½-׳³ג€׳³ֲ© ׳³ֲ-BotFather* ׳³ג€˜׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€ ׳³ג€׳³ג€˜׳³ֲ׳³ג€.\n"
            f"׳’ֲֲ ׳ֲ¸ֲ ׳³ג€׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€ ׳³ֲ©׳³ֲ׳³ֲ ׳³ֳ—׳³ג„¢׳³ֲ׳ֲ¿ֲ½-׳³ֲ§ ׳³ֲ׳³ג€¢׳³ֻ׳³ג€¢׳³ֲ׳³ֻ׳³ג„¢׳³ֳ— ׳³ֲ׳³ג„¢׳³ג€ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨׳³ג„¢ ׳³ֲ§׳³ג€˜׳³ֲ׳³ג€ (׳³ֲ׳³ג€˜׳³ֻ׳ֲ¿ֲ½-׳³ג€).\n"
            f"׳’ֲֲ± ׳³ג„¢׳³ֲ© ׳³ֲ׳³ֲ {PENDING_TTL_SECONDS // 60} ׳³ג€׳³ֲ§׳³ג€¢׳³ֳ—.\n"
            + ("\n׳ ֲג€ֲ *Swap mode:* ׳³ג€׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ ׳³ג„¢׳³ג€÷׳³ג€¢׳³ֲ ׳³ֲ׳³ג€׳³ג„¢׳³ג€¢׳³ֳ— ׳³ֲ©׳³ֲ ׳³ג€˜׳³ג€¢׳³ֻ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨ ׳’ג‚¬ג€ ׳³ג€׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֳ— ׳³ג„¢׳³ֲ¢׳³ג€˜׳³ג€¢׳³ֲ¨ ׳³ֲ׳³ֲ׳³ג„¢׳³ג€¢." if swap else "")
        )
        try:
            await cb.message.edit_text(prompt, reply_markup=_kb_cancel())
        except Exception:
            await cb.message.answer(prompt, reply_markup=_kb_cancel())
        await cb.answer()

    @dp.callback_query(F.data.startswith("adm:rot:"))
    async def cb_rot(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        await _start_rotate_flow(cb, swap=False)

    @dp.callback_query(F.data.startswith("adm:swap:"))
    async def cb_swap(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        await _start_rotate_flow(cb, swap=True)

    @dp.callback_query(F.data == "adm:cancel")
    async def cb_cancel(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        _PENDING.pop(cb.from_user.id, None)
        try:
            await cb.message.edit_text("׳’ֲֲ ׳³ג€˜׳³ג€¢׳³ֻ׳³ֲ. ׳ֲ¿ֲ½-׳³ג€¢׳³ג€“׳³ֲ¨ ׳³ֲ׳³ֳ—׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ.", reply_markup=_kb_main())
        except Exception:
            await cb.message.answer("׳’ֲֲ ׳³ג€˜׳³ג€¢׳³ֻ׳³ֲ.", reply_markup=_kb_main())
        await cb.answer("׳³ג€˜׳³ג€¢׳³ֻ׳³ֲ")

    @dp.callback_query(F.data.startswith("adm:confirm:"))
    async def cb_confirm(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        state = _PENDING.get(cb.from_user.id)
        if not state or not state.get("confirm_token") or not state.get("pending_token"):
            await cb.answer("׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜ ׳³ֲ׳³ֲ׳³ֳ—׳³ג„¢׳³ֲ ׳³ֲ׳³ֲ׳³ג„¢׳³ֲ©׳³ג€¢׳³ֲ¨ (׳³ג‚×׳³ג€™ ׳³ֳ—׳³ג€¢׳³ֲ§׳³ֲ£?)", show_alert=True)
            _PENDING.pop(cb.from_user.id, None)
            return
        await cb.answer("׳’ֲֲ³ ׳³ֲ׳³ֲ׳³ֲ©׳³ֲ¨ ׳³ג€¢׳³ֲ׳³ג€˜׳³ֲ¦׳³ֲ¢...")
        await _execute_pipeline(cb.message, cb.from_user.id, state)

    @dp.callback_query(F.data == "adm:status")
    async def cb_status(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        try:
            h = await _api_get("/api/admin/rotation-pipeline/health")
            stats = await _api_get("/api/admin/bots/stats")
        except Exception as e:
            await cb.message.edit_text(f"׳’ֲֲ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        by_tier = stats.get("by_tier") or {}
        text = (
            "׳ ֲג€ֲ *׳³ֲ׳³ֲ¦׳³ג€˜ Pipeline*\n"
            f"Config loaded: {'׳’ֲג€¦' if h.get('config_loaded') else '׳’ֲֲ'} "
            f"({h.get('config_entries')} entries)\n"
            f"Railway token: {'׳’ֲג€¦' if h.get('railway_token_ok') else '׳’ֲֲ'} "
            f"({h.get('railway_me_email') or h.get('railway_error') or '׳’ג‚¬ג€'})\n"
            f"Broadcast bot: {'׳’ֲג€¦' if h.get('broadcast_bot_token_set') else '׳’ֲֲ'}\n"
            f"Admin Telegrams: {h.get('admin_telegram_ids_count')}\n\n"
            f"׳ ֲג€ג€¹ *Bot fleet:* total={stats.get('total')}\n"
            f"  ׳ ֲֲֲ¨ critical={by_tier.get('critical', 0)} ײ²ֲ· "
            f"׳’ֲֲ ׳ֲ¸ֲ high={by_tier.get('high', 0)} ײ²ֲ· "
            f"׳ ֲג€ֲ¹ medium={by_tier.get('medium', 0)} ײ²ֲ· "
            f"׳’ֲֳ— low={by_tier.get('low', 0)}\n"
            f"  never_rotated={stats.get('never_rotated')}, "
            f"stale 90d={stats.get('stale_90d')}, "
            f"stale 180d={stats.get('stale_180d')}"
        )
        await cb.message.edit_text(text, reply_markup=_kb_back_home())
        await cb.answer()

    @dp.callback_query(F.data == "adm:hist")
    async def cb_hist(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        try:
            j = await _api_get("/api/admin/rotation-history?limit=10")
        except Exception as e:
            await cb.message.edit_text(f"׳’ֲֲ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        events = j.get("events") or []
        if not events:
            text = "׳ ֲג€ֲ *Audit log*\n_׳³ֲ¢׳³ג€׳³ג„¢׳³ג„¢׳³ֲ ׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜׳³ג„¢׳³ֲ ׳³ֲ׳³ֳ—׳³ג€¢׳³ֲ¢׳³ג€׳³ג„¢׳³ֲ._"
        else:
            lines = ["׳ ֲג€ֲ *10 ׳³ֲ׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֲ¢׳³ג„¢׳³ֲ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨׳³ג€¢׳³ֲ ׳³ג„¢׳³ֲ:*"]
            for ev in events:
                t = (ev.get("created_at") or "")[:19].replace("T", " ")
                action = (ev.get("action") or "").replace("secret.rotate.", "")
                rid = ev.get("resource_id") or "׳’ג‚¬ג€"
                meta = ev.get("metadata") or {}
                tier = meta.get("tier") or ""
                emoji = "׳’ֲג€¦" if action == "pushed" else ("׳’ֲֲ" if "fail" in action else "׳’ג‚¬ֲ¢")
                lines.append(f"{emoji} `{t}` ײ²ֲ· `{action}` ײ²ֲ· `{rid}` ײ²ֲ· {tier}")
            text = "\n".join(lines)
        await cb.message.edit_text(text, reply_markup=_kb_back_home())
        await cb.answer()

    @dp.callback_query(F.data == "adm:railway")
    async def cb_railway(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        text = (
            "׳ ֲֲג€ *Railway*\n"
            "׳³ג‚×׳³ֲ§׳³ג€¢׳³ג€׳³ג€¢׳³ֳ— ׳³ג€“׳³ֲ׳³ג„¢׳³ֲ ׳³ג€¢׳³ֳ— (׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ֲ¨׳³ג€™׳³ג„¢׳³ֲ, ׳³ֲ׳³ֲ inline):\n"
            "׳’ג‚¬ֲ¢ `/railway_status` ׳’ג‚¬ג€ ׳³ֲ׳³ֲ¦׳³ג€˜ ׳³ג€׳³ג‚×׳³ֲ¨׳³ג€¢׳³ג„¢׳³ֲ§׳³ֻ\n"
            "׳’ג‚¬ֲ¢ `/railway_list`   ׳’ג‚¬ג€ ׳³ג€÷׳³ֲ ׳³ג€׳³ג‚×׳³ֲ¨׳³ג€¢׳³ג„¢׳³ֲ§׳³ֻ׳³ג„¢׳³ֲ\n"
            "׳’ג‚¬ֲ¢ `/railway_vars <service>` ׳’ג‚¬ג€ ׳³ֲ©׳³ֲ׳³ג€¢׳³ֳ— ׳³ֲ׳³ֲ©׳³ֳ—׳³ֲ ׳³ג„¢׳³ֲ\n"
            "׳’ג‚¬ֲ¢ `/railway_logs <service>` ׳’ג‚¬ג€ ׳³ֲ׳³ג€¢׳³ג€™׳³ג„¢׳³ֲ\n"
            "׳’ג‚¬ֲ¢ `/railway_redeploy <service>` ׳’ג‚¬ג€ redeploy ׳³ג„¢׳³ג€׳³ֲ ׳³ג„¢"
        )
        await cb.message.edit_text(text, reply_markup=_kb_back_home())
        await cb.answer()

    # ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Token reception (text message handler) ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬
    # CRITICAL: this handler must ONLY match when a rotation flow is pending
    # for the sender. In aiogram 3.x, a matched handler consumes the message
    # ׳’ג‚¬ג€ it does NOT cascade to the next handler. So if we matched every text
    # message and returned early when no pending state exists, the AI text
    # handler in bot.py would never run.
    #
    # We use a callable filter that returns False unless the user has pending
    # state, which lets the message fall through to bot.py's on_text handler.

    def _has_pending_rotation(message: Message) -> bool:
        if message.from_user is None:
            return False
        st = _PENDING.get(message.from_user.id)
        if not st:
            return False
        # GC stale entries here too (cheap)
        if time.time() - st["started_at"] > PENDING_TTL_SECONDS:
            _PENDING.pop(message.from_user.id, None)
            return False
        return True

    @dp.message(F.text & ~F.text.startswith("/"), _has_pending_rotation)
    async def on_token_input(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            return
        state = _PENDING.get(msg.from_user.id)
        if not state:
            return  # race-defensive ׳’ג‚¬ג€ filter already checked
        text = (msg.text or "").strip()
        if not re.match(r"^\d+:[A-Za-z0-9_-]{30,}$", text):
            # Token-format check failed but flow is active ׳’ג‚¬ג€ guide the user
            # rather than silently swallowing or forwarding to the AI handler.
            await msg.answer(
                "׳’ֲֲ ׳ֲ¸ֲ ׳³ג€“׳³ג€ ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ¨׳³ֲ׳³ג€ ׳³ג€÷׳³ֲ׳³ג€¢ ׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ BotFather (׳³ג‚×׳³ג€¢׳³ֲ¨׳³ֲ׳³ֻ: `<digits>:<hash>`).\n"
                "׳³ֲ©׳³ֲ׳ֲ¿ֲ½- ׳³ֲ׳³ֳ— ׳³ג€׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ ׳³ֲ©׳³ג€¢׳³ג€˜, ׳³ֲ׳³ג€¢ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¥ ׳’ֲֲ ׳³ג€˜׳³ֻ׳³ֲ ׳³ג€˜׳³ֳ—׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ."
            )
            return

        # SECURITY: delete the user's message immediately so the token never
        # sits in chat history, even if the API call below fails.
        try:
            await msg.delete()
        except Exception as e:
            log.warning("could not delete token message: %s", e)

        state["pending_token"] = text
        await _execute_pipeline(msg, msg.from_user.id, state)


async def _execute_pipeline(host_msg: Message, user_id: int, state: dict) -> None:
    """Run the rotation pipeline for the given pending state. Streams updates
    by editing a single message instead of spamming new ones."""
    bot = state["bot"]
    token = state.get("pending_token") or ""
    swap = state.get("swap", False)
    confirm = state.get("confirm_token")

    # Status message ׳’ג‚¬ג€ start fresh, edit as we go
    progress = await host_msg.answer(
        f"׳’ֲֲ³ {('׳³ֲ׳³ֲ׳³ֲ©׳³ֲ¨ ׳³ג€¢' if confirm else '')}׳³ֲ©׳³ג€¢׳³ֲ׳ֲ¿ֲ½- ׳³ֲ׳³ֳ— ׳³ג€׳³ֻ׳³ג€¢׳³ֲ§׳³ֲ ׳³ֲ-pipeline׳’ג‚¬ֲ¦",
        reply_markup=_kb_cancel(),
    )

    payload = {
        "env_var": bot["env_var"],
        "new_token": token,
        "expect_handle": bot["handle"],
        "swap_mode": swap,
    }
    if confirm:
        payload["confirm_token"] = confirm

    status, j = await _api_post("/api/admin/rotate-bot-token-pipeline", payload)

    async def _edit(text: str, kb: Optional[InlineKeyboardMarkup] = None):
        try:
            await progress.edit_text(text, reply_markup=kb or _kb_back_home())
        except Exception:
            await progress.answer(text, reply_markup=kb or _kb_back_home())

    if j.get("needs_confirm"):
        state["confirm_token"] = j.get("confirm_token")
        # Don't keep the pending token in memory longer than necessary
        await _edit(
            f"׳ ֲג€ֲ *Critical tier ׳’ג‚¬ג€ ׳³ֲ׳³ג„¢׳³ֲ©׳³ג€¢׳³ֲ¨ ׳³ֲ ׳³ג€׳³ֲ¨׳³ֲ©*\n\n"
            f"`{bot['handle']}` ׳³ג€׳³ג€¢׳³ֲ tier=*critical*. "
            f"׳³ֲ׳ֲ¿ֲ½-׳³ֲ¥ ׳³ֲ¢׳³ֲ ׳³ג€׳³ג€÷׳³ג‚×׳³ֳ—׳³ג€¢׳³ֲ¨ ׳³ֳ—׳³ג€¢׳³ֲ {j.get('expires_in_seconds', 60)} ׳³ֲ©׳³ֲ ׳³ג„¢׳³ג€¢׳³ֳ— ׳³ֲ׳³ֲ׳³ג„¢׳³ֲ©׳³ג€¢׳³ֲ¨ ׳³ג€׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜.",
            _kb_confirm_critical(bot["id"]),
        )
        return

    if status != 200 or (status == 200 and not j.get("ok") and not j.get("phase")):
        detail = j.get("detail") or j.get("error") or json.dumps(j)[:300]
        # Scrub any token-shaped substring from server error text
        detail = re.sub(r"\d{8,12}:[A-Za-z0-9_\-]{30,}", "<TOKEN>", detail)
        _PENDING.pop(user_id, None)
        await _edit(f"׳’ֲֲ *׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜ ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ*\nHTTP {status}\n`{detail[:300]}`")
        return

    if j.get("phase") == "healthcheck_failed":
        _PENDING.pop(user_id, None)
        await _edit(
            f"׳ ֲֲֲ¨ *Healthcheck ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ*\n"
            f"Variable + redeploy ׳³ג€˜׳³ג€¢׳³ֲ¦׳³ֲ¢׳³ג€¢ ׳³ֲ׳³ֲ ׳³ג€׳³ג€˜׳³ג€¢׳³ֻ ׳³ֲ׳³ֲ ׳³ֲ׳³ג€™׳³ג„¢׳³ג€˜ ׳³ֲ-getMe.\n"
            f"Deploy: `{(j.get('deploy_id') or '')[:16]}`\n\n"
            f"_׳³ֲ ׳³ג€׳³ֲ¨׳³ֲ© ׳³ג€˜׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֲ¨ ׳³ג„¢׳³ג€׳³ֲ ׳³ג„¢ ׳³ג€˜-Railway logs._"
        )
        return

    if j.get("ok"):
        _PENDING.pop(user_id, None)
        last4 = j.get("last4") or "????"
        deploy = (j.get("deploy_id") or "")[:16]
        tg_username = j.get("tg_username") or "?"
        tier = j.get("tier") or "?"
        await _edit(
            f"׳’ֲג€¦ *׳³ֲ¡׳³ג„¢׳³ג€˜׳³ג€¢׳³ג€˜ ׳³ג€׳³ג€¢׳³ֲ©׳³ֲ׳³ֲ*\n\n"
            f"`{bot['handle']}` (env: `{bot['env_var']}`)\n"
            f"Tier: *{tier}* ײ²ֲ· Last4: `׳’ג‚¬ֲ¦{last4}`\n"
            f"Deploy: `{deploy}`\n"
            f"Verified: @{tg_username}\n\n"
            f"׳’ֲג€ Variable ׳³ֲ¢׳³ג€¢׳³ג€׳³ג€÷׳³ֲ ׳³ג€˜-Railway\n"
            f"׳’ֲג€ Redeploy ׳³ג€׳³ג€¢׳³ג‚×׳³ֲ¢׳³ֲ\n"
            f"׳’ֲג€ Healthcheck ׳³ֲ¢׳³ג€˜׳³ֲ¨\n"
            f"׳’ֲג€ setMyCommands ׳³ֲ¡׳³ג€¢׳³ֲ ׳³ג€÷׳³ֲ¨׳³ֲ\n"
            f"׳’ֲג€ Broadcast ׳³ֲ׳³ֲ׳³ג€׳³ֲ׳³ג„¢׳³ֲ ׳³ג„¢׳³ֲ ׳³ֲ ׳³ֲ©׳³ֲ׳ֲ¿ֲ½-"
        )
        return

    _PENDING.pop(user_id, None)
    await _edit(f"׳’ֲֲ ׳ֲ¸ֲ ׳³ֳ—׳³ֲ©׳³ג€¢׳³ג€˜׳³ג€ ׳³ֲ׳³ֲ ׳³ֲ¦׳³ג‚×׳³ג€¢׳³ג„¢׳³ג€:\n`{json.dumps(j)[:300]}`")


# Convenience export so bot.py can `import rotation_panel; rotation_panel.register(dp, auth)`
__all__ = ["register"]

