import os

bot_code = r'''import asyncio, logging, os, json, datetime, random
import asyncpg
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import groq

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_TELEGRAM_IDS", "224223270").split(",")]
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
WEBAPP_URL = "https://slh-ai-bot-production.up.railway.app/webapp/index.html"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, username TEXT, points INT DEFAULT 0, streak INT DEFAULT 0, last_checkin DATE, balance REAL DEFAULT 0, tier TEXT DEFAULT 'free', energy INT DEFAULT 100, last_energy TIMESTAMP DEFAULT NOW(), created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS identity (user_id BIGINT PRIMARY KEY, name TEXT, vision TEXT, values TEXT[])""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT, done BOOLEAN DEFAULT FALSE, created_at DATE DEFAULT CURRENT_DATE)""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS crm_notes (id SERIAL PRIMARY KEY, user_id BIGINT, note TEXT, created_at TIMESTAMP DEFAULT NOW())""")

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="?? Status", callback_data="status"), types.InlineKeyboardButton(text="? Points", callback_data="points"))
    builder.row(types.InlineKeyboardButton(text="? Check-in", callback_data="checkin"), types.InlineKeyboardButton(text="? Tap-to-Earn", callback_data="tap"))
    builder.row(types.InlineKeyboardButton(text="?? Crypto", callback_data="crypto"), types.InlineKeyboardButton(text="?? Donate", callback_data="donate"))
    builder.row(types.InlineKeyboardButton(text="?? Guide", callback_data="guide"), types.InlineKeyboardButton(text="? Help", callback_data="help"))
    builder.row(types.InlineKeyboardButton(text="?? Oracle", callback_data="oracle"), types.InlineKeyboardButton(text="?? Peace Game", callback_data="peace"))
    builder.row(types.InlineKeyboardButton(text="?? Upgrade", callback_data="upgrade"), types.InlineKeyboardButton(text="?? Tasks", callback_data="tasks"))
    builder.row(types.InlineKeyboardButton(text="?? Buy", callback_data="buy"), types.InlineKeyboardButton(text="?? Pay", callback_data="pay"))
    builder.row(types.InlineKeyboardButton(text="?? Identity", callback_data="identity"), types.InlineKeyboardButton(text="?? Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    return builder.as_markup()

def back_button():
    return InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="?? Main Menu", callback_data="start")).as_markup()

@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer("? Registered! Use /identity to set your profile.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    logo = ("????????????????????????????????????\n"
            "?     ???????????     ???  ???     ?\n"
            "?     ???????????     ???  ???     ?\n"
            "?     ???????????     ????????     ?\n"
            "?     ???????????     ????????     ?\n"
            "?     ???????????????????  ???     ?\n"
            "?     ???????????????????  ???     ?\n"
            "?   ?? SLH SPARK AI   v3.3        ?\n"
            "????????????????????????????????????")
    await message.answer(logo, parse_mode=None)
    await message.answer("SLH Spark AI v3.3\n\nWelcome, Osif!\nChoose an option:", reply_markup=main_menu_keyboard())

@dp.callback_query(F.data == "start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.message.answer("Choose an option:", reply_markup=main_menu_keyboard())
    await callback.answer()

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (telegram_id, username) VALUES ($1, $2) ON CONFLICT DO NOTHING", uid, username)

# ??? TAP-TO-EARN ???
@dp.message(Command("tap"))
async def cmd_tap(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT energy, points FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: return await message.answer("Register first with /register")
        energy = user['energy']
        if energy < 5: return await message.answer("? Not enough energy. Wait for recharge.")
        await conn.execute("UPDATE users SET energy = energy - 5, points = points + 5 WHERE telegram_id=$1", message.from_user.id)
        new_pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", message.from_user.id)
        await message.answer(f"? +5 points! Total: {new_pts} pts | Energy: {energy-5}")

# ??? DAILY TASKS ???
@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", message.from_user.id)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES ($1,$2)", message.from_user.id, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", message.from_user.id)
        text = "?? Daily Tasks:\n\n"
        for r in rows:
            icon = "?" if r['done'] else "?"
            text += f"{icon} {r['description']} (ID:{r['id']})\n"
        text += "\nUse /done [task_id] to complete."
        await message.answer(text)

@dp.message(Command("done"))
async def cmd_done(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2: return await message.answer("Usage: /done [task_id]")
    tid = parts[1]
    async with pool.acquire() as conn:
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id=$1 AND user_id=$2", int(tid), message.from_user.id)
        if not task: return await message.answer("Task not found.")
        if task['done']: return await message.answer("Already completed.")
        await conn.execute("UPDATE tasks SET done = TRUE WHERE id=$1", int(tid))
        await conn.execute("UPDATE users SET points = points + 10 WHERE telegram_id=$1", message.from_user.id)
        await message.answer(f"? Task completed! +10 points.")

# ??? CRM ???
@dp.message(Command("addcustomer"))
async def cmd_addcustomer(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3: return await message.answer("Usage: /addcustomer [name] [phone]", parse_mode=None)
    name, phone = parts[1], parts[2]
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO crm_notes (user_id, note) VALUES ($1,$2)", message.from_user.id, f"CUSTOMER: {name} | PHONE: {phone}")
    await message.answer(f"Customer {name} added!")

@dp.message(Command("customers"))
async def cmd_customers(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE 'CUSTOMER:%' ORDER BY created_at DESC LIMIT 20", message.from_user.id)
        if not rows: return await message.answer("No customers yet.")
        text = "Your Customers:\n\n"
        for i, r in enumerate(rows, 1): text += f"{i}. {r['note']} | {r['created_at'].strftime('%d/%m/%Y')}\n"
        await message.answer(text)

@dp.message(Command("addnote"))
async def cmd_addnote(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3: return await message.answer("Usage: /addnote [customer_id] [text]", parse_mode=None)
    cid, note = parts[1], parts[2]
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO crm_notes (user_id, note) VALUES ($1,$2)", message.from_user.id, f"NOTE:{cid}:{note}")
    await message.answer("Note added.")

@dp.message(Command("notes"))
async def cmd_notes(message: types.Message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2: return await message.answer("Usage: /notes [customer_id]", parse_mode=None)
    cid = parts[1]
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE $2 ORDER BY created_at DESC LIMIT 10", message.from_user.id, f"NOTE:{cid}:%")
        if not rows: return await message.answer("No notes.")
        text = f"Notes for {cid}:\n\n"
        for r in rows: text += f"[{r['created_at'].strftime('%H:%M')}] {r['note'].split(':',2)[-1]}\n"
        await message.answer(text)

# ??? WALLET ???
@dp.message(Command("wallet"))
async def cmd_wallet(msg):
    async with pool.acquire() as conn:
        bal = await conn.fetchval("SELECT balance FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id=$1", msg.from_user.id) or "free"
        await msg.answer(f"?? Wallet\nBalance: {bal:.2f} TON\nTier: {tier.upper()}", reply_markup=back_button())

@dp.message(Command("simdeposit"))
async def cmd_simdeposit(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2: return await message.answer("Usage: /simdeposit [amount]")
    try: amount = float(parts[1])
    except: return await message.answer("Invalid amount.")
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE telegram_id = $2", amount, message.from_user.id)
        new_balance = await conn.fetchval("SELECT balance FROM users WHERE telegram_id = $1", message.from_user.id)
        await conn.execute("UPDATE users SET tier = CASE WHEN $1 >= 29 THEN 'business' WHEN $1 >= 9.9 THEN 'pro' ELSE 'free' END WHERE telegram_id = $2", new_balance, message.from_user.id)
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id = $1", message.from_user.id)
    await message.answer(f"? Simulated deposit: {amount} TON\nBalance: {new_balance:.2f} TON\nTier: {tier.upper()}")

# ??? VIP ???
@dp.message(Command("vip"))
async def cmd_vip(msg):
    await msg.answer(
        f"?? SLH VIP Group\n\n"
        f"?? Private Trading Community\n"
        f"?? Cost: 18 ILS (one-time)\n\n"
        f"What you get:\n"
        f"?? Daily trading signals\n"
        f"?? Private chat with experts\n"
        f"?? Exclusive rewards\n"
        f"?? Priority support\n\n"
        f"How to join:\n"
        f"1. Send 18 ILS worth of TON to:\n{TON_WALLET}\n"
        f"2. In memo, write: VIP + your Telegram ID\n"
        f"3. You'll receive an invite link automatically!",
        parse_mode=None
    )

@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    ref_link = f"https://t.me/SLH_Claude_bot?start=ref{message.from_user.id}"
    await message.answer(f"?? Your Invite Link:\n{ref_link}\n\n?? Share this link to invite friends!\n? You earn 50 points per friend!")

# ??? AI ???
@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":message.text}], max_tokens=400, temperature=0.7)
        answer = resp.choices[0].message.content
        await message.answer(answer[:4096])
    except Exception as e:
        await message.answer(f"?? AI error: {str(e)[:200]}")

# ??? CALLBACK ROUTER ???
@dp.callback_query()
async def main_callback(callback: types.CallbackQuery):
    data = callback.data
    if data == "status": await callback.message.answer("System online")
    elif data == "points": await callback.message.answer("Use /points")
    elif data == "checkin": await callback.message.answer("Use /checkin")
    elif data == "tap": await cmd_tap(callback.message)
    elif data == "crypto": await callback.message.answer("Use /crypto")
    elif data == "donate": await callback.message.answer("Use /donate")
    elif data == "guide": await callback.message.answer("Use /guide")
    elif data == "help": await callback.message.answer("Use /help")
    elif data == "oracle": await callback.message.answer("Oracle coming soon")
    elif data == "peace": await callback.message.answer("Peace Game coming soon")
    elif data == "upgrade": await callback.message.answer("Use /upgrade")
    elif data == "tasks": await cmd_tasks(callback.message)
    elif data == "buy": await callback.message.answer("?? Buy: Enter product ID")
    elif data == "pay": await callback.message.answer("?? Payment options: /invoice /request /split")
    elif data == "identity": await callback.message.answer("?? Use /identity command to set your profile.")
    await callback.answer()

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(bot_code)

print("bot.py created successfully.")

