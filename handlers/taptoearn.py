import random
from datetime import datetime, timedelta

from aiogram import types
from aiogram.fsm.context import FSMContext

from database import db_pool
from config import REDIS_URL
import redis

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def handle_tap_command(message: types.Message):
    user_id = message.from_user.id
    today = datetime.now().date().isoformat()
    tap_key = f"tap:{user_id}:{today}"
    
    taps_today = redis_client.get(tap_key)
    if taps_today and int(taps_today) >= 100:
        await message.reply("📛 הגעת למקסימום ההקשות היומי (100). בוא מחר להמשיך להרוויח!")
        return
    
    points = random.randint(1, 5)
    streak_key = f"tap_streak:{user_id}"
    last_tap = redis_client.get(streak_key)
    
    if last_tap and (datetime.now() - datetime.fromisoformat(last_tap)) < timedelta(hours=24):
        streak = redis_client.incr(f"tap_streak_count:{user_id}")
        bonus = min(streak // 10, 50)
        points += bonus
    else:
        redis_client.set(f"tap_streak_count:{user_id}", 1)
        streak = 1
    
    redis_client.setex(streak_key, 60 * 60 * 24, datetime.now().isoformat())
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET points = points +  WHERE telegram_id = ",
            points, user_id
        )
    
    redis_client.incrby(tap_key, 1)
    redis_client.expire(tap_key, 60 * 60 * 24)
    
    await message.reply(
        f"👆 *Tap!* הרווחת {points} נקודות!\n"
        f"🔥 *Streak:* {streak} ימים\n"
        f"📊 *היום:* {int(taps_today or 0)+1}/100 הקשות\n"
        f"🎯 המשך להקיש כדי לצבור בונוסים!",
        parse_mode="Markdown"
    )
