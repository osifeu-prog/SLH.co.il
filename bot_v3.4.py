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

# ====================== DB + AUTO MIGRATION ======================
async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        # Auto Migration - זה ירוץ בכל הפעלה
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        print("✅ DB Migration completed successfully")
    print("✅ DB Pool ready")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, referral_code)
            VALUES (, , )
            ON CONFLICT (telegram_id) DO UPDATE 
            SET username = , last_seen = NOW()
        """, uid, username, f"SLH{uid}")

# ====================== Keyboards ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="status"),
         InlineKeyboardButton(text="⭐ Points", callback_data="points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="checkin"),
         InlineKeyboardButton(text="⚡ Tap-to-Earn", callback_data="tap")],
        [InlineKeyboardButton(text="💎 Upgrade", callback_data="upgrade"),
         InlineKeyboardButton(text="🤝 Donate", callback_data="donate")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="crypto"),
         InlineKeyboardButton(text="👑 Admin", callback_data="admin")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")],
    ])

# ====================== Basic Commands ======================
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("🧠 <b>SLH Spark AI v3.4</b>\n\nברוך הבא!", parse_mode=ParseMode.HTML, reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer("פקודות זמינות:\n/start /status /points /checkin /tap /upgrade /donate /crypto /admin /referral")

# Callback handler
@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    await call.answer()
    data = call.data
    if data == "status":
        await call.message.answer("📊 Status - Coming soon")
    elif data == "tap":
        await call.message.answer("⚡ +5 points! (Tap system active)")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
