import asyncio, os, datetime
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TON_WALLET = os.getenv("TON_WALLET")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=None))
dp = Dispatcher()
pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                points INT DEFAULT 0,
                streak INT DEFAULT 0,
                last_checkin DATE,
                tier TEXT DEFAULT 'free',
                balance REAL DEFAULT 0,
                referral_code TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        print("? DB ready")

async def ensure_user(uid, username):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username) VALUES ($1, $2)
            ON CONFLICT (telegram_id) DO NOTHING
        """, uid, username)

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="?? Status", callback_data="status"),
         types.InlineKeyboardButton(text="? Points", callback_data="points")],
        [types.InlineKeyboardButton(text="? Check-in", callback_data="checkin"),
         types.InlineKeyboardButton(text="? Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="?? Upgrade", callback_data="upgrade"),
         types.InlineKeyboardButton(text="?? Donate", callback_data="donate")],
    ])

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer(
        "?? SLH Spark AI v4.5\n\n? All systems stable\n? Tap, Points, Check-in, Upgrade",
        reply_markup=main_menu()
    )

@dp.message(Command("status"))
async def cmd_status(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, streak, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"?? Points: {user['points']}\n?? Streak: {user['streak']}\n?? Tier: {user['tier']}")
        else:
            await msg.answer("Please /start first")

@dp.message(Command("points"))
async def cmd_points(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        if pts is None:
            await msg.answer("Please /start first")
        else:
            await msg.answer(f"? Points: {pts}")

@dp.message(Command("checkin"))
async def cmd_checkin(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    today = datetime.date.today()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT last_checkin, points, streak FROM users WHERE telegram_id=$1", uid)
        if row and row['last_checkin'] == today:
            await msg.answer("? Already checked in today!")
            return
        new_streak = (row['streak'] + 1) if row and row['streak'] else 1
        new_points = (row['points'] if row else 0) + 10
        await conn.execute("UPDATE users SET points=$1, streak=$2, last_checkin=$3 WHERE telegram_id=$4",
                           new_points, new_streak, today, uid)
        await msg.answer(f"? +10 points! Total: {new_points} | Streak: {new_streak}")

@dp.message(Command("tap"))
async def cmd_tap(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        if pts is None:
            await msg.answer("Please /start first")
            return
        new_pts = pts + 5
        await conn.execute("UPDATE users SET points=$1 WHERE telegram_id=$2", new_pts, uid)
        await msg.answer(f"? +5 points! Total: {new_pts}")

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: types.Message):
    await msg.answer(f"?? Pro: 9.9 TON/mo\n?? Business: 29 TON/mo\n\nSend TON to:\n{TON_WALLET}\nwith your ID: {msg.from_user.id}")

@dp.message(Command("donate"))
async def cmd_donate(msg: types.Message):
    await msg.answer(f"?? TON: {TON_WALLET}\n?? USDT (TRC20): TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ")

async def ask_groq(prompt):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
            )
            data = resp.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            else:
                return f"?? Groq response: {data}"
    except Exception as e:
        return f"?? AI error: {str(e)[:100]}"

@dp.message()
async def ai_fallback(msg: types.Message):
    if msg.text and msg.text.startswith('/'):
        return
    await bot.send_chat_action(msg.chat.id, "typing")
    reply = await ask_groq(msg.text)
    await msg.answer(reply[:2000])

@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    if data == "status": await cmd_status(call.message)
    elif data == "points": await cmd_points(call.message)
    elif data == "checkin": await cmd_checkin(call.message)
    elif data == "tap": await cmd_tap(call.message)
    elif data == "upgrade": await cmd_upgrade(call.message)
    elif data == "donate": await cmd_donate(call.message)
    else: await call.message.answer("? Unknown command")

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    print("?? SLH Spark AI v4.5 running")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
