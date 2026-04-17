"""
@G4meb0t_bot_bot — SLH Dating Telegram bot
============================================
Consumes the /api/dating/* endpoints. No local DB — everything via SLH API.

Commands:
  /start        — welcome + age gate
  /profile      — view/edit your profile (redirects to web for full edit)
  /match        — get next candidate
  /like         — like current candidate (after /match)
  /pass         — pass on current candidate
  /matches      — list mutual matches
  /help         — commands
  /settings     — language, notifications, pause

Deploy:
  Env: G4MEBOT_TOKEN (from BotFather)
  Env: SLH_API (default: https://slh-api-production.up.railway.app)
  Run: python g4mebot/bot.py
  Or:  docker run via docker-compose.yml entry
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("g4mebot")

TOKEN = os.getenv("G4MEBOT_TOKEN", "").strip()
SLH_API = os.getenv("SLH_API", "https://slh-api-production.up.railway.app").rstrip("/")
SITE = os.getenv("SLH_SITE", "https://slh-nft.com").rstrip("/")
BOT_USERNAME = os.getenv("G4MEBOT_USERNAME", "G4meb0t_bot_bot").lstrip("@")

if not TOKEN:
    raise SystemExit("G4MEBOT_TOKEN env var is required")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# In-memory session state per user (candidate currently shown + referral source)
USER_STATE: dict[int, dict] = {}


def web_url(path: str, tg_id: int | None = None) -> str:
    """Build a deep-link that keeps the bot and site in sync for a given user."""
    sep = "&" if "?" in path else "?"
    base = f"{SITE}{path}"
    if tg_id is None:
        return base
    return f"{base}{sep}tg_id={tg_id}&src=bot"


class ProfileWizard(StatesGroup):
    waiting_age = State()
    waiting_name = State()
    waiting_city = State()
    waiting_bio = State()


async def api_get(path: str) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.get(SLH_API + path, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return await r.json()


async def api_post(path: str, body: dict) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(SLH_API + path, json=body, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return await r.json()


def age_gate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ כן, 18+", callback_data="age:ok"),
            InlineKeyboardButton(text="❌ לא", callback_data="age:no"),
        ]
    ])


def main_menu(tg_id: int | None = None) -> InlineKeyboardMarkup:
    dating_url = web_url("/dating.html", tg_id)
    profile_url = web_url("/profile.html", tg_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 מצא התאמה", callback_data="cmd:match")],
        [InlineKeyboardButton(text="💘 ההתאמות שלי", callback_data="cmd:matches")],
        [InlineKeyboardButton(text="🔗 הזמן חברים", callback_data="cmd:share")],
        [InlineKeyboardButton(text="👤 פרופיל (עריכה באתר)", url=dating_url)],
        [InlineKeyboardButton(text="🌐 אזור אישי באתר", url=profile_url)],
        [InlineKeyboardButton(text="❓ עזרה", callback_data="cmd:help")],
    ])


def candidate_keyboard(cand_uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💔 דלג", callback_data=f"act:pass:{cand_uid}"),
            InlineKeyboardButton(text="❤️ לייק", callback_data=f"act:like:{cand_uid}"),
            InlineKeyboardButton(text="⭐ Super", callback_data=f"act:superlike:{cand_uid}"),
        ],
        [InlineKeyboardButton(text="🔍 הבא", callback_data="cmd:match")],
    ])


WELCOME = (
    "💘 ברוכים הבאים ל‑SLH Dating\n\n"
    "זה לא Tinder. זה קהילה של אנשים עם ערכים:\n"
    "• מומחים מאומתים\n"
    "• הכרויות רציניות\n"
    "• תחומי עניין עמוקים\n\n"
    "השירות ל‑18+ בלבד. האם אתה/את מעל גיל 18?"
)


@dp.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject | None = None):
    # Block the family minor immediately
    if m.from_user.id == 6466974138:
        await m.answer("⚠ שירות זה מיועד למשתמשים מעל גיל 18 בלבד. צור קשר עם אוסיף לעזרה.")
        return

    # Referral tracking: /start <ref_code>  — ref_code is inviter's tg_id
    ref_raw = (command.args if command else None) or ""
    ref_raw = ref_raw.strip()
    if ref_raw.isdigit() and int(ref_raw) != m.from_user.id:
        USER_STATE.setdefault(m.from_user.id, {})["referred_by"] = int(ref_raw)
        try:
            await api_post("/api/dating/referral", {
                "inviter_tg_id": int(ref_raw),
                "invitee_tg_id": m.from_user.id,
                "invitee_username": m.from_user.username or "",
            })
        except Exception:
            logger.warning("Referral register failed (non-fatal)", exc_info=True)

    await m.answer(WELCOME, reply_markup=age_gate_keyboard())


@dp.callback_query(F.data.startswith("age:"))
async def cb_age(c: CallbackQuery):
    if c.data == "age:no":
        await c.message.edit_text("עלית על כפתור 'לא'. חזור לאתר SLH הראשי: https://slh-nft.com")
        return
    # Check if profile exists
    profile = await api_get(f"/api/dating/profile/{c.from_user.id}")
    if profile.get("exists"):
        await c.message.edit_text(
            f"ברוך הבא, {profile.get('display_name','חבר')}! הפרופיל שלך פעיל.\n\nמה לעשות?",
            reply_markup=main_menu(c.from_user.id),
        )
    else:
        await c.message.edit_text(
            "נהדר! כדי להתחיל — צור פרופיל באתר:\n\n"
            f"👉 {web_url('/dating.html', c.from_user.id)}\n\n"
            "אחרי שתשמור פרופיל, חזור לכאן וכתוב /match כדי למצוא התאמות.",
            reply_markup=main_menu(c.from_user.id),
        )
    await c.answer()


@dp.callback_query(F.data == "cmd:match")
@dp.message(Command("match"))
async def show_candidate(event):
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        reply = event.message.answer
        await event.answer()
    else:
        user_id = event.from_user.id
        reply = event.answer

    # Check profile exists
    profile = await api_get(f"/api/dating/profile/{user_id}")
    if not profile.get("exists"):
        await reply(
            "עוד לא יצרת פרופיל. לחץ כדי ליצור:\n"
            "👉 https://slh-nft.com/dating.html",
        )
        return

    # Fetch next candidate
    res = await api_post("/api/dating/match/candidates", {"user_id": user_id, "limit": 1})
    cands = res.get("candidates", [])
    if not cands:
        await reply("אין מועמדים חדשים כרגע. חזור מאוחר יותר, או כתוב /matches.")
        return

    c = cands[0]
    USER_STATE[user_id] = {"current_candidate": c["user_id"]}
    text = (
        f"👤 *{c['display_name']}* · {c['age']}\n"
        f"📍 {c.get('city') or '—'} · {'✓ מאומת' if c.get('verified') else ''}\n\n"
        f"{c.get('bio') or '(אין ביו)'}\n\n"
        f"🎯 {c.get('overlap_count', 0)} תחומי עניין משותפים"
    )
    await reply(text, reply_markup=candidate_keyboard(c["user_id"]), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("act:"))
async def cb_action(c: CallbackQuery):
    _, action, target_uid = c.data.split(":")
    target_uid = int(target_uid)
    res = await api_post("/api/dating/match/action", {
        "from_user_id": c.from_user.id,
        "to_user_id": target_uid,
        "action": action,
    })
    if res.get("is_match"):
        # Fetch the matched profile
        pub = await api_get(f"/api/dating/profile/{target_uid}/public")
        tg = pub.get("tg_username")
        tg_line = f"\n💬 שלח הודעה: t.me/{tg}" if tg else "\nאין לו username בטלגרם."
        await c.answer("🎉 התאמה הדדית!", show_alert=True)
        await c.message.answer(
            f"🎉 *התאמה הדדית עם {pub.get('display_name')}!*\n"
            f"{pub.get('bio') or ''}\n{tg_line}",
            parse_mode="Markdown",
        )
    else:
        emoji = {"like": "❤️", "pass": "💔", "superlike": "⭐"}.get(action, "✓")
        await c.answer(f"{emoji} נשמר")
    # Auto-show next
    await show_candidate(c)


@dp.callback_query(F.data == "cmd:matches")
@dp.message(Command("matches"))
async def show_matches(event):
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        reply = event.message.answer
        await event.answer()
    else:
        user_id = event.from_user.id
        reply = event.answer

    res = await api_get(f"/api/dating/matches/{user_id}")
    matches = res.get("matches", [])
    if not matches:
        await reply("עדיין אין התאמות הדדיות. המשך לחפש עם /match.")
        return

    lines = ["💘 *ההתאמות שלך:*\n"]
    for m in matches[:10]:
        tg = f" · t.me/{m['tg_username']}" if m.get("tg_username") else ""
        verified = " ✓" if m.get("verified") else ""
        lines.append(f"• {m['display_name']} · {m['age']}{verified}{tg}")
    await reply("\n".join(lines), parse_mode="Markdown")


@dp.callback_query(F.data == "cmd:help")
@dp.message(Command("help"))
async def cmd_help(event):
    uid = event.from_user.id
    text = (
        "📚 *פקודות:*\n"
        "/start — התחלה מחדש\n"
        "/match — מצא התאמה חדשה\n"
        "/matches — רשימת התאמות הדדיות\n"
        "/profile — תצוגת הפרופיל שלך + לינק לעריכה\n"
        "/share — הזמן חברים (+3 AIC עבורך)\n"
        "/site — לינקים לאזור האישי באתר\n"
        "/help — הודעה זו\n\n"
        "💡 עריכה מלאה של פרופיל, תמונות, תחומי עניין — רק באתר:\n"
        f"{web_url('/dating.html', uid)}\n"
        f"🌐 אזור אישי מלא: {web_url('/profile.html', uid)}"
    )
    kb = main_menu(uid)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)


@dp.message(Command("profile"))
async def cmd_profile(m: Message):
    profile = await api_get(f"/api/dating/profile/{m.from_user.id}")
    if not profile.get("exists"):
        await m.answer(
            f"עוד אין לך פרופיל. צור באתר: {web_url('/dating.html', m.from_user.id)}",
            reply_markup=main_menu(m.from_user.id),
        )
        return
    text = (
        f"👤 *{profile['display_name']}* · {profile['age']}\n"
        f"📍 {profile.get('city','—')}\n"
        f"🎯 {profile.get('looking_for','—')}\n"
        f"💼 {profile.get('profession','—')}\n\n"
        f"{profile.get('bio','(אין ביו)')}\n\n"
        f"🔗 עריכה: {web_url('/dating.html', m.from_user.id)}\n"
        f"🌐 אזור אישי: {web_url('/profile.html', m.from_user.id)}"
    )
    await m.answer(text, parse_mode="Markdown", reply_markup=main_menu(m.from_user.id))


@dp.callback_query(F.data == "cmd:share")
@dp.message(Command("share"))
async def cmd_share(event):
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        reply = event.message.answer
        await event.answer()
    else:
        user_id = event.from_user.id
        reply = event.answer

    invite = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    text = (
        "🎁 *הזמן חברים וצברו יחד מטבעות אהבה*\n\n"
        "שתף את הקישור האישי שלך:\n"
        f"`{invite}`\n\n"
        "כל מי שמצטרף דרך הקישור שלך:\n"
        "• אתה מקבל +3 AIC\n"
        "• הוא/היא מקבלים +5 AIC welcome\n"
        "• שניכם מופיעים ב‑leaderboard של ההפניות\n\n"
        "💡 טיפ: אפשר גם לשתף לפייסבוק/אינסטגרם/וואטסאפ דרך האתר."
    )
    share_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 שתף את הקישור",
            switch_inline_query=f"הצטרפו איתי ל‑SLH Dating — לא רק עוד אפליקציה: {invite}",
        )],
        [InlineKeyboardButton(text="🌐 שיתוף דרך האתר (כל הרשתות)", url=web_url("/referral.html", user_id))],
        [InlineKeyboardButton(text="🔙 חזרה לתפריט", callback_data="cmd:menu")],
    ])
    await reply(text, parse_mode="Markdown", reply_markup=share_kb)


@dp.callback_query(F.data == "cmd:menu")
async def cb_menu(c: CallbackQuery):
    await c.message.answer("תפריט ראשי:", reply_markup=main_menu(c.from_user.id))
    await c.answer()


@dp.message(Command("site"))
async def cmd_site(m: Message):
    await m.answer(
        "🌐 *אזור אישי באתר SLH*\n\n"
        f"• [Dashboard]({web_url('/dashboard.html', m.from_user.id)})\n"
        f"• [פרופיל Dating]({web_url('/dating.html', m.from_user.id)})\n"
        f"• [Wallet]({web_url('/wallet.html', m.from_user.id)})\n"
        f"• [Community]({web_url('/community.html', m.from_user.id)})\n"
        f"• [Sudoku]({web_url('/sudoku.html', m.from_user.id)})\n",
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=main_menu(m.from_user.id),
    )


async def main():
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (id={me.id})")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
