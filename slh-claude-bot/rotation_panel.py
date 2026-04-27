"""SLH Token Rotation — Telegram admin panel for @SLH_Claude_bot.

Mirrors /admin/tokens.html on Telegram with inline keyboards. Same backend
endpoint (POST /api/admin/rotate-bot-token-pipeline) — bot is just a wrapper.

Commands:
    /admin              → main menu (Tokens / Railway / Status / Audit)

Callbacks (data prefixes):
    adm:home            → show main menu
    adm:tokens:<page>   → show paginated bot list
    adm:bot:<id>        → show bot detail card
    adm:rot:<id>        → start rotate flow for bot
    adm:swap:<id>       → start rotate flow with swap_mode=true
    adm:hist            → show last 10 audit events
    adm:status          → pipeline-health snapshot
    adm:railway         → bridge to railway_ops dashboard
    adm:cancel          → cancel pending token-input flow

Auth: shared with bot.py via auth.is_authorized — only Osif's IDs reach here.

In-memory state: pending token-input requests per user (TTL 5 min). Resets on
restart, which is fine — a stale flow just times out and the user retries.
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
TIER_EMOJI = {"critical": "🚨", "high": "⚠️", "medium": "🔹", "low": "⚪"}
TIER_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PENDING_TTL_SECONDS = 300  # 5 min for user to send the new token

# Per-user pending flow state. Cleared on success/cancel/timeout.
# Key: telegram_user_id, Value: {bot, swap, confirm_token, message_id, started_at}
_PENDING: dict[int, dict] = {}


# ─── HTTP helpers ──────────────────────────────────────────────────────────


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
        return "❓ never"
    if days > 180:
        return f"🚨 {days}d"
    if days > 90:
        return f"⚠️ {days}d"
    return f"✅ {days}d"


# ─── Keyboards ─────────────────────────────────────────────────────────────


def _kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Tokens",  callback_data="adm:tokens:0"),
         InlineKeyboardButton(text="🚂 Railway", callback_data="adm:railway")],
        [InlineKeyboardButton(text="📊 Pipeline status", callback_data="adm:status"),
         InlineKeyboardButton(text="📜 Audit",   callback_data="adm:hist")],
    ])


def _kb_back_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ חזרה לתפריט", callback_data="adm:home")],
    ])


def _kb_bot_detail(bot: dict) -> InlineKeyboardMarkup:
    bot_id = bot["id"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 סובב טוקן", callback_data=f"adm:rot:{bot_id}")],
        [InlineKeyboardButton(text="🔁 Swap mode (טוקן של בוט אחר)", callback_data=f"adm:swap:{bot_id}")],
        [InlineKeyboardButton(text="⬅ לרשימת בוטים", callback_data="adm:tokens:0"),
         InlineKeyboardButton(text="🏠 תפריט", callback_data="adm:home")],
    ])


def _kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ בטל", callback_data="adm:cancel")],
    ])


def _kb_confirm_critical(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ אשר וסובב (60s)", callback_data=f"adm:confirm:{bot_id}")],
        [InlineKeyboardButton(text="❌ בטל", callback_data="adm:cancel")],
    ])


# ─── Render helpers ────────────────────────────────────────────────────────


def _sort_bots(bots: list[dict]) -> list[dict]:
    """Critical→Low, then by stale-days desc (most stale first)."""
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
    last_iso = (bot.get("last_rotated_at") or "")[:10] or "—"
    note = bot.get("notes") or ""
    confirm_note = " (יש להגיב לכפתור confirm 60s)" if tier == "critical" else ""
    return (
        f"🤖 *{bot['name']}*\n"
        f"Handle: `{bot['handle']}`\n"
        f"Env: `{bot['env_var']}`\n"
        f"Service: `{bot.get('service') or '—'}`\n"
        f"Tier: {emoji} *{tier.upper()}*{confirm_note}\n"
        f"Last rotated: `{last_iso}` · {stale}\n"
        + (f"Notes: _{note}_\n" if note else "")
    )


# ─── Handlers ──────────────────────────────────────────────────────────────


def register(dp: Dispatcher, auth_module) -> None:

    @dp.message(Command("admin"))
    async def cmd_admin(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        await msg.answer(
            "🎛 *פאנל אדמין SLH Spark*\n_בחר אזור:_",
            reply_markup=_kb_main(),
        )

    @dp.callback_query(F.data == "adm:home")
    async def cb_home(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        try:
            await cb.message.edit_text("🎛 *פאנל אדמין SLH Spark*\n_בחר אזור:_",
                                       reply_markup=_kb_main())
        except Exception:
            await cb.message.answer("🎛 *פאנל אדמין SLH Spark*\n_בחר אזור:_",
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
            await cb.message.edit_text(f"❌ שגיאה בטעינת בוטים:\n`{str(e)[:300]}`",
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
            label = f"{emoji} {b['handle']} · {stale}"
            if len(label) > 60:
                label = label[:58] + "…"
            rows.append([InlineKeyboardButton(text=label, callback_data=f"adm:bot:{b['id']}")])
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="⬅ prev", callback_data=f"adm:tokens:{page-1}"))
        if start + PAGE_SIZE < total:
            nav.append(InlineKeyboardButton(text="next ➡", callback_data=f"adm:tokens:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton(text="🏠 תפריט", callback_data="adm:home")])

        last_page = max(0, (total - 1) // PAGE_SIZE)
        text = (
            f"🔐 *Bots {start+1}–{min(start+PAGE_SIZE, total)} מתוך {total}* "
            f"(עמוד {page+1}/{last_page+1})\n"
            f"_מיון: tier ↓ ואז staleness ↓_"
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
            await cb.message.edit_text(f"❌ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        bot = next((b for b in (j.get("bots") or []) if b.get("id") == bot_id), None)
        if not bot:
            await cb.answer("הבוט לא נמצא", show_alert=True)
            return
        await cb.message.edit_text(_render_bot_detail(bot), reply_markup=_kb_bot_detail(bot))
        await cb.answer()

    async def _start_rotate_flow(cb: CallbackQuery, swap: bool):
        bot_id = int(cb.data.split(":")[2])
        try:
            j = await _api_get("/api/admin/bots")
        except Exception as e:
            await cb.message.edit_text(f"❌ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        bot = next((b for b in (j.get("bots") or []) if b.get("id") == bot_id), None)
        if not bot:
            await cb.answer("הבוט לא נמצא", show_alert=True)
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
            f"📨 *סיבוב {bot['handle']}*\n\n"
            f"שלח את *הטוקן החדש מ-BotFather* בהודעה הבאה.\n"
            f"⚠️ ההודעה שלך תימחק אוטומטית מיד אחרי קבלה (אבטחה).\n"
            f"⏱ יש לך {PENDING_TTL_SECONDS // 60} דקות.\n"
            + ("\n🔁 *Swap mode:* הטוקן יכול להיות של בוט אחר — השירות יעבור אליו." if swap else "")
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
            await cb.message.edit_text("❌ בוטל. חוזר לתפריט.", reply_markup=_kb_main())
        except Exception:
            await cb.message.answer("❌ בוטל.", reply_markup=_kb_main())
        await cb.answer("בוטל")

    @dp.callback_query(F.data.startswith("adm:confirm:"))
    async def cb_confirm(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        state = _PENDING.get(cb.from_user.id)
        if not state or not state.get("confirm_token") or not state.get("pending_token"):
            await cb.answer("אין סיבוב ממתין לאישור (פג תוקף?)", show_alert=True)
            _PENDING.pop(cb.from_user.id, None)
            return
        await cb.answer("⏳ מאשר ומבצע...")
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
            await cb.message.edit_text(f"❌ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        by_tier = stats.get("by_tier") or {}
        text = (
            "📊 *מצב Pipeline*\n"
            f"Config loaded: {'✅' if h.get('config_loaded') else '❌'} "
            f"({h.get('config_entries')} entries)\n"
            f"Railway token: {'✅' if h.get('railway_token_ok') else '❌'} "
            f"({h.get('railway_me_email') or h.get('railway_error') or '—'})\n"
            f"Broadcast bot: {'✅' if h.get('broadcast_bot_token_set') else '❌'}\n"
            f"Admin Telegrams: {h.get('admin_telegram_ids_count')}\n\n"
            f"📋 *Bot fleet:* total={stats.get('total')}\n"
            f"  🚨 critical={by_tier.get('critical', 0)} · "
            f"⚠️ high={by_tier.get('high', 0)} · "
            f"🔹 medium={by_tier.get('medium', 0)} · "
            f"⚪ low={by_tier.get('low', 0)}\n"
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
            await cb.message.edit_text(f"❌ {str(e)[:300]}", reply_markup=_kb_back_home())
            await cb.answer()
            return
        events = j.get("events") or []
        if not events:
            text = "📜 *Audit log*\n_עדיין אין סיבובים מתועדים._"
        else:
            lines = ["📜 *10 אירועים אחרונים:*"]
            for ev in events:
                t = (ev.get("created_at") or "")[:19].replace("T", " ")
                action = (ev.get("action") or "").replace("secret.rotate.", "")
                rid = ev.get("resource_id") or "—"
                meta = ev.get("metadata") or {}
                tier = meta.get("tier") or ""
                emoji = "✅" if action == "pushed" else ("❌" if "fail" in action else "•")
                lines.append(f"{emoji} `{t}` · `{action}` · `{rid}` · {tier}")
            text = "\n".join(lines)
        await cb.message.edit_text(text, reply_markup=_kb_back_home())
        await cb.answer()

    @dp.callback_query(F.data == "adm:railway")
    async def cb_railway(cb: CallbackQuery):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("Unauthorized", show_alert=True)
            return
        text = (
            "🚂 *Railway*\n"
            "פקודות זמינות (טקסט רגיל, לא inline):\n"
            "• `/railway_status` — מצב הפרויקט\n"
            "• `/railway_list`   — כל הפרויקטים\n"
            "• `/railway_vars <service>` — שמות משתנים\n"
            "• `/railway_logs <service>` — לוגים\n"
            "• `/railway_redeploy <service>` — redeploy ידני"
        )
        await cb.message.edit_text(text, reply_markup=_kb_back_home())
        await cb.answer()

    # ─── Token reception (text message handler) ────────────────────────────
    # CRITICAL: this handler must ONLY match when a rotation flow is pending
    # for the sender. In aiogram 3.x, a matched handler consumes the message
    # — it does NOT cascade to the next handler. So if we matched every text
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
            return  # race-defensive — filter already checked
        text = (msg.text or "").strip()
        if not re.match(r"^\d+:[A-Za-z0-9_-]{30,}$", text):
            # Token-format check failed but flow is active — guide the user
            # rather than silently swallowing or forwarding to the AI handler.
            await msg.answer(
                "⚠️ זה לא נראה כמו טוקן BotFather (פורמט: `<digits>:<hash>`).\n"
                "שלח את הטוקן שוב, או לחץ ❌ בטל בתפריט."
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

    # Status message — start fresh, edit as we go
    progress = await host_msg.answer(
        f"⏳ {('מאשר ו' if confirm else '')}שולח את הטוקן ל-pipeline…",
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
            f"🔐 *Critical tier — אישור נדרש*\n\n"
            f"`{bot['handle']}` הוא tier=*critical*. "
            f"לחץ על הכפתור תוך {j.get('expires_in_seconds', 60)} שניות לאישור הסיבוב.",
            _kb_confirm_critical(bot["id"]),
        )
        return

    if status != 200 or (status == 200 and not j.get("ok") and not j.get("phase")):
        detail = j.get("detail") or j.get("error") or json.dumps(j)[:300]
        # Scrub any token-shaped substring from server error text
        detail = re.sub(r"\d{8,12}:[A-Za-z0-9_\-]{30,}", "<TOKEN>", detail)
        _PENDING.pop(user_id, None)
        await _edit(f"❌ *סיבוב נכשל*\nHTTP {status}\n`{detail[:300]}`")
        return

    if j.get("phase") == "healthcheck_failed":
        _PENDING.pop(user_id, None)
        await _edit(
            f"🚨 *Healthcheck נכשל*\n"
            f"Variable + redeploy בוצעו אך הבוט לא מגיב ל-getMe.\n"
            f"Deploy: `{(j.get('deploy_id') or '')[:16]}`\n\n"
            f"_נדרש בירור ידני ב-Railway logs._"
        )
        return

    if j.get("ok"):
        _PENDING.pop(user_id, None)
        last4 = j.get("last4") or "????"
        deploy = (j.get("deploy_id") or "")[:16]
        tg_username = j.get("tg_username") or "?"
        tier = j.get("tier") or "?"
        await _edit(
            f"✅ *סיבוב הושלם*\n\n"
            f"`{bot['handle']}` (env: `{bot['env_var']}`)\n"
            f"Tier: *{tier}* · Last4: `…{last4}`\n"
            f"Deploy: `{deploy}`\n"
            f"Verified: @{tg_username}\n\n"
            f"✓ Variable עודכן ב-Railway\n"
            f"✓ Redeploy הופעל\n"
            f"✓ Healthcheck עבר\n"
            f"✓ setMyCommands סונכרן\n"
            f"✓ Broadcast לאדמינים נשלח"
        )
        return

    _PENDING.pop(user_id, None)
    await _edit(f"⚠️ תשובה לא צפויה:\n`{json.dumps(j)[:300]}`")


# Convenience export so bot.py can `import rotation_panel; rotation_panel.register(dp, auth)`
__all__ = ["register"]
