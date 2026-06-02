import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional

import redis
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import REDIS_URL, ADMIN_ID, TON_WALLET
from database import db_pool

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class PremiumStates(StatesGroup):
    waiting_for_tx_hash = State()

async def check_premium(user_id: int) -> bool:
    premium_until = redis_client.get(f"premium:{user_id}")
    if premium_until:
        expiry = datetime.fromisoformat(premium_until)
        if expiry > datetime.now():
            return True
        else:
            redis_client.delete(f"premium:{user_id}")
    return False

async def activate_premium(user_id: int, months: int = 1):
    expiry = datetime.now() + timedelta(days=30 * months)
    redis_client.setex(f"premium:{user_id}", 60 * 60 * 24 * 30 * months, expiry.isoformat())
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO premium_users (user_id, expires_at) VALUES (, ) "
            "ON CONFLICT (user_id) DO UPDATE SET expires_at = ",
            user_id, expiry
        )

async def handle_premium_command(message: types.Message):
    text = (
        "💎 *מסלולי Premium של SLH Spark AI*\n\n"
        "🌟 *Pro*  9.9 TON/חודש\n"
        "• פי 2 נקודות\n"
        "• התראות בזמן אמת\n"
        "• תמיכה עדיפות\n\n"
        "🏢 *Business*  29 TON/חודש\n"
        "• כל היתרונות של Pro\n"
        "• CRM מובנה\n"
        "• broadcast לעד 1000 עוקבים\n\n"
        f"📮 שלחו בדיוק 9.9 TON (או 29 TON) לכתובת:\n{TON_WALLET}\n"
        "ואז לחצו /confirm [transaction_hash]\n\n"
        "🔍 איך מוצאים hash? בענן שלכם (Tonkeeper, Tonhub)  לחצו על העסקה, העתיקו 'Transaction ID'."
    )
    await message.reply(text, parse_mode="Markdown")

async def handle_confirm_command(message: types.Message):
    parts = message.get_args().split()
    if not parts:
        await message.reply("❗ שלח /confirm ואת ה-hash של העסקה, למשל:\n/confirm 0a1b2c3d...")
        return
    tx_hash = parts[0]
    if tx_hash.startswith("0") and len(tx_hash) > 20:
        await activate_premium(message.from_user.id, months=1)
        await message.reply("✅ *הפרימיום שלך הופעל!* עכשיו אתה מקבל פי 2 נקודות, תמיכה עדיפות ועוד.", parse_mode="Markdown")
        await message.bot.send_message(ADMIN_ID, f"🎉 משתמש {message.from_user.id} (@{message.from_user.username}) הפעיל פרימיום Pro!")
    else:
        await message.reply("❓ לא הצלחנו לאמת את התשלום. נסה שוב או צור קשר עם התמיכה.")
