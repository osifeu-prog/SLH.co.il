"""
SLH Wellness - בריאות נפש, מדיטציה, תזונה, אימונים
Powered by SPARK IND | @NIFTI_Publisher_Bot

5 תזכורות יומיות + תגמולים במטבעות
"""
import os
import sys
import asyncio
import logging
import random
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB,
    ReplyKeyboardMarkup as RKM, KeyboardButton as KB,
)

sys.path.insert(0, "/app/shared")
try:
    from slh_payments import db as pay_db
    from slh_payments.config import ADMIN_USER_ID, TON_WALLET
except Exception:
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))
    TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    pay_db = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("slh.wellness")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = Bot(TOKEN)
dp = Dispatcher()

users = {}

# Daily content
MEDITATIONS = [
    "\U0001f9d8 *\u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4 \u05d9\u05d5\u05de\u05d9\u05ea*\n\n\u05e9\u05d1 \u05d1\u05e0\u05d5\u05d7, \u05e2\u05e6\u05d5\u05dd \u05e2\u05d9\u05e0\u05d9\u05d9\u05dd.\n\u05e0\u05e9\u05d5\u05dd \u05e2\u05de\u05d5\u05e7 3 \u05e4\u05e2\u05de\u05d9\u05dd.\n\u05e9\u05d9\u05dd \u05dc\u05d1 \u05dc\u05e0\u05e9\u05d9\u05de\u05d4 \u05e9\u05dc\u05da.\n\u05e9\u05d0\u05e3 5 \u05e4\u05e2\u05de\u05d9\u05dd \u05d3\u05e8\u05da \u05d4\u05d0\u05e3.\n\u05e0\u05e9\u05d5\u05e3 \u05d1\u05d0\u05d9\u05d8\u05d9\u05d5\u05ea 5 \u05e4\u05e2\u05de\u05d9\u05dd.\n\u05e4\u05ea\u05d7 \u05e2\u05d9\u05e0\u05d9\u05d9\u05dd \u05d1\u05d0\u05d9\u05d8\u05d9\u05d5\u05ea.",
    "\U0001f9d8 *\u05d4\u05e8\u05e4\u05d9\u05d4 \u05d2\u05d5\u05e4\u05e0\u05d9\u05ea*\n\n\u05e9\u05d1 \u05d1\u05e0\u05d5\u05d7.\n\u05d7\u05e9\u05d5\u05d1 \u05e2\u05dc \u05de\u05e9\u05d4\u05d5 \u05d0\u05d7\u05d3 \u05d8\u05d5\u05d1 \u05e9\u05e7\u05e8\u05d4 \u05dc\u05da \u05d4\u05d9\u05d5\u05dd.\n\u05ea\u05df \u05dc\u05d5 \u05ea\u05d5\u05d3\u05d4 \u05d1\u05dc\u05d1.\n\u05e0\u05e9\u05d5\u05dd \u05e2\u05de\u05d5\u05e7 \u05d3\u05e7\u05d4.\n\u05d7\u05d9\u05d9\u05da.",
    "\U0001f9d8 *\u05e1\u05e8\u05d9\u05e7\u05ea \u05d2\u05d5\u05e3*\n\n\u05e9\u05d1 \u05d0\u05d5 \u05e2\u05de\u05d5\u05d3.\n\u05e1\u05e8\u05d5\u05e7 \u05d0\u05ea \u05d4\u05d2\u05d5\u05e3 \u05de\u05d4\u05e8\u05d0\u05e9 \u05dc\u05e8\u05d2\u05dc\u05d9\u05d9\u05dd.\n\u05e9\u05d7\u05e8\u05e8 \u05db\u05dc \u05de\u05ea\u05d7.\n\u05e0\u05e9\u05d5\u05dd 3 \u05e0\u05e9\u05d9\u05de\u05d5\u05ea \u05e2\u05de\u05d5\u05e7\u05d5\u05ea.",
]

EXERCISES = [
    "\U0001f3cb\ufe0f *\u05d0\u05d9\u05de\u05d5\u05df \u05d9\u05d5\u05de\u05d9 (10 \u05d3\u05e7\u05d5\u05ea)*\n\n\u2022 20 \u05e1\u05e7\u05d5\u05d5\u05d8\u05d9\u05dd\n\u2022 15 \u05e9\u05db\u05d9\u05d1\u05d5\u05ea\n\u2022 10 \u05dc\u05d7\u05d9\u05e6\u05d5\u05ea \u05d1\u05d8\u05df\n\u2022 30 \u05e9\u05e0\u05d9\u05d5\u05ea \u05e4\u05dc\u05d0\u05e0\u05e7\n\u2022 20 \u05de\u05ea\u05d9\u05d7\u05d5\u05ea",
    "\U0001f3cb\ufe0f *\u05d0\u05d9\u05de\u05d5\u05df \u05d1\u05d5\u05e7\u05e8 (15 \u05d3\u05e7\u05d5\u05ea)*\n\n\u2022 30 \u05e1\u05e7\u05d5\u05d5\u05d8\u05d9\u05dd + \u05e7\u05e4\u05d9\u05e6\u05d4\n\u2022 20 \u05e9\u05db\u05d9\u05d1\u05d5\u05ea\n\u2022 15 \u05dc\u05d7\u05d9\u05e6\u05d5\u05ea \u05d1\u05d8\u05df\n\u2022 45 \u05e9\u05e0\u05d9\u05d5\u05ea \u05e4\u05dc\u05d0\u05e0\u05e7\n\u2022 30 \u05de\u05ea\u05d9\u05d7\u05d5\u05ea",
]

NUTRITION_TIPS = [
    "\U0001f957 *\u05d8\u05d9\u05e4 \u05ea\u05d6\u05d5\u05e0\u05d4*\n\n\u05e9\u05ea\u05d4 \u05dc\u05e4\u05d7\u05d5\u05ea 8 \u05db\u05d5\u05e1\u05d5\u05ea \u05de\u05d9\u05dd \u05d1\u05d9\u05d5\u05dd.\n\u05de\u05d9\u05dd = \u05d7\u05d9\u05d9\u05dd. \u05ea\u05ea\u05d7\u05d9\u05dc \u05d0\u05ea \u05d4\u05d1\u05d5\u05e7\u05e8 \u05e2\u05dd \u05db\u05d5\u05e1 \u05de\u05d9\u05dd.",
    "\U0001f957 *\u05d0\u05e8\u05d5\u05d7\u05ea \u05d1\u05d5\u05e7\u05e8*\n\n\u2022 \u05d1\u05d9\u05e6\u05d9\u05dd + \u05d7\u05de\u05d0\u05ea \u05d1\u05d5\u05d8\u05e0\u05d9\u05dd + \u05dc\u05d7\u05dd \u05de\u05dc\u05d0\n\u2022 \u05e9\u05d9\u05d1\u05d5\u05dc\u05ea \u05e9\u05d5\u05e2\u05dc + \u05e4\u05d9\u05e8\u05d5\u05ea\n\u2022 \u05ea\u05d4 \u05d9\u05e8\u05d5\u05e7 \u05d1\u05dc\u05d9 \u05e1\u05d5\u05db\u05e8",
]

AFFIRMATIONS = [
    "\U0001f31f \u05d0\u05e0\u05d9 \u05e8\u05d0\u05d5\u05d9/\u05d4 \u05dc\u05d3\u05d1\u05e8\u05d9\u05dd \u05d8\u05d5\u05d1\u05d9\u05dd.",
    "\U0001f31f \u05d0\u05e0\u05d9 \u05de\u05ea\u05e7\u05d3\u05dd/\u05ea \u05d1\u05db\u05dc \u05d9\u05d5\u05dd.",
    "\U0001f31f \u05d0\u05e0\u05d9 \u05d1\u05d5\u05d7\u05e8/\u05ea \u05d1\u05e9\u05de\u05d7\u05d4.",
    "\U0001f31f \u05d4\u05d2\u05d5\u05e3 \u05e9\u05dc\u05d9 \u05d7\u05d6\u05e7.",
    "\U0001f31f \u05d0\u05e0\u05d9 \u05d1\u05e9\u05dc\u05d5\u05dd \u05e2\u05dd \u05e2\u05e6\u05de\u05d9.",
]


def get_user(uid, username=""):
    if uid not in users:
        users[uid] = {
            "username": username, "joined": datetime.now().isoformat(),
            "streak": 0, "total_sessions": 0, "tokens": 5,  # 5 free
            "last_checkin": "", "completed_today": [],
        }
    if username:
        users[uid]["username"] = username
    return users[uid]


def main_kb():
    return RKM(keyboard=[
        [KB(text="\U0001f9d8 \u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4"), KB(text="\U0001f3cb\ufe0f \u05d0\u05d9\u05de\u05d5\u05df")],
        [KB(text="\U0001f957 \u05ea\u05d6\u05d5\u05e0\u05d4"), KB(text="\U0001f31f \u05d0\u05d9\u05de\u05e8\u05d4")],
        [KB(text="\U0001f4ca \u05d4\u05ea\u05e7\u05d3\u05de\u05d5\u05ea"), KB(text="\u2753 \u05e2\u05d6\u05e8\u05d4")],
    ], resize_keyboard=True)


@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username or "")
    await m.answer(
        "\U0001f4a1 *SLH Wellness*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\u05e9\u05dc\u05d5\u05dd {m.from_user.first_name}! \U0001f44b\n\n"
        "\u05d4\u05de\u05e8\u05db\u05d6 \u05dc\u05d1\u05e8\u05d9\u05d0\u05d5\u05ea \u05d4\u05d2\u05d5\u05e3, \u05d4\u05e0\u05e4\u05e9 \u05d5\u05d4\u05e8\u05d5\u05d7.\n\n"
        "\U0001f9d8 *\u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4* - \u05ea\u05e8\u05d2\u05d5\u05dc\u05d9\u05dd \u05de\u05d5\u05e0\u05d7\u05d9\u05dd \u05d9\u05d5\u05de\u05d9\u05d9\u05dd\n"
        "\U0001f3cb\ufe0f *\u05d0\u05d9\u05de\u05d5\u05df* - \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea \u05d0\u05d9\u05de\u05d5\u05df \u05d9\u05d5\u05de\u05d9\u05d5\u05ea\n"
        "\U0001f957 *\u05ea\u05d6\u05d5\u05e0\u05d4* - \u05d8\u05d9\u05e4\u05d9\u05dd \u05d5\u05de\u05ea\u05db\u05d5\u05e0\u05d9\u05dd\n"
        "\U0001f31f *\u05d0\u05d9\u05de\u05e8\u05d5\u05ea* - \u05d7\u05d9\u05d6\u05d5\u05e7\u05d9\u05dd \u05d9\u05d5\u05de\u05d9\u05d9\u05dd\n\n"
        f"\U0001f525 \u05e8\u05e6\u05e3: {u['streak']} \u05d9\u05de\u05d9\u05dd | \U0001f3c5 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea: {u['tokens']}\n\n"
        "\u05d4\u05e9\u05dc\u05dd \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea \u05d9\u05d5\u05de\u05d9\u05d5\u05ea = \u05e7\u05d1\u05dc \u05ea\u05d2\u05de\u05d5\u05dc\u05d9\u05dd!\n\n"
        "_Powered by SPARK IND | SLH Ecosystem_",
        parse_mode="Markdown", reply_markup=main_kb(),
    )


@dp.message(F.text == "\U0001f9d8 \u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4")
async def meditation_cmd(m: types.Message):
    u = get_user(m.from_user.id)
    med = random.choice(MEDITATIONS)
    kb = IKM(inline_keyboard=[
        [IKB(text="\u2705 \u05d4\u05e9\u05dc\u05de\u05ea\u05d9 (+2 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea)", callback_data="well:done:meditation")],
    ])
    await m.answer(med, parse_mode="Markdown", reply_markup=kb)


@dp.message(F.text == "\U0001f3cb\ufe0f \u05d0\u05d9\u05de\u05d5\u05df")
async def exercise_cmd(m: types.Message):
    ex = random.choice(EXERCISES)
    kb = IKM(inline_keyboard=[
        [IKB(text="\u2705 \u05d4\u05e9\u05dc\u05de\u05ea\u05d9 (+3 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea)", callback_data="well:done:exercise")],
    ])
    await m.answer(ex, parse_mode="Markdown", reply_markup=kb)


@dp.message(F.text == "\U0001f957 \u05ea\u05d6\u05d5\u05e0\u05d4")
async def nutrition_cmd(m: types.Message):
    tip = random.choice(NUTRITION_TIPS)
    kb = IKM(inline_keyboard=[
        [IKB(text="\u2705 \u05e7\u05e8\u05d0\u05ea\u05d9 (+1 \u05e0\u05e7\u05d5\u05d3\u05d4)", callback_data="well:done:nutrition")],
    ])
    await m.answer(tip, parse_mode="Markdown", reply_markup=kb)


@dp.message(F.text == "\U0001f31f \u05d0\u05d9\u05de\u05e8\u05d4")
async def affirmation_cmd(m: types.Message):
    aff = random.choice(AFFIRMATIONS)
    await m.answer(aff + "\n\n\u05d7\u05d6\u05d5\u05e8/\u05d9 \u05e2\u05dc \u05d6\u05d4 3 \u05e4\u05e2\u05de\u05d9\u05dd \u05d1\u05e7\u05d5\u05dc.", parse_mode="Markdown")


@dp.callback_query(F.data.startswith("well:done:"))
async def complete_activity(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)
    activity = cb.data.split(":")[2]
    today = datetime.now().strftime("%Y-%m-%d")
    rewards = {"meditation": 2, "exercise": 3, "nutrition": 1}
    reward = rewards.get(activity, 1)

    if today != u.get("last_checkin"):
        u["last_checkin"] = today
        u["completed_today"] = []
        u["streak"] += 1

    if activity not in u["completed_today"]:
        u["completed_today"].append(activity)
        u["tokens"] += reward
        u["total_sessions"] += 1
        await cb.message.answer(
            f"\u2705 *{activity} \u05d4\u05d5\u05e9\u05dc\u05dd!*\n+{reward} \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea\n\n"
            f"\U0001f525 \u05e8\u05e6\u05e3: {u['streak']} \u05d9\u05de\u05d9\u05dd\n"
            f"\U0001f3c5 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea: {u['tokens']}\n"
            f"\u05d4\u05d9\u05d5\u05dd: {len(u['completed_today'])}/3 \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea",
            parse_mode="Markdown")
    else:
        await cb.answer("\u05db\u05d1\u05e8 \u05d4\u05e9\u05dc\u05de\u05ea \u05d4\u05d9\u05d5\u05dd!", show_alert=True)
    await cb.answer()


@dp.message(F.text == "\U0001f4ca \u05d4\u05ea\u05e7\u05d3\u05de\u05d5\u05ea")
async def progress_cmd(m: types.Message):
    u = get_user(m.from_user.id)
    today_done = len(u.get("completed_today", []))
    await m.answer(
        "\U0001f4ca *\u05d4\u05ea\u05e7\u05d3\u05de\u05d5\u05ea*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f525 \u05e8\u05e6\u05e3: {u['streak']} \u05d9\u05de\u05d9\u05dd\n"
        f"\U0001f3c5 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea: {u['tokens']}\n"
        f"\U0001f4c6 \u05e1\u05d4\"\u05db \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea: {u['total_sessions']}\n"
        f"\u05d4\u05d9\u05d5\u05dd: {today_done}/3\n\n"
        "\u05d4\u05e9\u05dc\u05dd 3 \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea \u05d1\u05d9\u05d5\u05dd = \u05d1\u05d5\u05e0\u05d5\u05e1 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea!",
        parse_mode="Markdown")


@dp.message(F.text == "\u2753 \u05e2\u05d6\u05e8\u05d4")
@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    await m.answer(
        "\u2753 *SLH Wellness*\n\n"
        "\U0001f9d8 \u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4 - \u05ea\u05e8\u05d2\u05d5\u05dc\u05d9 \u05e0\u05e9\u05d9\u05de\u05d4 \u05d5\u05de\u05d9\u05d9\u05e0\u05d3\u05e4\u05d5\u05dc\u05e0\u05e1 (+2)\n"
        "\U0001f3cb\ufe0f \u05d0\u05d9\u05de\u05d5\u05df - \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea \u05d9\u05d5\u05de\u05d9\u05d5\u05ea \u05de\u05d5\u05ea\u05d0\u05de\u05d5\u05ea (+3)\n"
        "\U0001f957 \u05ea\u05d6\u05d5\u05e0\u05d4 - \u05d8\u05d9\u05e4\u05d9\u05dd \u05d5\u05de\u05ea\u05db\u05d5\u05e0\u05d9\u05dd (+1)\n"
        "\U0001f31f \u05d0\u05d9\u05de\u05e8\u05d5\u05ea - \u05d7\u05d9\u05d6\u05d5\u05e7\u05d9\u05dd \u05d9\u05d5\u05de\u05d9\u05d9\u05dd\n\n"
        "\u05d4\u05e9\u05dc\u05dd \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea \u05d5\u05e6\u05d1\u05d5\u05e8 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea!\n"
        "\u05e8\u05e6\u05e3 \u05d9\u05d5\u05de\u05d9 = \u05d1\u05d5\u05e0\u05d5\u05e1\u05d9\u05dd!\n\n"
        "\U0001f4a1 SPARK IND | SLH Ecosystem",
        parse_mode="Markdown")


async def main():
    logger.info("=" * 40)
    logger.info("SLH Wellness Bot - Starting")
    logger.info("=" * 40)

    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        me = await bot.get_me()
        await init_coordination_for_bot(
            bot, dp,
            name="nifti-bot",
            username=me.username,
        )
    except Exception as e:
        logger.warning("coordination init failed: %s", e)

    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
