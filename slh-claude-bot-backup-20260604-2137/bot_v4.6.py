import asyncio, os, datetime, json
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
pool = None

# ====================== AI Smart Router ======================
async def ask_ai(prompt: str) -> str:
    if not prompt or len(prompt.strip()) < 2:
        return "×©××œ ××•×ª×™ ×ž×©×”×•, ×× ×™ ×›××Ÿ ×œ×¢×–×•×¨ ðŸ˜Š"
    prompt_lower = prompt.lower()
    length = len(prompt)
    is_complex = any(kw in prompt_lower for kw in ["×”×¡×‘×¨", "×œ×ž×”", "××™×š", "× ×™×ª×•×—", "×ª×›× ×Ÿ", "××¡×˜×¨×˜×’×™×”", "×”×©×•×•×”", "×ž×“×•×¢", "×¤×¨×˜", "×¦×¢×“×™×"])
    is_code = any(kw in prompt_lower for kw in ["×§×•×“", "python", "sql", "function", "class", "debug", "×©×’×™××”", "×›×ª×•×‘"])
    is_long = length > 120
    if is_code or (is_complex and is_long):
        model, temp = "llama-3.1-70b-versatile", 0.7
    else:
        model, temp = "llama-3.1-8b-instant", 0.8
    system_prompt = """××ª×” SLH Spark AI v4.6 â€” ×¢×•×–×¨ ××™×©×™ ×—×›×, ×™×“×™×“×•×ª×™, ×©× ×•×Ÿ ×•×ž×“×•×™×§ ×‘×¢×‘×¨×™×ª.
××ª×” ×—×œ×§ ×ž×ž×¢×¨×›×ª SLH ×¢× × ×§×•×“×•×ª, ×× ×¨×’×™×”, Tap, ×ž×©×™×ž×•×ª, TON, CRM ×•×—× ×•×ª ×ž×•×¦×¨×™×.
×¢× ×” ×‘×¦×•×¨×” ×˜×‘×¢×™×ª ×›×ž×• ×—×‘×¨ ×—×›×, ×œ× ×›×ž×• ×¨×•×‘×•×˜. ×§×¦×¨ + ×ž×•×¢×™×œ."""
    try:
        import groq
        client = groq.Client(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            model=model, temperature=temp, max_tokens=950, top_p=0.95
        )
        response = completion.choices[0].message.content.strip()
        print(f"ðŸ”€ [Router] {model} | Length: {length}")
        return response
    except Exception as e:
        print(f"Groq Error: {e}")
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            return resp.text.strip()
        except:
            pass
    return "×”-AI ×§×¦×ª ×¢×ž×•×¡ ×›×¨×’×¢... ×ª× ×¡×” ×©×•×‘ ×‘×¢×•×“ ×›×ž×” ×©× ×™×•×ª!"

# ====================== DB ======================
async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL, username TEXT, full_name TEXT, points INTEGER DEFAULT 0, energy INTEGER DEFAULT 100, tier TEXT DEFAULT 'free', referral_code TEXT, referred_by BIGINT, created_at TIMESTAMP DEFAULT NOW(), last_seen TIMESTAMP DEFAULT NOW(), last_energy_update TIMESTAMP DEFAULT NOW(), is_admin BOOLEAN DEFAULT FALSE);''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT, done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS identities (id SERIAL PRIMARY KEY, user_id BIGINT, full_name TEXT, doc_type TEXT, verified BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name TEXT, phone TEXT, added_by BIGINT, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, customer_id INTEGER, content TEXT, created_by BIGINT, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT, description TEXT, price INTEGER, stock INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS purchases (id SERIAL PRIMARY KEY, user_id BIGINT, product_id INTEGER, points_spent INTEGER, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT, amount INTEGER, type TEXT, created_at TIMESTAMP DEFAULT NOW());''')
        await conn.execute('''ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT, ADD COLUMN IF NOT EXISTS referred_by BIGINT, ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(), ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;''')
    print("All tables & migration OK")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""INSERT INTO users (telegram_id, username, referral_code) VALUES ($1, $2, $3) ON CONFLICT (telegram_id) DO UPDATE SET username = $2, last_seen = NOW()""", uid, username, f"SLH{uid}")

def get_multiplier(tier):
    if not tier: return 1.0
    return 2.0 if tier == "business" else 1.5 if tier == "pro" else 1.0

# ====================== Keyboards ======================
def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="ðŸ“Š ×¡×˜×˜×•×¡", callback_data="status"), types.InlineKeyboardButton(text="â­ × ×§×•×“×•×ª", callback_data="points")],
        [types.InlineKeyboardButton(text="âœ… ×¦'×§-××™×Ÿ", callback_data="checkin"), types.InlineKeyboardButton(text="âš¡ ×”×§×© Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="ðŸ’Ž ×©×“×¨×•×’", callback_data="upgrade"), types.InlineKeyboardButton(text="ðŸ¤ ×ª×¨×•×ž×”", callback_data="donate")],
        [types.InlineKeyboardButton(text="ðŸ’° ×§×¨×™×¤×˜×•", callback_data="crypto"), types.InlineKeyboardButton(text="ðŸ”— ×”×¤× ×™×•×ª", callback_data="referral")],
        [types.InlineKeyboardButton(text="ðŸ“‹ ×ž×©×™×ž×•×ª", callback_data="tasks"), types.InlineKeyboardButton(text="ðŸ‘› ××¨× ×§", callback_data="wallet")],
        [types.InlineKeyboardButton(text="ðŸ”® ××•×¨×§×œ", callback_data="oracle"), types.InlineKeyboardButton(text="â˜®ï¸ ×©×œ×•×", callback_data="peace")],
        [types.InlineKeyboardButton(text="ðŸ“Š ×“×©×‘×•×¨×“", callback_data="dashboard"), types.InlineKeyboardButton(text="ðŸ›’ ×—× ×•×ª", callback_data="store")],
        [types.InlineKeyboardButton(text="ðŸ‘‘ × ×™×”×•×œ", callback_data="admin"), types.InlineKeyboardButton(text="ðŸ’Ž ×ž×©×§×™×¢×™×", callback_data="investors")],
        [types.InlineKeyboardButton(text="â“ ×¢×–×¨×”", callback_data="help")]
    ])

def store_menu(products):
    kb = [[types.InlineKeyboardButton(text=f"{p['name']} - {p['price']} × ×§'", callback_data=f"buy_{p['id']}")] for p in products]
    kb.append([types.InlineKeyboardButton(text="ðŸ”™ ×—×–×¨×”", callback_data="main_menu")])
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# ====================== HANDOFF ======================
HANDOFF = """\
# ðŸ¤– SLH SPARK AI â€” AGENT HANDOFF
Version 4.6 | 2026-06-04
Marketplace: /store /add_product /products /buy
Investor System: /invest /microinvest /certificate (coming soon)
"""

# ====================== Commands ======================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("ðŸ§  <b>SLH Spark AI v4.6</b>\n\n×›×œ ×”×ž×¢×¨×›×•×ª ×¤×¢×™×œ×•×ª! ðŸ›’ ×—× ×•×ª + ðŸ’Ž ×ž×©×§×™×¢×™× ×‘×§×¨×•×‘", reply_markup=main_menu())

@dp.message(Command("context"))
async def cmd_context(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×’×™×©×ª ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer(f"<pre>{HANDOFF}</pre>")

# --- Marketplace ---
@dp.message(Command("store"))
async def cmd_store(msg: types.Message):
    async with pool.acquire() as conn:
        products = await conn.fetch("SELECT id, name, price FROM products WHERE stock > 0 ORDER BY id")
        if not products:
            return await msg.answer("ðŸ›’ ×”×—× ×•×ª ×¨×™×§×” ×›×¨×’×¢.")
        await msg.answer("ðŸ›’ <b>×—× ×•×ª SLH</b>\n×‘×—×¨ ×ž×•×¦×¨ ×œ×¨×›×™×©×”:", reply_markup=store_menu(products))

@dp.message(Command("add_product"))
async def cmd_add_product(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×’×™×©×ª ×ž× ×”×œ ×‘×œ×‘×“.")
    parts = msg.text.split(None, 3)
    if len(parts) < 4:
        return await msg.answer("×©×™×ž×•×©: /add_product [×©×] [×ž×—×™×¨] [×ª×™××•×¨]")
    name, price_str, desc = parts[1], parts[2], parts[3]
    try:
        price = int(price_str)
    except ValueError:
        return await msg.answer("×ž×—×™×¨ ×—×™×™×‘ ×œ×”×™×•×ª ×ž×¡×¤×¨.")
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO products (name, description, price, stock) VALUES ($1, $2, $3, 999)", name, desc, price)
        await msg.answer(f"âœ… ×ž×•×¦×¨ '{name}' × ×•×¡×£ ×‘×ž×—×™×¨ {price} × ×§×•×“×•×ª.")

@dp.message(Command("products"))
async def cmd_products(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price, stock FROM products ORDER BY id")
        if not rows:
            return await msg.answer("××™×Ÿ ×ž×•×¦×¨×™×.")
        text = "\n".join(f"{r['id']}: {r['name']} - {r['price']} × ×§' ({r['stock']} ×‘×ž×œ××™)" for r in rows)
        await msg.answer(f"ðŸ“¦ <b>×ž×•×¦×¨×™×</b>:\n{text}")

@dp.message(Command("buy"))
async def cmd_buy(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("×©×™×ž×•×©: /buy [×ž×–×”×” ×ž×•×¦×¨]")
    try:
        product_id = int(parts[1])
    except ValueError:
        return await msg.answer("×ž×–×”×” ×ž×•×¦×¨ ×—×™×™×‘ ×œ×”×™×•×ª ×ž×¡×¤×¨.")
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        product = await conn.fetchrow("SELECT id, name, price, stock FROM products WHERE id = $1", product_id)
        if not product:
            return await msg.answer("×ž×•×¦×¨ ×œ× × ×ž×¦×.")
        if product['stock'] <= 0:
            return await msg.answer("××–×œ ×ž×”×ž×œ××™.")
        user = await conn.fetchrow("SELECT points FROM users WHERE telegram_id = $1", uid)
        if not user or user['points'] < product['price']:
            return await msg.answer("××™×Ÿ ×ž×¡×¤×™×§ × ×§×•×“×•×ª.")
        await conn.execute("UPDATE users SET points = points - $1 WHERE telegram_id = $2", product['price'], uid)
        await conn.execute("UPDATE products SET stock = stock - 1 WHERE id = $1", product_id)
        await conn.execute("INSERT INTO purchases (user_id, product_id, points_spent) VALUES ($1, $2, $3)", uid, product_id, product['price'])
        new_points = user['points'] - product['price']
        await msg.answer(f"ðŸŽ‰ ×¨×›×©×ª {product['name']} ×‘-{product['price']} × ×§×•×“×•×ª!\n×™×ª×¨×”: {new_points}")

# --- Investor Placeholder (to be expanded tomorrow) ---
@dp.message(Command("invest"))
async def cmd_invest(msg: types.Message):
    await msg.answer("ðŸ’Ž <b>×”×©×§×¢×” ×‘-SLH</b>\n×ž×¢×¨×›×ª ×”×ž×©×§×™×¢×™× ×ª×™×¤×ª×— ×‘×§×¨×•×‘!\n×‘×™× ×ª×™×™× ××¤×©×¨ ×œ×”×ª×¢×“×›×Ÿ ×‘-/context")

@dp.message(Command("microinvest"))
async def cmd_microinvest(msg: types.Message):
    await msg.answer("ðŸ’Ž <b>×”×©×§×¢×” ×§×˜× ×”</b>\n×‘×§×¨×•×‘ ×ª×•×›×œ ×œ×ª×ž×•×š ×‘×¤×¨×•×™×§×˜ ×ž-5 ×©\"×— ×•×œ×§×‘×œ ×ª×¢×•×“×ª ×ž×©×§×™×¢.")

@dp.message(Command("certificate"))
async def cmd_certificate(msg: types.Message):
    await msg.answer("ðŸ“œ <b>×ª×¢×•×“×ª ×ž×©×§×™×¢</b>\n××™×Ÿ ×œ×š ×¢×“×™×™×Ÿ ×ª×¢×•×“×”. ×”×©×ª×ž×© ×‘-/invest")

# (×©××¨ ×”×¤×§×•×“×•×ª: status, points, checkin, tap, tasks, done, referral, dashboard, leaderboard, profile, myid, help, admin, users, stats, stubs...)
# [×”×¢×ª×§ ×ž×”×’×¨×¡×” 4.5  ×”×Ÿ ×–×”×•×ª ×œ×—×œ×•×˜×™×Ÿ]

# ====================== AI Fallback ======================
@dp.message()
async def ai_fallback(msg: types.Message):
    if msg.text and msg.text.startswith('/'):
        return
    await bot.send_chat_action(msg.chat.id, 'typing')
    reply = await ask_ai(msg.text)
    await msg.answer(reply)

# ====================== Callbacks ======================
@dp.callback_query()
async def main_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    msg = call.message
    if data.startswith("buy_"):
        product_id = int(data.split("_")[1])
        # simulate /buy by calling the handler logic directly
        uid = call.from_user.id
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT id, name, price, stock FROM products WHERE id = $1", product_id)
            if not product:
                return await msg.answer("×ž×•×¦×¨ ×œ× × ×ž×¦×.")
            if product['stock'] <= 0:
                return await msg.answer("××–×œ ×ž×”×ž×œ××™.")
            user = await conn.fetchrow("SELECT points FROM users WHERE telegram_id = $1", uid)
            if not user or user['points'] < product['price']:
                return await msg.answer("××™×Ÿ ×ž×¡×¤×™×§ × ×§×•×“×•×ª.")
            await conn.execute("UPDATE users SET points = points - $1 WHERE telegram_id = $2", product['price'], uid)
            await conn.execute("UPDATE products SET stock = stock - 1 WHERE id = $1", product_id)
            await conn.execute("INSERT INTO purchases (user_id, product_id, points_spent) VALUES ($1, $2, $3)", uid, product_id, product['price'])
            new_points = user['points'] - product['price']
            await msg.answer(f"ðŸŽ‰ ×¨×›×©×ª {product['name']} ×‘-{product['price']} × ×§×•×“×•×ª!\n×™×ª×¨×”: {new_points}")
        return
    if data == "store":
        await cmd_store(msg)
        return
    if data == "main_menu":
        await msg.answer("ðŸ§  <b>SLH Spark AI v4.6</b>\n\n×ª×¤×¨×™×˜ ×¨××©×™", reply_markup=main_menu())
        return
    if data == "investors":
        await msg.answer("ðŸ’Ž <b>×ž×¢×¨×›×ª ×ž×©×§×™×¢×™×</b>\n×‘×§×¨×•×‘: /invest, /microinvest, /certificate")
        return
    mapping = {
        "status": cmd_status, "points": cmd_points, "checkin": cmd_checkin,
        "tap": cmd_tap, "crypto": cmd_crypto, "donate": cmd_donate,
        "upgrade": cmd_upgrade, "tasks": cmd_tasks, "oracle": cmd_oracle,
        "peace": cmd_peace, "wallet": cmd_wallet, "referral": cmd_referral,
        "dashboard": cmd_dashboard, "admin": cmd_admin, "help": cmd_help
    }
    handler = mapping.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer("âœ¨ Feature coming soon")

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    print("ðŸš€ SLH Spark AI v4.6  Marketplace + Investor Preview")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
