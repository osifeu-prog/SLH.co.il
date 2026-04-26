#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import aiohttp
import asyncpg
from shared_db_core import init_db_pool as _shared_init_db_pool
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup

from slh_payments.ledger import transfer, get_balance, ensure_balance
from slh_payments.config import ADMIN_USER_ID, TON_WALLET

APP_NAME = "SLH NFT Marketplace | SPARK IND"
TAGLINE = "From Bits to Infinity"
ACTIVATION_FEE_ILS = Decimal("22.221")
ACTIVATION_FEE_TON = Decimal("1.5")
COINGECKO_BASE = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
BSC_TOKEN_CONTRACT = os.getenv("SLH_BSC_CONTRACT", "0xACb0A09414CEA1C879c67bB7A877E4e19480f022")
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("NFTY_MADNESS_TOKEN")
BROADCAST_CHANNEL = os.getenv("NFTY_BROADCAST_CHANNEL", "@slhniffty")
BOT_USERNAME = os.getenv("NFTY_BOT_USERNAME", "NFTY_madness_bot")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("nfty-bot")
router = Router()

class SellStates(StatesGroup):
    waiting_name = State()
    waiting_category = State()
    waiting_price = State()
    waiting_currency = State()
    waiting_description = State()
    waiting_media_url = State()

@dataclass
class AppContext:
    pool: asyncpg.Pool
    session: aiohttp.ClientSession


APP_CTX: Optional[AppContext] = None
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 שוק המרקטפלייס"), KeyboardButton(text="🔍 חיפוש פריטים")],
            [KeyboardButton(text="📦 הפריטים שלי"), KeyboardButton(text="🏷️ מרקטפלייס קטגוריות")],
            [KeyboardButton(text="🛒 עגלת קניות"), KeyboardButton(text="💰 ארנק דיגיטלי")],
            [KeyboardButton(text="📊 סטטיסטיקות"), KeyboardButton(text="💎 פרימיום")],
            [KeyboardButton(text="🎮 משחקים"), KeyboardButton(text="🤖 בינה מלאכותית")],
            [KeyboardButton(text="🎲 הגרלות"), KeyboardButton(text="👤 הפרופיל שלי")],
            [KeyboardButton(text="ℹ️ עזרה ומידע")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def admin_listing_actions(listing_id: int, owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ אישור", callback_data=f"admin:approve:{listing_id}:{owner_id}"),
            InlineKeyboardButton(text="❌ דחייה", callback_data=f"admin:reject:{listing_id}:{owner_id}")
        ]]
    )

def activation_actions(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ אישור הפעלה", callback_data=f"admin:activate:{user_id}"),
            InlineKeyboardButton(text="❌ דחייה הפעלה", callback_data=f"admin:activate_reject:{user_id}")
        ]]
    )

async def create_http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))

async def create_pool() -> asyncpg.Pool:
    # Phase 0B (2026-04-21): unified pool via shared_db_core (fail-fast, health-checked).
    # max_size drops 10→4 to fit Railway's 88-conn budget across 22 containers.
    return await _shared_init_db_pool(DATABASE_URL)

async def bootstrap_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS nfty_users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_activated BOOLEAN NOT NULL DEFAULT FALSE,
                activated_at TIMESTAMPTZ,
                referred_by BIGINT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS nfty_activation_requests (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                ton_amount NUMERIC(18,8) NOT NULL DEFAULT 1.5,
                ils_amount NUMERIC(18,3) NOT NULL DEFAULT 22.221,
                tx_ref TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ
            );

            CREATE TABLE IF NOT EXISTS nfty_items (
                id BIGSERIAL PRIMARY KEY,
                owner_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                media_url TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS nfty_listings (
                id BIGSERIAL PRIMARY KEY,
                item_id BIGINT NOT NULL REFERENCES nfty_items(id) ON DELETE CASCADE,
                seller_id BIGINT NOT NULL,
                price NUMERIC(18,8) NOT NULL,
                currency_symbol TEXT NOT NULL DEFAULT 'SLH',
                status TEXT NOT NULL DEFAULT 'pending_approval',
                admin_note TEXT,
                approved_by BIGINT,
                approved_at TIMESTAMPTZ,
                sold_to BIGINT,
                sold_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS virtual_pets (
                user_id BIGINT PRIMARY KEY,
                pet_name TEXT NOT NULL DEFAULT 'Sparky',
                pet_type TEXT NOT NULL DEFAULT 'spark',
                level INT NOT NULL DEFAULT 1,
                xp INT NOT NULL DEFAULT 0,
                mood INT NOT NULL DEFAULT 80,
                energy INT NOT NULL DEFAULT 80,
                hunger INT NOT NULL DEFAULT 20,
                curiosity INT NOT NULL DEFAULT 50,
                creativity INT NOT NULL DEFAULT 50,
                evolution_stage INT NOT NULL DEFAULT 1,
                last_action_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS pet_action_log (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                delta JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS system_events (
                id BIGSERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                actor_id BIGINT,
                entity_type TEXT,
                entity_id TEXT,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS breathing_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                exercise_type TEXT NOT NULL,
                duration_sec INT NOT NULL DEFAULT 60,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                pet_bonus_applied BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS daily_quests (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                quest_key TEXT NOT NULL,
                quest_title TEXT NOT NULL,
                quest_desc TEXT NOT NULL,
                xp_reward INT NOT NULL DEFAULT 10,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                assigned_date DATE NOT NULL DEFAULT CURRENT_DATE,
                completed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, quest_key, assigned_date)
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                achievement_key TEXT NOT NULL,
                unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, achievement_key)
            );
        """)

async def log_event(pool: asyncpg.Pool, event_type: str, actor_id: Optional[int]=None, entity_type: Optional[str]=None, entity_id: Optional[str]=None, payload: Optional[dict[str, Any]]=None) -> None:
    payload = payload or {}
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO system_events (event_type, actor_id, entity_type, entity_id, payload)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            """,
            event_type, actor_id, entity_type, entity_id, json.dumps(payload, ensure_ascii=False)
        )

# ─── Achievements System ───

ACHIEVEMENTS = {
    "first_breath": {"title": "🫁 נשימה ראשונה", "desc": "השלם תרגיל נשימה ראשון", "xp": 20},
    "breath_master": {"title": "🧘 מאסטר נשימה", "desc": "השלם 10 תרגילי נשימה", "xp": 50},
    "quest_rookie": {"title": "🎯 טירון משימות", "desc": "השלם משימה יומית ראשונה", "xp": 15},
    "quest_master": {"title": "👑 מלך המשימות", "desc": "השלם 3 משימות ביום אחד", "xp": 100},
    "pet_parent": {"title": "🐾 הורה אוהב", "desc": "האכל את החיה 10 פעמים", "xp": 30},
    "playful": {"title": "🎮 שובב", "desc": "שחק עם החיה 10 פעמים", "xp": 30},
    "scholar": {"title": "📚 חכם", "desc": "למד את החיה 10 פעמים", "xp": 40},
    "early_bird": {"title": "🌅 ציפור מוקדמת", "desc": "בצע פעולה לפני 07:00", "xp": 25},
    "night_owl": {"title": "🦉 ינשוף לילה", "desc": "בצע פעולה אחרי 23:00", "xp": 25},
    "week_streak": {"title": "🔥 שבוע רצוף", "desc": "בצע פעולה 7 ימים ברציפות", "xp": 100},
    "level_5": {"title": "⭐ רמה 5", "desc": "הגע לרמה 5 עם החיה", "xp": 50},
    "level_10": {"title": "💎 רמה 10", "desc": "הגע לרמה 10 עם החיה", "xp": 100},
    "social_butterfly": {"title": "🦋 חברותי", "desc": "שתף את הלינק שלך", "xp": 15},
    "collector": {"title": "🛍️ אספן", "desc": "רכוש פריט ראשון בשוק", "xp": 30},
    "seller": {"title": "💼 סוחר", "desc": "העלה פריט ראשון למכירה", "xp": 30},
}


async def check_and_unlock_achievement(pool, user_id, key):
    """Try to unlock an achievement. Returns the achievement dict if newly unlocked, None if already had."""
    if key not in ACHIEVEMENTS:
        return None
    try:
        async with pool.acquire() as conn:
            existing = await conn.fetchval(
                "SELECT id FROM achievements WHERE user_id = $1 AND achievement_key = $2", user_id, key
            )
            if existing:
                return None
            await conn.execute(
                "INSERT INTO achievements (user_id, achievement_key) VALUES ($1, $2) ON CONFLICT DO NOTHING", user_id, key
            )
            # Award XP
            xp = ACHIEVEMENTS[key].get("xp", 0)
            if xp > 0:
                await conn.execute(
                    "UPDATE virtual_pets SET xp = xp + $2, updated_at = NOW() WHERE user_id = $1", user_id, xp
                )
        return ACHIEVEMENTS[key]
    except Exception:
        return None


async def notify_achievement(msg_or_cb, achievement):
    """Send achievement unlock notification"""
    text = f"🏆 הישג חדש!\n\n{achievement['title']}\n{achievement['desc']}\n+{achievement['xp']} XP"
    if hasattr(msg_or_cb, 'answer'):
        await msg_or_cb.answer(text)
    elif hasattr(msg_or_cb, 'message'):
        await msg_or_cb.message.answer(text)


async def check_time_achievements(pool, user_id, msg_or_cb):
    """Check early_bird and night_owl based on current hour"""
    hour = datetime.now().hour
    if hour < 7:
        ach = await check_and_unlock_achievement(pool, user_id, "early_bird")
        if ach:
            await notify_achievement(msg_or_cb, ach)
    elif hour >= 23:
        ach = await check_and_unlock_achievement(pool, user_id, "night_owl")
        if ach:
            await notify_achievement(msg_or_cb, ach)


async def check_pet_level_achievements(pool, user_id, msg_or_cb):
    """Check level-based achievements after pet actions"""
    pet = await get_pet(pool, user_id)
    if pet:
        level = int(pet["level"])
        if level >= 5:
            ach = await check_and_unlock_achievement(pool, user_id, "level_5")
            if ach:
                await notify_achievement(msg_or_cb, ach)
        if level >= 10:
            ach = await check_and_unlock_achievement(pool, user_id, "level_10")
            if ach:
                await notify_achievement(msg_or_cb, ach)


async def upsert_user(pool: asyncpg.Pool, message: Message, referred_by: Optional[int]=None) -> None:
    full_name = " ".join([x for x in [message.from_user.first_name, message.from_user.last_name] if x]).strip()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO nfty_users (user_id, username, full_name, referred_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id)
            DO UPDATE SET username = EXCLUDED.username, full_name = EXCLUDED.full_name, updated_at = NOW()
            """,
            message.from_user.id, message.from_user.username, full_name, referred_by
        )
        await conn.execute(
            """
            INSERT INTO virtual_pets (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            message.from_user.id
        )

async def is_activated(pool: asyncpg.Pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT is_activated FROM nfty_users WHERE user_id = $1", user_id)
        return bool(val)

async def require_activation(message: Message, pool: asyncpg.Pool) -> bool:
    if await is_activated(pool, message.from_user.id):
        return True
    await message.answer(
        "⚠️ <b>נדרש הפעלת חשבון</b>\n\n"
        "כדי להשתמש במרקטפלייס של הבוט עליך להפעיל חשבון דיגיטלי-טלגרם.\n"
        f"עלות ההפעלה: <b>{ACTIVATION_FEE_ILS}₪</b> (~{ACTIVATION_FEE_TON} TON)\n"
        f"כתובת TON להעברה:\n<code>{TON_WALLET}</code>\n\n"
        "שלחו אסמכתא להפעלה:\n<code>/activate TX123456</code>",
        reply_markup=main_menu()
    )
    return False

async def fetch_prices(session: aiohttp.ClientSession) -> dict[str, Any]:
    out = {"bitcoin": None, "toncoin": None, "bsc_token": None}
    try:
        async with session.get(f"{COINGECKO_BASE}/simple/price", params={"ids":"bitcoin,toncoin","vs_currencies":"usd,ils"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                out["bitcoin"] = data.get("bitcoin")
                out["toncoin"] = data.get("toncoin")
        async with session.get(f"{COINGECKO_BASE}/simple/token_price/binance-smart-chain", params={"contract_addresses":BSC_TOKEN_CONTRACT,"vs_currencies":"usd,ils"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                out["bsc_token"] = data.get(BSC_TOKEN_CONTRACT.lower()) or data.get(BSC_TOKEN_CONTRACT)
    except Exception:
        log.exception("price fetch failed")
    return out

def fmt_prices(prices: dict[str, Any]) -> str:
    lines = ["📈 <b>מחירי שוק</b>"]
    if prices.get("bitcoin"):
        lines.append(f"🪙 BTC: ${prices['bitcoin'].get('usd','?')} | ₪{prices['bitcoin'].get('ils','?')}")
    if prices.get("toncoin"):
        lines.append(f"🪙 TON: ${prices['toncoin'].get('usd','?')} | ₪{prices['toncoin'].get('ils','?')}")
    if prices.get("bsc_token"):
        lines.append(f"🪙 SLH/BSC: ${prices['bsc_token'].get('usd','?')} | ₪{prices['bsc_token'].get('ils','?')}")
    if len(lines) == 1:
        lines.append("🪙 אין נתונים זמינים כרגע")
    return "\n".join(lines)

def get_ctx() -> AppContext:
    if APP_CTX is None:
        raise RuntimeError("App context not initialized")
    return APP_CTX

async def get_pet(pool: asyncpg.Pool, user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)

def pet_face(stage: int, mood: int, energy: int) -> str:
    if energy < 25:
        return "😴"
    if mood < 35:
        return "😢"
    if stage >= 4:
        return "🦄"
    if stage == 3:
        return "🐉"
    if stage == 2:
        return "🐣"
    return "🥚"

def pet_stage_name(stage: int) -> str:
    return {
        1: "ביצה",
        2: "גור",
        3: "נוער",
        4: "בוגר",
    }.get(stage, "אגדה")

async def apply_pet_action(pool: asyncpg.Pool, user_id: int, action_type: str):
    deltas = {
        "feed":  {"mood": 6, "energy": 4, "hunger": -12, "xp": 4, "curiosity": 0, "creativity": 0},
        "play":  {"mood": 10, "energy": -8, "hunger": 5, "xp": 6, "curiosity": 2, "creativity": 1},
        "learn": {"mood": 3, "energy": -6, "hunger": 3, "xp": 10, "curiosity": 8, "creativity": 2},
        "sleep": {"mood": 2, "energy": 14, "hunger": 4, "xp": 2, "curiosity": 0, "creativity": 0},
    }
    delta = deltas[action_type]

    async with pool.acquire() as conn:
        pet = await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)
        if not pet:
            await conn.execute("INSERT INTO virtual_pets (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING", user_id)
            pet = await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)

        level = int(pet["level"])
        xp = int(pet["xp"]) + delta["xp"]
        mood = max(0, min(100, int(pet["mood"]) + delta["mood"]))
        energy = max(0, min(100, int(pet["energy"]) + delta["energy"]))
        hunger = max(0, min(100, int(pet["hunger"]) + delta["hunger"]))
        curiosity = max(0, min(100, int(pet["curiosity"]) + delta["curiosity"]))
        creativity = max(0, min(100, int(pet["creativity"]) + delta["creativity"]))
        evolution_stage = int(pet["evolution_stage"])

        while xp >= level * 25:
            xp -= level * 25
            level += 1

        if level >= 15:
            evolution_stage = 4
        elif level >= 9:
            evolution_stage = 3
        elif level >= 4:
            evolution_stage = 2

        await conn.execute(
            """
            UPDATE virtual_pets
            SET level = $2,
                xp = $3,
                mood = $4,
                energy = $5,
                hunger = $6,
                curiosity = $7,
                creativity = $8,
                evolution_stage = $9,
                last_action_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $1
            """,
            user_id, level, xp, mood, energy, hunger, curiosity, creativity, evolution_stage
        )
        await conn.execute(
            "INSERT INTO pet_action_log (user_id, action_type, delta) VALUES ($1, $2, $3::jsonb)",
            user_id, action_type, json.dumps(delta, ensure_ascii=False)
        )

    return await get_pet(pool, user_id)

def pet_status_text(pet) -> str:
    face = pet_face(int(pet["evolution_stage"]), int(pet["mood"]), int(pet["energy"]))
    return (
        f"{face} <b>{pet['pet_name']}</b>\n"
        f"שלב: <b>{pet_stage_name(int(pet['evolution_stage']))}</b>\n"
        f"רמה: <b>{pet['level']}</b>\n"
        f"XP: <b>{pet['xp']}</b>\n"
        f"מצב רוח: <b>{pet['mood']}</b>/100\n"
        f"אנרגיה: <b>{pet['energy']}</b>/100\n"
        f"רעב: <b>{pet['hunger']}</b>/100\n"
        f"סקרנות: <b>{pet['curiosity']}</b>/100\n"
        f"יצירתיות: <b>{pet['creativity']}</b>/100"
    )

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    ctx = get_ctx()
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            referred_by = int(command.args.replace("ref_", "").strip())
        except Exception:
            referred_by = None

    await upsert_user(ctx.pool, message, referred_by)
    prices = await fetch_prices(ctx.session)
    pet = await get_pet(ctx.pool, message.from_user.id)

    await message.answer(
        f"🎉 <b>{APP_NAME}</b>\n"
        f"<i>{TAGLINE}</i>\n\n"
        "ברוכים הבאים למרקטפלייס הדיגיטלי של SLH.\n"
        "כאן תוכלו למכור, לקנות ולסחור בפריטים דיגיטליים 🌐 עם חיית מחמד וירטואלית שגדלה איתכם.\n\n"
        f"{fmt_prices(prices)}\n\n"
        f"🐾 החיה שלך כרגע:\n{pet_status_text(pet)}\n\n"
        f"⚡ עלות הפעלה: <b>{ACTIVATION_FEE_ILS}₪</b> (~{ACTIVATION_FEE_TON} TON)",
        reply_markup=main_menu()
    )
    await log_event(ctx.pool, "user_start", actor_id=message.from_user.id, payload={"referred_by": referred_by})

@router.message(Command("help"))
@router.message(F.text == "ℹ️ עזרה ומידע")
async def cmd_help(message: Message, bot: Bot):
    ctx = get_ctx()
    await log_event(ctx.pool, "view_help", actor_id=message.from_user.id)
    await message.answer(
        "📋 <b>מדריך פקודות</b>\n\n"
        "/start 🔹 התחלה\n"
        "/activate TXREF 🔹 בקשת הפעלה\n"
        "/browse 🔹 עיון במרקטפלייס\n"
        "/sell 🔹 יצירת פריט למכירה\n"
        "/buy 123 🔹 רכישת פריט\n"
        "/my_items 🔹 הפריטים שלי\n"
        "/my_listings 🔹 המכירות שלי\n"
        "/wallet 🔹 ארנק SLH/ZVK\n"
        "/pet 🔹 מצב החיה הווירטואלית\n"
        "/feed | /play | /learn | /sleep 🔹 פעולות עם החיה\n"
        "/share 🔹 שיתוף לינק הפניה",
        reply_markup=main_menu()
    )

@router.message(Command("faq"))
@router.message(F.text == "ℹ️ שאלות נפוצות")
async def cmd_faq(message: Message, bot: Bot):
    await message.answer(
        "ℹ️ <b>שאלות נפוצות</b>\n\n"
        "🪙 הפעלה: העבירו תשלום והשתמשו /activate עם האסמכתא\n"
        "🪙 מטבעות: SLH או ZVK\n"
        "🪙 איך למכור: צרו פריט חדש דרך המרקטפלייס, מנהל יאשר לפני הצגה\n"
        "🪙 חיות וירטואליות תמגוצ'י מגדלות כמו נפש, האכלה והשכלה מעלות רמה",
        reply_markup=main_menu()
    )

@router.message(Command("share"))
@router.message(F.text == "📤 שיתוף")
async def cmd_share(message: Message, bot: Bot):
    ctx = get_ctx()
    me = await bot.get_me()
    text = f"🔗 {APP_NAME}\n🏷️ {TAGLINE}\nhttps://t.me/{me.username}?start=ref_{message.from_user.id}"
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "share")
    await message.answer("📤 <b>קישור שיתוף</b>\n\n" + f"<code>{text}</code>", reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")
    # Achievement: social_butterfly
    ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "social_butterfly")
    if ach:
        await notify_achievement(message, ach)

@router.message(Command("wallet"))
@router.message(F.text == "🔍 חיפוש פריטים")
async def cmd_wallet(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)

    balances = []
    for symbol in ("SLH", "ZVK"):
        try:
            try:
                bal = await get_balance(message.from_user.id, symbol)
            except TypeError:
                bal = await get_balance(user_id=message.from_user.id, symbol=symbol)
        except Exception:
            bal = "?"
        balances.append(f"🪙 {symbol}: <b>{bal}</b>")

    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "wallet")
    await message.answer("💰 <b>ארנק דיגיטלי</b>\n\n" + "\n".join(balances), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")

@router.message(Command("browse"))
@router.message(F.text == "🏪 שוק המרקטפלייס")
async def cmd_browse(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT l.id, i.title, i.category, i.description, l.price, l.currency_symbol
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.status = 'active'
            ORDER BY l.created_at DESC
            LIMIT 15
        """)

    if not rows:
        await message.answer("אין עדיין פריטים זמינים במרקטפלייס.", reply_markup=main_menu())
        return

    parts = ["🏪 <b>פריטים זמינים</b>\n"]
    for row in rows:
        parts.append(
            f"#{row['id']} | <b>{row['title']}</b>\n"
            f"קטגוריה: {row['category']}\n"
            f"מחיר: <b>{row['price']} {row['currency_symbol']}</b>\n"
            f"תיאור: {row['description'][:120]}\n"
            f"לרכישה: <code>/buy {row['id']}</code>\n"
        )
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "browse")
    await message.answer("\n".join(parts), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")

@router.message(Command("my_items"))
@router.message(F.text == "📦 הפריטים שלי")
async def cmd_my_items(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, title, category, description
            FROM nfty_items
            WHERE owner_id = $1
            ORDER BY created_at DESC
            LIMIT 30
        """, message.from_user.id)

    if not rows:
        await message.answer("עדיין אין לך פריטים דיגיטליים.", reply_markup=main_menu())
        return

    out = ["📦 <b>הפריטים שלי</b>\n"]
    for row in rows:
        out.append(f"🪙 #{row['id']} | <b>{row['title']}</b> | {row['category']}\n  {row['description'][:100]}")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("my_listings"))
@router.message(F.text == "🏷️ מרקטפלייס קטגוריות")
async def cmd_my_listings(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT l.id, i.title, l.price, l.currency_symbol, l.status
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.seller_id = $1
            ORDER BY l.created_at DESC
            LIMIT 30
        """, message.from_user.id)

    if not rows:
        await message.answer("אין לך עדיין מכירות פעילות.", reply_markup=main_menu())
        return

    out = ["🏷️ <b>המכירות שלי</b>\n"]
    for row in rows:
        out.append(f"🪙 #{row['id']} | <b>{row['title']}</b>\n  מחיר: {row['price']} {row['currency_symbol']} | סטטוס: <b>{row['status']}</b>")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("activate"))
async def cmd_activate(message: Message, command: CommandObject, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    tx_ref = (command.args or "").strip()
    if not tx_ref:
        await message.answer("שימוש נכון:\n<code>/activate TX123456</code>", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nfty_activation_requests (user_id, tx_ref, status)
            VALUES ($1, $2, 'pending')
        """, message.from_user.id, tx_ref)

    await message.answer("✅ בקשת ההפעלה נשלחה לבדיקת מנהל.", reply_markup=main_menu())

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "⚡ <b>בקשת הפעלה חדשה</b>\n\n"
            f"משתמש: <code>{message.from_user.id}</code>\n"
            f"אסמכתא: <code>{tx_ref}</code>",
            reply_markup=activation_actions(message.from_user.id)
        )
    except Exception:
        log.exception("failed to notify admin")

@router.callback_query(F.data.startswith("admin:activate:"))
async def cb_admin_activate(callback, bot: Bot):
    ctx = get_ctx()
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nfty_users (user_id, is_activated, activated_at)
            VALUES ($1, TRUE, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET is_activated = TRUE, activated_at = NOW(), updated_at = NOW()
        """, user_id)
        await conn.execute("""
            UPDATE nfty_activation_requests
            SET status='approved', reviewed_at=NOW()
            WHERE user_id=$1 AND status='pending'
        """, user_id)

    await callback.answer("ההפעלה אושרה")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "🎉 ההפעלה שלך אושרה.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("admin:activate_reject:"))
async def cb_admin_activate_reject(callback, bot: Bot):
    ctx = get_ctx()
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_activation_requests
            SET status='rejected', reviewed_at=NOW()
            WHERE user_id=$1 AND status='pending'
        """, user_id)

    await callback.answer("בקשת ההפעלה נדחתה")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "❌ בקשת ההפעלה נדחתה.", reply_markup=main_menu())

@router.message(Command("sell"))
@router.message(F.text == "🛒 עגלת קניות")
async def cmd_sell(message: Message, state: FSMContext, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    await state.set_state(SellStates.waiting_name)
    await message.answer("📦 <b>יצירת פריט חדש</b>\n\nשלב 1/6\nהכניסו את שם הפריט:", reply_markup=main_menu())

@router.message(SellStates.waiting_name)
async def sell_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(SellStates.waiting_category)
    await message.answer("שלב 2/6\nהכניסו קטגוריה לפריט:")

@router.message(SellStates.waiting_category)
async def sell_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(SellStates.waiting_price)
    await message.answer("שלב 3/6\nהכניסו מחיר מספרי. לדוגמה: 150")

@router.message(SellStates.waiting_price)
async def sell_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        await message.answer("אנא הזינו מחיר מספרי תקין.")
        return
    await state.update_data(price=str(price))
    await state.set_state(SellStates.waiting_currency)
    await message.answer("שלב 4/6\nבחרו מטבע: SLH או ZVK")

@router.message(SellStates.waiting_currency)
async def sell_currency(message: Message, state: FSMContext):
    symbol = message.text.strip().upper()
    if symbol not in {"SLH", "ZVK"}:
        await message.answer("אנא בחרו את SLH או ZVK.")
        return
    await state.update_data(currency_symbol=symbol)
    await state.set_state(SellStates.waiting_description)
    await message.answer("שלב 5/6\nהכניסו תיאור של הפריט:")

@router.message(SellStates.waiting_description)
async def sell_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(SellStates.waiting_media_url)
    await message.answer("שלב 6/6\nשלחו לינק לתמונה/סרטון, או הקלידו - לדילוג.")

@router.message(SellStates.waiting_media_url)
async def sell_media_url(message: Message, state: FSMContext, bot: Bot):
    ctx = get_ctx()
    data = await state.get_data()
    media_url = None if message.text.strip() == "-" else message.text.strip()
    await state.clear()

    async with ctx.pool.acquire() as conn:
        async with conn.transaction():
            item_id = await conn.fetchval("""
                INSERT INTO nfty_items (owner_id, title, category, description, media_url)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, message.from_user.id, data["title"], data["category"], data["description"], media_url)

            listing_id = await conn.fetchval("""
                INSERT INTO nfty_listings (item_id, seller_id, price, currency_symbol, status)
                VALUES ($1, $2, $3, $4, 'pending_approval')
                RETURNING id
            """, item_id, message.from_user.id, Decimal(data["price"]), data["currency_symbol"])

    await message.answer(f"✅ הפריט נוצר ונשלח לאישור מנהל.\nמספר מכירה: <b>{listing_id}</b>", reply_markup=main_menu())
    # Achievement: seller
    ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "seller")
    if ach:
        await notify_achievement(message, ach)

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "⚡ <b>פריט חדש לאישור</b>\n\n"
            f"מספר מכירה: <b>{listing_id}</b>\n"
            f"מוכר: <code>{message.from_user.id}</code>\n"
            f"שם: <b>{data['title']}</b>\n"
            f"קטגוריה: {data['category']}\n"
            f"מחיר: {data['price']} {data['currency_symbol']}\n"
            f"תיאור: {data['description']}",
            reply_markup=admin_listing_actions(listing_id, message.from_user.id)
        )
    except Exception:
        log.exception("failed sending admin approval")

@router.callback_query(F.data.startswith("admin:approve:"))
async def cb_admin_approve(callback, bot: Bot):
    ctx = get_ctx()
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='active', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))
        listing_row = await conn.fetchrow("""
            SELECT l.id, l.price, l.currency_symbol,
                   i.title, i.category, i.description, i.media_url
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.id = $1
        """, int(listing_id))

    await callback.answer("הפריט אושר")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"🎉 הפריט #{listing_id} שלך אושר למרקטפלייס.", reply_markup=main_menu())

    if listing_row:
        await broadcast_new_listing(bot, listing_row)


async def broadcast_new_listing(bot: Bot, row) -> None:
    try:
        title = row["title"]
        category = row["category"] or ""
        price = row["price"]
        currency = row["currency_symbol"] or "SLH"
        description = (row["description"] or "")[:280]
        media_url = row["media_url"]
        deep_link = f"https://t.me/{BOT_USERNAME}?start=buy_{row['id']}"

        caption = (
            f"🎨 <b>פריט חדש במרקטפלייס SLH NFT</b>\n\n"
            f"<b>{title}</b>\n"
            f"{category}\n\n"
            f"{description}\n\n"
            f"💰 <b>{price} {currency}</b>\n"
            f"🛒 <a href=\"{deep_link}\">קנה עכשיו בבוט</a>"
        )

        if media_url and media_url.startswith(("http://", "https://")):
            try:
                await bot.send_photo(BROADCAST_CHANNEL, photo=media_url, caption=caption, parse_mode=ParseMode.HTML)
                return
            except Exception:
                log.warning("Photo broadcast failed, falling back to text", exc_info=True)

        await bot.send_message(BROADCAST_CHANNEL, caption, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
    except Exception:
        log.exception("broadcast_new_listing failed for listing #%s", row.get("id"))

@router.callback_query(F.data.startswith("admin:reject:"))
async def cb_admin_reject(callback, bot: Bot):
    ctx = get_ctx()
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='rejected', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))

    await callback.answer("הפריט נדחה")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"❌ הפריט #{listing_id} נדחה.", reply_markup=main_menu())

@router.message(Command("buy"))
async def cmd_buy(message: Message, command: CommandObject, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    if not command.args:
        await message.answer("יש לציין מספר פריט: <code>/buy 123</code>", reply_markup=main_menu())
        return

    try:
        listing_id = int(command.args.strip())
    except Exception:
        await message.answer("מספר פריט לא תקין. לדוגמה: <code>/buy 123</code>", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT l.id, l.item_id, l.price, l.currency_symbol, l.status, l.seller_id, i.title
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.id = $1
        """, listing_id)

    if not row:
        await message.answer("הפריט לא נמצא.", reply_markup=main_menu())
        return
    if row["status"] != "active":
        await message.answer("הפריט אינו זמין לרכישה.", reply_markup=main_menu())
        return
    if row["seller_id"] == message.from_user.id:
        await message.answer("אי אפשר לקנות את הפריט של עצמך.", reply_markup=main_menu())
        return

    price = Decimal(str(row["price"]))
    symbol = row["currency_symbol"]

    try:
        try:
            enough = await ensure_balance(message.from_user.id, symbol, price)
        except TypeError:
            enough = await ensure_balance(user_id=message.from_user.id, symbol=symbol, amount=price)
    except Exception:
        await message.answer("לא הצלחנו לבדוק יתרה כרגע.", reply_markup=main_menu())
        return

    if not enough:
        await message.answer(f"❌ אין מספיק {symbol}. נדרש: <b>{price} {symbol}</b>", reply_markup=main_menu())
        return

    try:
        try:
            await transfer(message.from_user.id, row["seller_id"], symbol, price, f"NFT purchase #{listing_id}")
        except TypeError:
            await transfer(from_user_id=message.from_user.id, to_user_id=row["seller_id"], symbol=symbol, amount=price, note=f"NFT purchase #{listing_id}")
    except Exception:
        await message.answer("שגיאה בביצוע ההעברה.", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE nfty_items SET owner_id = $1 WHERE id = $2", message.from_user.id, row["item_id"])
            await conn.execute("UPDATE nfty_listings SET status='sold', sold_to=$1, sold_at=NOW() WHERE id=$2", message.from_user.id, listing_id)

    # רכישה מעדכנת חיית מחמד וירטואלית של הקונה
    await apply_pet_action(ctx.pool, message.from_user.id, "play")

    await message.answer(
        f"✅ רכישה הושלמה\nרכשת את <b>{row['title']}</b>\nעלות: <b>{price} {symbol}</b>\n\n"
        "🐾 החיה שלך קיבלה בונוס משחק על הרכישה.",
        reply_markup=main_menu()
    )
    try:
        await bot.send_message(row["seller_id"], f"💰 הפריט שלך <b>{row['title']}</b> נמכר.", reply_markup=main_menu())
    except Exception:
        pass
    # Achievement: collector
    ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "collector")
    if ach:
        await notify_achievement(message, ach)

@router.message(Command("pet"))
@router.message(F.text == "🐾 החיה שלי")
async def cmd_pet(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    pet = await get_pet(ctx.pool, message.from_user.id)
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "pet")
    await message.answer("🐾 <b>החיה הווירטואלית שלך</b>\n\n" + pet_status_text(pet), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")

@router.message(Command("feed"))
@router.message(F.text == "📊 סטטיסטיקות")
async def cmd_feed(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "feed")
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "feed")
    await message.answer("🍖 החיה שלך אכלה.\n\n" + pet_status_text(pet), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")
    # Achievement checks: pet_parent, time, quest, level
    async with ctx.pool.acquire() as conn:
        feed_count = await conn.fetchval("SELECT COUNT(*) FROM pet_action_log WHERE user_id = $1 AND action_type = $2", message.from_user.id, "feed")
    if feed_count >= 10:
        ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "pet_parent")
        if ach:
            await notify_achievement(message, ach)
    await check_time_achievements(ctx.pool, message.from_user.id, message)
    await check_pet_level_achievements(ctx.pool, message.from_user.id, message)

@router.message(Command("play"))
@router.message(F.text == "🎮 משחקים")
async def cmd_play(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "play")
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "play")
    await message.answer("🎮 שיחקת עם החיה שלך.\n\n" + pet_status_text(pet), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")
    # Achievement checks: playful, time, quest, level
    async with ctx.pool.acquire() as conn:
        play_count = await conn.fetchval("SELECT COUNT(*) FROM pet_action_log WHERE user_id = $1 AND action_type = $2", message.from_user.id, "play")
    if play_count >= 10:
        ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "playful")
        if ach:
            await notify_achievement(message, ach)
    await check_time_achievements(ctx.pool, message.from_user.id, message)
    await check_pet_level_achievements(ctx.pool, message.from_user.id, message)

@router.message(Command("learn"))
@router.message(F.text == "🤖 בינה מלאכותית")
async def cmd_learn(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "learn")
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "learn")
    await message.answer("📚 החיה שלך למדה דבר חדש.\n\n" + pet_status_text(pet), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")
    # Achievement checks: scholar, time, quest, level
    async with ctx.pool.acquire() as conn:
        learn_count = await conn.fetchval("SELECT COUNT(*) FROM pet_action_log WHERE user_id = $1 AND action_type = $2", message.from_user.id, "learn")
    if learn_count >= 10:
        ach = await check_and_unlock_achievement(ctx.pool, message.from_user.id, "scholar")
        if ach:
            await notify_achievement(message, ach)
    await check_time_achievements(ctx.pool, message.from_user.id, message)
    await check_pet_level_achievements(ctx.pool, message.from_user.id, message)

@router.message(Command("sleep"))
@router.message(F.text == "😴 שינה")
async def cmd_sleep(message: Message, bot: Bot):
    ctx = get_ctx()
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "sleep")
    completed_quest = await check_quest_completion(ctx.pool, message.from_user.id, "sleep")
    await message.answer("😴 החיה שלך הלכה לישון.\n\n" + pet_status_text(pet), reply_markup=main_menu())
    if completed_quest:
        await message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")

# ─── CBT Breathing Exercises (/breathe) ───

@router.message(Command("breathe"))
async def cmd_breathe(msg: Message):
    """Start a breathing exercise"""
    ctx = get_ctx()
    if not await is_activated(ctx.pool, msg.from_user.id):
        return await msg.answer("⚠️ Activate first with /activate")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🫁 נשימה מרגיעה (60 שניות)", callback_data="breath_calm_60")],
        [InlineKeyboardButton(text="🔥 נשימה מאנרגטית (90 שניות)", callback_data="breath_energy_90")],
        [InlineKeyboardButton(text="🧘 מדיטציה קצרה (120 שניות)", callback_data="breath_meditate_120")],
        [InlineKeyboardButton(text="💨 4-7-8 להירגעות (60 שניות)", callback_data="breath_478_60")]
    ])
    await msg.answer(
        "🌬️ <b>תרגילי נשימה — CBT</b>\n\n"
        "בחרו תרגיל. החיית המחמד שלכם תקבל בונוס אנרגיה ומצב רוח!\n\n"
        "💡 <i>טיפ: תרגול יומי משפר ריכוז, מפחית מתח, ומעלה XP</i>",
        reply_markup=kb, parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("breath_"))
async def cb_breathing(cb: CallbackQuery):
    await cb.answer()
    ctx = get_ctx()
    parts = cb.data.split("_")  # breath_calm_60
    exercise_type = parts[1]
    duration = int(parts[2])
    user_id = cb.from_user.id

    # Save session to DB
    async with ctx.pool.acquire() as conn:
        session_id = await conn.fetchval(
            "INSERT INTO breathing_sessions (user_id, exercise_type, duration_sec) VALUES ($1, $2, $3) RETURNING id",
            user_id, exercise_type, duration
        )

    # Exercise configurations
    exercises = {
        "calm": {
            "name": "נשימה מרגיעה",
            "steps": [
                ("🫁 שאפו דרך האף... 4 שניות", 4),
                ("⏸️ החזיקו... 4 שניות", 4),
                ("💨 נשפו באיטיות דרך הפה... 6 שניות", 6),
                ("😌 יופי! סיבוב נוסף...", 2),
            ],
            "rounds": 4,
            "pet_bonus": {"mood": 10, "energy": 5, "xp": 5}
        },
        "energy": {
            "name": "נשימה מאנרגטית",
            "steps": [
                ("🔥 שאפו בעוצמה דרך האף!", 3),
                ("💥 נשפו בחוזקה דרך הפה!", 3),
                ("⚡ שוב! מהר יותר!", 2),
                ("🌟 מצוין! עוד סיבוב!", 2),
            ],
            "rounds": 5,
            "pet_bonus": {"mood": 5, "energy": 15, "xp": 5}
        },
        "meditate": {
            "name": "מדיטציה קצרה",
            "steps": [
                ("🧘 עצמו עיניים. שאפו עמוק...", 5),
                ("🌊 דמיינו גל שוטף מתח...", 5),
                ("☁️ נשפו. שחררו הכל...", 5),
                ("✨ הרגישו את הרגיעה...", 5),
            ],
            "rounds": 3,
            "pet_bonus": {"mood": 15, "energy": 3, "curiosity": 5, "creativity": 8, "xp": 8}
        },
        "478": {
            "name": "טכניקת 4-7-8",
            "steps": [
                ("🫁 שאפו דרך האף... 4 שניות", 4),
                ("⏸️ החזיקו את הנשימה... 7 שניות", 7),
                ("💨 נשפו דרך הפה... 8 שניות", 8),
                ("😌 נהדר! שוב...", 2),
            ],
            "rounds": 3,
            "pet_bonus": {"mood": 12, "energy": 8, "xp": 6}
        }
    }

    ex = exercises.get(exercise_type, exercises["calm"])

    await cb.message.edit_text(
        f"🌬️ <b>{ex['name']}</b> — מתחילים!\n\n"
        f"⏱ {duration} שניות | {ex['rounds']} סיבובים\n"
        "──────────────",
        parse_mode="HTML"
    )

    for round_num in range(1, ex["rounds"] + 1):
        for step_text, wait_sec in ex["steps"]:
            await asyncio.sleep(wait_sec)
            try:
                await cb.message.edit_text(
                    f"🌬️ <b>{ex['name']}</b> — סיבוב {round_num}/{ex['rounds']}\n\n"
                    f"{step_text}\n"
                    "──────────────",
                    parse_mode="HTML"
                )
            except Exception:
                pass  # message edit rate limit - continue anyway

    # Mark completed and apply pet bonus
    async with ctx.pool.acquire() as conn:
        await conn.execute(
            "UPDATE breathing_sessions SET completed = TRUE, pet_bonus_applied = TRUE WHERE id = $1",
            session_id
        )
        # Apply pet bonus
        pet = await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)
        if pet:
            bonus = ex["pet_bonus"]
            await conn.execute(
                """UPDATE virtual_pets SET
                    mood = LEAST(100, mood + $2),
                    energy = LEAST(100, energy + $3),
                    xp = xp + $4,
                    curiosity = LEAST(100, curiosity + COALESCE($5, 0)),
                    creativity = LEAST(100, creativity + COALESCE($6, 0)),
                    updated_at = NOW()
                WHERE user_id = $1""",
                user_id,
                bonus.get("mood", 0),
                bonus.get("energy", 0),
                bonus.get("xp", 0),
                bonus.get("curiosity", 0),
                bonus.get("creativity", 0)
            )

        # Count total sessions
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM breathing_sessions WHERE user_id = $1 AND completed = TRUE", user_id
        )

    bonus_text = " | ".join(f"+{v} {k}" for k, v in ex["pet_bonus"].items())
    await cb.message.edit_text(
        f"✅ <b>{ex['name']} — הושלם!</b>\n\n"
        f"🎉 מעולה! סיימתם {ex['rounds']} סיבובים\n"
        f"🐾 בונוס לחיית המחמד: {bonus_text}\n"
        f"📊 סה\"כ תרגילים שהשלמתם: {total}\n\n"
        "💡 תרגול יומי מוריד מתח ומעלה XP!\n"
        "הקלידו /breathe לתרגיל נוסף",
        parse_mode="HTML"
    )
    await log_event(ctx.pool, "breathing_completed", user_id, "breathing", str(session_id), {"type": exercise_type, "duration": duration})

    # Check quest completion for breathing
    completed_quest = await check_quest_completion(ctx.pool, user_id, "breathing")
    if completed_quest:
        await cb.message.answer(f"🎉 משימה הושלמה: {completed_quest['quest_title']}! +{completed_quest['xp_reward']} XP")

    # Achievement checks for breathing
    ach = await check_and_unlock_achievement(ctx.pool, user_id, "first_breath")
    if ach:
        await notify_achievement(cb, ach)
    if total >= 10:
        ach = await check_and_unlock_achievement(ctx.pool, user_id, "breath_master")
        if ach:
            await notify_achievement(cb, ach)
    await check_time_achievements(ctx.pool, user_id, cb)

# ─── Daily Quests (/quests) ───

QUEST_POOL = [
    {"key": "feed_pet", "title": "🍖 האכל את החיה", "desc": "השתמש בפקודה /feed פעם אחת", "xp": 10, "check_action": "feed"},
    {"key": "play_pet", "title": "🎮 שחק עם החיה", "desc": "השתמש בפקודה /play פעם אחת", "xp": 10, "check_action": "play"},
    {"key": "learn_pet", "title": "📚 למד את החיה", "desc": "השתמש בפקודה /learn פעם אחת", "xp": 15, "check_action": "learn"},
    {"key": "breathe_once", "title": "🫁 תרגיל נשימה", "desc": "השלם תרגיל נשימה אחד (/breathe)", "xp": 20, "check_action": "breathing"},
    {"key": "check_wallet", "title": "💰 בדוק ארנק", "desc": "בדוק את היתרה שלך (/wallet)", "xp": 5, "check_action": "wallet"},
    {"key": "share_link", "title": "🔗 שתף הפניה", "desc": "שתף את הלינק שלך (/share)", "xp": 15, "check_action": "share"},
    {"key": "browse_market", "title": "🛍️ עיין בשוק", "desc": "עיין בפריטים (/browse)", "xp": 10, "check_action": "browse"},
    {"key": "pet_status", "title": "🐾 בדוק חיה", "desc": "בדוק את מצב החיה (/pet)", "xp": 5, "check_action": "pet"},
    {"key": "sleep_pet", "title": "😴 שים את החיה לישון", "desc": "השתמש בפקודה /sleep", "xp": 10, "check_action": "sleep"},
    {"key": "breathe_twice", "title": "🧘 תרגל פעמיים", "desc": "השלם 2 תרגילי נשימה היום", "xp": 30, "check_action": "breathing_x2"},
]

async def get_or_assign_quests(pool, user_id):
    """Get today's quests for user, assign if none exist"""
    today = date.today()
    async with pool.acquire() as conn:
        quests = await conn.fetch(
            "SELECT * FROM daily_quests WHERE user_id = $1 AND assigned_date = $2 ORDER BY id",
            user_id, today
        )
        if not quests:
            # Assign 3 random quests
            chosen = random.sample(QUEST_POOL, min(3, len(QUEST_POOL)))
            for q in chosen:
                await conn.execute(
                    """INSERT INTO daily_quests (user_id, quest_key, quest_title, quest_desc, xp_reward, assigned_date)
                    VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT DO NOTHING""",
                    user_id, q["key"], q["title"], q["desc"], q["xp"], today
                )
            quests = await conn.fetch(
                "SELECT * FROM daily_quests WHERE user_id = $1 AND assigned_date = $2 ORDER BY id",
                user_id, today
            )
    return quests

async def check_quest_completion(pool, user_id, action_type):
    """Check if an action completes a quest, auto-claim if so"""
    today = date.today()
    async with pool.acquire() as conn:
        quests = await conn.fetch(
            "SELECT * FROM daily_quests WHERE user_id = $1 AND assigned_date = $2 AND completed = FALSE",
            user_id, today
        )
        for quest in quests:
            qkey = quest["quest_key"]
            match = False
            if action_type == "feed" and qkey == "feed_pet": match = True
            elif action_type == "play" and qkey == "play_pet": match = True
            elif action_type == "learn" and qkey == "learn_pet": match = True
            elif action_type == "sleep" and qkey == "sleep_pet": match = True
            elif action_type == "breathing" and qkey == "breathe_once": match = True
            elif action_type == "wallet" and qkey == "check_wallet": match = True
            elif action_type == "share" and qkey == "share_link": match = True
            elif action_type == "browse" and qkey == "browse_market": match = True
            elif action_type == "pet" and qkey == "pet_status": match = True
            elif action_type == "breathing" and qkey == "breathe_twice":
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM breathing_sessions WHERE user_id = $1 AND completed = TRUE AND created_at::date = $2",
                    user_id, today
                )
                if count >= 2: match = True

            if match:
                await conn.execute(
                    "UPDATE daily_quests SET completed = TRUE, completed_at = NOW() WHERE id = $1",
                    quest["id"]
                )
                # Award XP
                await conn.execute(
                    "UPDATE virtual_pets SET xp = xp + $2, mood = LEAST(100, mood + 3), updated_at = NOW() WHERE user_id = $1",
                    user_id, quest["xp_reward"]
                )
                # Achievement: quest_rookie (always), quest_master (if all 3 done today)
                await check_and_unlock_achievement(pool, user_id, "quest_rookie")
                completed_today = await conn.fetchval(
                    "SELECT COUNT(*) FROM daily_quests WHERE user_id = $1 AND assigned_date = $2 AND completed = TRUE",
                    user_id, today
                )
                if completed_today >= 3:
                    await check_and_unlock_achievement(pool, user_id, "quest_master")
                return quest  # Return the completed quest for notification
    return None

@router.message(Command("quests"))
async def cmd_quests(msg: Message):
    """Show today's daily quests"""
    ctx = get_ctx()
    if not await is_activated(ctx.pool, msg.from_user.id):
        return await msg.answer("⚠️ Activate first with /activate")

    quests = await get_or_assign_quests(ctx.pool, msg.from_user.id)

    lines = ["🎯 <b>משימות יומיות</b>\n"]
    total_xp = 0
    completed = 0
    for q in quests:
        if q["completed"]:
            lines.append(f"  ✅ <s>{q['quest_title']}</s> (+{q['xp_reward']} XP)")
            total_xp += q["xp_reward"]
            completed += 1
        else:
            lines.append(f"  ⬜ {q['quest_title']}")
            lines.append(f"     <i>{q['quest_desc']}</i> — {q['xp_reward']} XP")

    lines.append(f"\n📊 הושלמו: {completed}/{len(quests)}")
    if completed == len(quests):
        lines.append("🏆 כל המשימות הושלמו! חזרו מחר למשימות חדשות")
    else:
        lines.append(f"💰 XP שנותר: {sum(q['xp_reward'] for q in quests if not q['completed'])}")

    lines.append("\n🔄 המשימות מתחדשות כל יום בחצות")
    await msg.answer("\n".join(lines), parse_mode="HTML")

@router.message(Command("achievements"))
async def cmd_achievements(msg: Message):
    if not await is_activated(get_ctx().pool, msg.from_user.id):
        return await msg.answer("⚠️ Activate first with /activate")

    async with get_ctx().pool.acquire() as conn:
        unlocked = await conn.fetch(
            "SELECT achievement_key, unlocked_at FROM achievements WHERE user_id = $1 ORDER BY unlocked_at",
            msg.from_user.id
        )

    unlocked_keys = {r["achievement_key"] for r in unlocked}

    lines = ["🏆 <b>הישגים</b>\n"]
    for key, ach in ACHIEVEMENTS.items():
        if key in unlocked_keys:
            lines.append(f"  ✅ {ach['title']} — {ach['desc']} (+{ach['xp']} XP)")
        else:
            lines.append(f"  🔒 {ach['title']} — {ach['desc']}")

    lines.append(f"\n📊 נפתחו: {len(unlocked_keys)}/{len(ACHIEVEMENTS)}")
    await msg.answer("\n".join(lines), parse_mode="HTML")

@router.message()
async def fallback(message: Message):
    await message.answer(
        "לא הבנתי את הפקודה.\n\n"
        "תוכלו להשתמש בפקודות הבאות:\n"
        "/start | /browse | /sell | /buy  | /my_items | /my_listings | /wallet | /pet | /feed | /play | /learn | /sleep | /help | /faq | /share",
        reply_markup=main_menu()
    )

async def on_startup(bot: Bot):
    ctx = get_ctx()
    await bootstrap_db(ctx.pool)
    log.info("startup complete")

async def on_shutdown(bot: Bot):
    ctx = get_ctx()
    await ctx.session.close()
    await ctx.pool.close()
    log.info("shutdown complete")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN or NFTY_MADNESS_TOKEN")

    pool = await create_pool()
    session = await create_http_session()
    ctx = AppContext(pool=pool, session=session)

    global APP_CTX
    APP_CTX = ctx

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    storage = RedisStorage.from_url(REDIS_URL)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        me = await bot.get_me()
        await init_coordination_for_bot(
            bot, dp,
            name="nfty-bot",
            username=me.username,
        )
    except Exception as e:
        log.warning("coordination init failed: %s", e)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
