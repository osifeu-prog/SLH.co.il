# === bot_v3.4_full.py - מלא + יציב ===
import asyncio, os, datetime
import asyncpg
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
pool = None

# ====================== DB ======================
async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        print("✅ DB Migration completed")
    print("✅ DB Pool ready")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, referral_code)
            VALUES (, , ) ON CONFLICT (telegram_id) 
            DO UPDATE SET username = , last_seen = NOW()
        """, uid, username, f"SLH{uid}")

async def update_energy(uid):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int),
            last_energy_update = NOW() WHERE telegram_id = 
        """, uid)

def get_multiplier(tier):
    return 2.0 if tier == "business" else 1.5 if tier == "pro" else 1.0

# ====================== Keyboards ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="status"), InlineKeyboardButton(text="⭐ Points", callback_data="points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="checkin"), InlineKeyboardButton(text="⚡ Tap", callback_data="tap")],
        [InlineKeyboardButton(text="💎 Upgrade", callback_data="upgrade"), InlineKeyboardButton(text="🤝 Donate", callback_data="donate")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="crypto"), InlineKeyboardButton(text="🔗 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="📋 Tasks", callback_data="tasks"), InlineKeyboardButton(text="👛 Wallet", callback_data="wallet")],
        [InlineKeyboardButton(text="🔮 Oracle", callback_data="oracle"), InlineKeyboardButton(text="☮️ Peace", callback_data="peace")],
        [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"), InlineKeyboardButton(text="👑 Admin", callback_data="admin")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")]
    ])

# ====================== Core Commands ======================
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("🧠 <b>SLH Spark AI v3.4</b>\n\nברוך הבא!", parse_mode=ParseMode.HTML, reply_markup=main_menu())

@dp.message(Command("tap"))
async def cmd_tap(msg: Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    await update_energy(uid)
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT energy, points, tier FROM users WHERE telegram_id=", uid)
        if not user or user['energy'] < 5:
            return await msg.answer("❌ אין מספיק אנרגיה. חכה כמה שניות.")
        gain = int(5 * get_multiplier(user['tier']))
        new_energy = user['energy'] - 5
        new_points = user['points'] + gain
        await conn.execute("UPDATE users SET energy=, points=, last_energy_update=NOW() WHERE telegram_id=", new_energy, new_points, uid)
    await msg.answer(f"⚡ +{gain} נקודות! סה\"כ: {new_points} | אנרגיה: {new_energy}")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id= AND created_at = CURRENT_DATE", uid)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES (,)", uid, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id= AND created_at = CURRENT_DATE", uid)
        text = "📋 משימות יומיות:\n\n" + "\n".join(f"{'✅' if r['done'] else '❌'} {r['description']} (ID:{r['id']})" for r in rows)
        await msg.answer(text + "\n\nהשתמש ב /done [ID]")

# ... (שאר הפקודות יתווספו בהמשך)

@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    await call.answer()
    data = call.data
    msg = call.message
    if data == "tap":
        await cmd_tap(msg)
    elif data == "status":
        await msg.answer("📊 Status - תכונה בפיתוח")
    else:
        await msg.answer("✨ Feature coming soon")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 SLH Spark AI v3.4 is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
