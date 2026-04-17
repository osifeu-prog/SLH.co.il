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
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("g4mebot")

TOKEN = os.getenv("G4MEBOT_TOKEN", "").strip()
SLH_API = os.getenv("SLH_API", "https://slh-api-production.up.railway.app").rstrip("/")

if not TOKEN:
    raise SystemExit("G4MEBOT_TOKEN env var is required")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# In-memory session state per user (candidate currently shown)
USER_STATE: dict[int, dict] = {}


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


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 מצא התאמה", callback_data="cmd:match")],
        [InlineKeyboardButton(text="💘 ההתאמות שלי", callback_data="cmd:matches")],
        [InlineKeyboardButton(text="👤 פרופיל (עריכה מלאה באתר)", url="https://slh-nft.com/dating.html")],
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
async def cmd_start(m: Message):
    # Block the family minor immediately
    if m.from_user.id == 6466974138:
        await m.answer("⚠ שירות זה מיועד למשתמשים מעל גיל 18 בלבד. צור קשר עם אוסיף לעזרה.")
        return
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
            reply_markup=main_menu(),
        )
    else:
        await c.message.edit_text(
            "נהדר! כדי להתחיל — צור פרופיל באתר:\n\n"
            "👉 https://slh-nft.com/dating.html\n\n"
            "אחרי שתשמור פרופיל, חזור לכאן וכתוב /match כדי למצוא התאמות.",
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
    text = (
        "📚 *פקודות:*\n"
        "/start — התחלה מחדש\n"
        "/match — מצא התאמה חדשה\n"
        "/matches — רשימת התאמות הדדיות\n"
        "/profile — עריכה באתר\n"
        "/help — הודעה זו\n\n"
        "💡 טיפ: עריכת פרופיל מפורטת — רק באתר:\n"
        "https://slh-nft.com/dating.html"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown")


@dp.message(Command("profile"))
async def cmd_profile(m: Message):
    profile = await api_get(f"/api/dating/profile/{m.from_user.id}")
    if not profile.get("exists"):
        await m.answer("עוד אין לך פרופיל. צור באתר: https://slh-nft.com/dating.html")
        return
    text = (
        f"👤 *{profile['display_name']}* · {profile['age']}\n"
        f"📍 {profile.get('city','—')}\n"
        f"🎯 {profile.get('looking_for','—')}\n"
        f"💼 {profile.get('profession','—')}\n\n"
        f"{profile.get('bio','(אין ביו)')}\n\n"
        f"לעריכה: https://slh-nft.com/dating.html"
    )
    await m.answer(text, parse_mode="Markdown")


async def main():
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (id={me.id})")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
