import asyncio, os, datetime
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        # Auto-migration: ensures columns exist
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        print("✅ DB Migration OK")
    print("✅ DB Pool ready")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, referral_code)
            VALUES (\, \, \) ON CONFLICT (telegram_id) 
            DO UPDATE SET username = \, last_seen = NOW()
        """, uid, username, f"SLH{uid}")

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📊 Status", callback_data="status"),
         types.InlineKeyboardButton(text="⭐ Points", callback_data="points")],
        [types.InlineKeyboardButton(text="✅ Check-in", callback_data="checkin"),
         types.InlineKeyboardButton(text="⚡ Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="💎 Upgrade", callback_data="upgrade"),
         types.InlineKeyboardButton(text="🤝 Donate", callback_data="donate")],
        [types.InlineKeyboardButton(text="💰 Crypto", callback_data="crypto"),
         types.InlineKeyboardButton(text="🔗 Referral", callback_data="referral")],
        [types.InlineKeyboardButton(text="📋 Tasks", callback_data="tasks"),
         types.InlineKeyboardButton(text="👛 Wallet", callback_data="wallet")],
        [types.InlineKeyboardButton(text="🔮 Oracle", callback_data="oracle"),
         types.InlineKeyboardButton(text="☮️ Peace", callback_data="peace")],
        [types.InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"),
         types.InlineKeyboardButton(text="👑 Admin", callback_data="admin")],
        [types.InlineKeyboardButton(text="❓ Help", callback_data="help")]
    ])

# ====================== Core Commands (from SSoT) ======================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("🧠 <b>SLH Spark AI v3.4</b>\n\nברוך הבא!", reply_markup=main_menu())

@dp.message(Command("tap"))
async def cmd_tap(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET 
                energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int),
                last_energy_update = NOW()
            WHERE telegram_id = \
        """, uid)
        user = await conn.fetchrow("SELECT energy, points, tier FROM users WHERE telegram_id=\", uid)
        if not user or user['energy'] < 5:
            return await msg.answer("❌ אין מספיק אנרגיה. חכה כמה שניות.")
        multiplier = 2.0 if user['tier'] == 'business' else 1.5 if user['tier'] == 'pro' else 1.0
        gain = int(5 * multiplier)
        new_energy = user['energy'] - 5
        new_points = user['points'] + gain
        await conn.execute("UPDATE users SET energy=\, points=\ WHERE telegram_id=\", new_energy, new_points, uid)
    await msg.answer(f"⚡ +{gain} נקודות! סה\"כ: {new_points} | אנרגיה: {new_energy}")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=\ AND created_at = CURRENT_DATE", uid)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES (\,\)", uid, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=\ AND created_at = CURRENT_DATE", uid)
        text = "📋 משימות יומיות:\n\n" + "\n".join(f"{'✅' if r['done'] else '❌'} {r['description']} (ID:{r['id']})" for r in rows)
        await msg.answer(text + "\n\nהשתמש ב /done [ID]")

# תוכל להוסיף את שאר הפקודות מה-SSoT בהמשך...

@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    if data == "tap":
        await cmd_tap(call.message)
    elif data == "status":
        await call.message.answer("📊 Status - בהמשך...")
    else:
        await call.message.answer("✨ Feature coming soon")

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 SLH Spark AI v3.4 running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
