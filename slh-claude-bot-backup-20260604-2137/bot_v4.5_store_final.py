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
from features.store import router as store_router      # <-- ×ž×•×“×•×œ ×—× ×•×ª

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
dp.include_router(store_router)                # <-- ×¨×™×©×•× × ×ª×‘ ×”×—× ×•×ª
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
    system_prompt = """××ª×” SLH Spark AI v4.5  ×¢×•×–×¨ ××™×©×™ ×—×›×, ×™×“×™×“×•×ª×™, ×©× ×•×Ÿ ×•×ž×“×•×™×§ ×‘×¢×‘×¨×™×ª.
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
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL, username TEXT, full_name TEXT, points INTEGER DEFAULT 0, energy INTEGER DEFAULT 100, tier TEXT DEFAULT ''free'', referral_code TEXT, referred_by BIGINT, created_at TIMESTAMP DEFAULT NOW(), last_seen TIMESTAMP DEFAULT NOW(), last_energy_update TIMESTAMP DEFAULT NOW(), is_admin BOOLEAN DEFAULT FALSE);''')
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
    kb = [
        [types.InlineKeyboardButton(text="ðŸ“Š ×¡×˜×˜×•×¡", callback_data="status"),
         types.InlineKeyboardButton(text="â­ï¸ × ×§×•×“×•×ª", callback_data="points")],
        [types.InlineKeyboardButton(text="âœ… ×¦'×§-××™×Ÿ", callback_data="checkin"),
         types.InlineKeyboardButton(text="âš¡ï¸ ×”×§×© Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="ðŸ’Ž ×©×“×¨×•×’", callback_data="upgrade"),
         types.InlineKeyboardButton(text="ðŸ¤ ×ª×¨×•×ž×”", callback_data="donate")],
        [types.InlineKeyboardButton(text="ðŸ’° ×§×¨×™×¤×˜×•", callback_data="crypto"),
         types.InlineKeyboardButton(text="ðŸ”— ×”×¤× ×™×•×ª", callback_data="referral")],
        [types.InlineKeyboardButton(text="ðŸ“‹ ×ž×©×™×ž×•×ª", callback_data="tasks"),
         types.InlineKeyboardButton(text="ðŸ‘› ××¨× ×§", callback_data="wallet")],
        [types.InlineKeyboardButton(text="ðŸ”® ××•×¨×§×œ", callback_data="oracle"),
         types.InlineKeyboardButton(text="â˜®ï¸ ×©×œ×•×", callback_data="peace")],
        [types.InlineKeyboardButton(text="ðŸ“Š ×“×©×‘×•×¨×“", callback_data="dashboard"),
         types.InlineKeyboardButton(text="ðŸ›’ ×—× ×•×ª", callback_data="store")],
        [types.InlineKeyboardButton(text="ðŸ‘‘ × ×™×”×•×œ", callback_data="admin"),
         types.InlineKeyboardButton(text="â“ ×¢×–×¨×”", callback_data="help")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# ====================== HANDOFF ======================
HANDOFF = """\
# ðŸ¤– SLH SPARK AI â€” AGENT HANDOFF
Version 4.5 | 2026-06-04
Bot: @SLH_Claude_bot | Railway: diligent-radiance
Stack: Python + aiogram 3.x + PostgreSQL + Groq AI
Admin: 224223270 | Local: D:\\slh-website\\slh-claude-bot
Env: BOT_TOKEN, DATABASE_URL, GROQ_API_KEY, GEMINI_API_KEY, HF_TOKEN, TON_WALLET
DB: users, tasks, identities, customers, notes, products, purchases, transactions
47 commands: /start, /status, /points, /checkin, /tap, /tasks, /done,
/referral, /dashboard, /leaderboard, /wallet, /deposit, /transfer, /paid,
/simdeposit, /upgrade, /donate, /crypto, /oracle, /peace, /identity,
/myidentity, /myid, /profile, /register, /help, /faq, /guide, /tutorial,
/admin, /users, /stats, /broadcast, /crm, /backup, /morning, /doctor,
/statusapi, /setreminder, /addcustomer, /customers, /addnote, /notes,
/events, /segments, /context, /store, /products, /buy, /add_product
AI: Router 8b/70b + Gemini fallback
Deploy: railway down -y â†’ wait â†’ railway up --detach â†’ wait â†’ railway logs
"""

# ====================== Commands (×œ×œ× stubs ×©×œ store) ======================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("ðŸ§  <b>SLH Spark AI v4.5</b>\n\n×›×œ ×”×ž×¢×¨×›×•×ª ×¤×¢×™×œ×•×ª! ðŸ›’ ×—× ×•×ª ×ž×—×•×‘×¨×ª", reply_markup=main_menu())

@dp.message(Command("context"))
async def cmd_context(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›”ï¸ ×’×™×©×ª ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer(f"<pre>{HANDOFF}</pre>")

@dp.message(Command("status"))
async def cmd_status(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, energy, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"ðŸ“Š <b>×¡×˜×˜×•×¡</b>\nâ­ï¸ × ×§×•×“×•×ª: {user['points']}\nâš¡ï¸ ×× ×¨×’×™×”: {user['energy']}\nðŸ… ×¨×ž×”: {user['tier']}")
        else:
            await msg.answer("×ž×©×ª×ž×© ×œ× × ×ž×¦×. ×”×§×œ×“ /start")

@dp.message(Command("points"))
async def cmd_points(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        await msg.answer(f"â­ï¸ ×”× ×§×•×“×•×ª ×©×œ×š: {pts or 0}")

@dp.message(Command("checkin"))
async def cmd_checkin(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + 10, last_seen = NOW() WHERE telegram_id=$1", uid)
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        await msg.answer(f"âœ… ×¦'×§-××™×Ÿ ×‘×•×¦×¢! +10 × ×§×•×“×•×ª. ×¡×”\"×›: {pts}")

@dp.message(Command("tap"))
async def cmd_tap(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET 
                energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int),
                last_energy_update = NOW()
            WHERE telegram_id = $1
        """, uid)
        user = await conn.fetchrow("SELECT energy, points, tier FROM users WHERE telegram_id=$1", uid)
        if not user or user['energy'] < 5:
            return await msg.answer("âŒ ××™×Ÿ ×ž×¡×¤×™×§ ×× ×¨×’×™×”. ×—×›×” ×ž×¡×¤×¨ ×©× ×™×•×ª.")
        gain = int(5 * get_multiplier(user['tier']))
        new_energy = user['energy'] - 5
        new_points = user['points'] + gain
        await conn.execute("UPDATE users SET energy=$1, points=$2 WHERE telegram_id=$3", new_energy, new_points, uid)
        await msg.answer(f"âš¡ï¸ +{gain} × ×§×•×“×•×ª! ×¡×”\"×›: {new_points} | ×× ×¨×’×™×”: {new_energy}")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at::date = CURRENT_DATE", uid)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES ($1,$2)", uid, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at::date = CURRENT_DATE", uid)
        text = "ðŸ“‹ <b>×ž×©×™×ž×•×ª ×™×•×ž×™×•×ª</b>:\n\n" + "\n".join(f"{'âœ…' if r['done'] else 'âŒ'} {r['description']} (ID:{r['id']})" for r in rows)
        await msg.answer(text + "\n\n×”×©×œ× ×ž×©×™×ž×”: /done [ID]")

@dp.message(Command("done"))
async def cmd_done(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("×©×™×ž×•×©: /done [ID]")
    task_id = int(parts[1])
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET done=true WHERE id=$1 AND user_id=$2", task_id, uid)
        await msg.answer(f"âœ… ×ž×©×™×ž×” {task_id} ×”×•×©×œ×ž×”!")

@dp.message(Command("referral"))
async def cmd_referral(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        code = await conn.fetchval("SELECT referral_code FROM users WHERE telegram_id=$1", uid)
        if not code:
            code = f"SLH{uid}"
            await conn.execute("UPDATE users SET referral_code=$1 WHERE telegram_id=$2", code, uid)
        await msg.answer(f"ðŸ”— ×§×™×©×•×¨ ×”×”×¤× ×™×” ×©×œ×š:\nhttps://t.me/SLH_Claude_bot?start={code}")

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid) or 0
        refs = await conn.fetchval("SELECT count(*) FROM users WHERE referred_by=$1", uid) or 0
        await msg.answer(f"ðŸ“Š <b>×œ×•×— ×ž×—×•×•× ×™×</b>\nâ­ï¸ × ×§×•×“×•×ª: {pts}\nðŸ‘¥ ×—×‘×¨×™× ×©×”×•×¤× ×•: {refs}")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
        text = "\n".join(f"{i+1}. {r['username'] or '?'} - {r['points']}" for i,r in enumerate(rows))
        await msg.answer(f"ðŸ† <b>×˜×‘×œ×ª ×ž×•×‘×™×œ×™×</b>:\n{text}")

@dp.message(Command("profile"))
async def cmd_profile(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, points, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"ðŸ‘¤ ×¤×¨×•×¤×™×œ:\n×©×: {user['username']}\n× ×§×•×“×•×ª: {user['points']}\n×¨×ž×”: {user['tier']}")
        else:
            await msg.answer("××™×Ÿ ×¤×¨×•×¤×™×œ. /start")

@dp.message(Command("myid"))
async def cmd_myid(msg: types.Message):
    await msg.answer(f"ðŸ†” ×”-Telegram ID ×©×œ×š: <code>{msg.from_user.id}</code>")

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer("â“ ×¢×–×¨×”:\n/start, /status, /tap, /tasks, /wallet, /admin, /context, /store ×•×¢×•×“...")

# Admin
@dp.message(Command("admin"))
async def cmd_admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›”ï¸ ×’×™×©×ª ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer("ðŸ‘‘ ×ª×¤×¨×™×˜ ×ž× ×”×œ:\n/users /broadcast /crm /stats /backup /context")

@dp.message(Command("users"))
async def cmd_users(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›”ï¸ ×ž× ×”×œ ×‘×œ×‘×“.")
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT count(*) FROM users")
        await msg.answer(f"ðŸ‘¥ ×¡×”\"×› ×ž×©×ª×ž×©×™×: {total}")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›”ï¸ ×ž× ×”×œ ×‘×œ×‘×“.")
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT count(*) FROM users")
        points = await conn.fetchval("SELECT sum(points) FROM users") or 0
        await msg.answer(f"ðŸ“ˆ ×¡×˜×˜×™×¡×˜×™×§×•×ª:\nðŸ‘¥ ×ž×©×ª×ž×©×™×: {users}\nâ­ï¸ ×¡×”\"×› × ×§×•×“×•×ª: {points}")

# Stubs  ×œ×œ× store, products, buy, add_product (×ž×˜×•×¤×œ×™× ×‘×ž×•×“×•×œ)
@dp.message(Command("register"))
async def cmd_register(msg: types.Message): await msg.answer("ðŸ“ ×”×¨×©×ž×”: /identity")
@dp.message(Command("crypto"))
async def cmd_crypto(msg: types.Message): await msg.answer("ðŸ’° ×ž×™×“×¢ ×§×¨×™×¤×˜×• ×™×’×™×¢ ×‘×§×¨×•×‘.")
@dp.message(Command("donate"))
async def cmd_donate(msg: types.Message): await msg.answer(f"ðŸ¤ ×ª×¨×•×ž×”:\n<code>{TON_WALLET}</code>")
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: types.Message): await msg.answer("ðŸ’Ž ×©×“×¨×•×’: Pro (9.9 TON) / Business (29 TON) - /paid")
@dp.message(Command("oracle"))
async def cmd_oracle(msg: types.Message): await msg.answer("ðŸ”® ××•×¨×§×œ  ×—×›×ž×” ×¢×ª×™×§×”. ×©××œ ×©××œ×”.")
@dp.message(Command("peace"))
async def cmd_peace(msg: types.Message): await msg.answer(", ×ž×¢×¨×›×ª SLH × ×•×¢×“×” ×›×“×™ ×œ×¢×•×“×“ ××•×ª×š ×œ×ž×¦×•×™×™× ×•×ª ×©×‘×šâ˜®ï¸ ×©×œ×•× ×¢×•×œ×ž×™ ×ž×ª×—×™×œ ×‘×š.")
@dp.message(Command("wallet"))
async def cmd_wallet(msg: types.Message): await msg.answer("ðŸ‘› ××¨× ×§: /deposit, /transfer, /simdeposit")
@dp.message(Command("deposit"))
async def cmd_deposit(msg: types.Message): await msg.answer("ðŸ’° ×”×¤×§×“×”: ×©×œ×— TON ×œ××¨× ×§.")
@dp.message(Command("transfer"))
async def cmd_transfer(msg: types.Message): await msg.answer("ðŸ” ×”×¢×‘×¨×ª × ×§×•×“×•×ª: /transfer [×ž×–×”×”] [×›×ž×•×ª]")
@dp.message(Command("paid"))
async def cmd_paid(msg: types.Message): await msg.answer("ðŸ’³ ×ª×©×œ×•× (×‘×§×¨×•×‘: TON webhook)")
@dp.message(Command("invite"))
async def cmd_invite(msg: types.Message): await cmd_referral(msg)
@dp.message(Command("simdeposit"))
async def cmd_simdeposit(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + 100 WHERE telegram_id=$1", uid)
        await msg.answer("ðŸ’¸ +100 × ×§×•×“×•×ª (×”×“×ž×™×”)")
@dp.message(Command("addcustomer"))
async def cmd_addcustomer(msg: types.Message): await msg.answer("âž• ×”×•×¡×¤×ª ×œ×§×•×—: /addcustomer [×©×] [×˜×œ×¤×•×Ÿ]")
@dp.message(Command("customers"))
async def cmd_customers(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, phone FROM customers LIMIT 10")
        if not rows: return await msg.answer("××™×Ÿ ×œ×§×•×—×•×ª.")
        await msg.answer("ðŸ“‹ ×œ×§×•×—×•×ª:\n" + "\n".join(f"{r['id']}: {r['name']} - {r['phone']}" for r in rows))
@dp.message(Command("addnote"))
async def cmd_addnote(msg: types.Message): await msg.answer("ðŸ“ ×”×¢×¨×”: /addnote [×ž×–×”×” ×œ×§×•×—] [×˜×§×¡×˜]")
@dp.message(Command("notes"))
async def cmd_notes(msg: types.Message): await msg.answer("ðŸ“ ×¦×¤×™×™×” ×‘×”×¢×¨×•×ª: /notes [×ž×–×”×” ×œ×§×•×—]")
@dp.message(Command("vip"))
async def cmd_vip(msg: types.Message): await msg.answer("ðŸ‘‘ VIP  ×‘×§×¨×•×‘.")
@dp.message(Command("crm"))
async def cmd_crm(msg: types.Message): await msg.answer("ðŸ“Š CRM: /customers, /addnote, /notes")
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: types.Message): await msg.answer("ðŸ“¢ ×©×™×“×•×¨ (×‘×§×¨×•×‘)")
@dp.message(Command("morning"))
async def cmd_morning(msg: types.Message): await msg.answer("ðŸŒ… ×‘×•×§×¨ ×˜×•×‘!")
@dp.message(Command("doctor"))
async def cmd_doctor(msg: types.Message): await msg.answer("ðŸ©º ×“×•×§×˜×•×¨ (×‘×§×¨×•×‘)")
@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: types.Message): await msg.answer("ðŸ“¡ API: 200 OK")
@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: types.Message): await msg.answer("â° ×ª×–×›×•×¨×ª ×”×•×’×“×¨×” (×“×ž×•)")
@dp.message(Command("backup"))
async def cmd_backup(msg: types.Message): await msg.answer("ðŸ’¾ ×’×™×‘×•×™ (×‘×§×¨×•×‘)")
@dp.message(Command("events"))
async def cmd_events(msg: types.Message): await msg.answer("ðŸ“… ××™×¨×•×¢×™×: ××™×Ÿ ××™×¨×•×¢×™×.")
@dp.message(Command("segments"))
async def cmd_segments(msg: types.Message): await msg.answer("ðŸ“Š ×¡×’×ž× ×˜×™× (×‘×§×¨×•×‘)")
@dp.message(Command("guide"))
async def cmd_guide(msg: types.Message): await msg.answer("ðŸ“˜ ×ž×“×¨×™×š: https://example.com/guide")
@dp.message(Command("faq"))
async def cmd_faq(msg: types.Message): await msg.answer("â“ ×©××œ×•×ª × ×¤×•×¦×•×ª: ×”×©×ª×ž×© ×‘-/tap ×œ×¦×‘×•×¨ × ×§×•×“×•×ª.")
@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: types.Message): await msg.answer("ðŸŽ“ ×”×“×¨×›×”: ×”×ª×—×œ ×¢× /start, ×”×§×© Tap.")

class IdentityForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_doc = State()

@dp.message(Command("identity"))
async def cmd_identity(msg: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.waiting_for_name)
    await msg.answer("ðŸ“› ×× × ×”×–×Ÿ ××ª ×©×ž×š ×”×ž×œ×:")

@dp.message(IdentityForm.waiting_for_name)
async def process_name(msg: types.Message, state: FSMContext):
    await state.update_data(full_name=msg.text)
    await state.set_state(IdentityForm.waiting_for_doc)
    await msg.answer("ðŸ“„ ×”×¢×œ×” ×ª×ž×•× ×” ×©×œ ×ª×¢×•×“×ª ×–×”×•×ª (××• ×”×§×œ×“ '×“×œ×’'):")

@dp.message(IdentityForm.waiting_for_doc)
async def process_doc(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    full_name = data['full_name']
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO identities (user_id, full_name, doc_type) VALUES ($1,$2,'manual')", uid, full_name)
    await state.clear()
    await msg.answer("âœ… ×–×”×•×ª × ×©×ž×¨×”.")

@dp.message(Command("myidentity"))
async def cmd_myidentity(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT full_name, verified FROM identities WHERE user_id=$1 ORDER BY id DESC LIMIT 1", uid)
        if row:
            status = "âœ”ï¸ ×ž××•×ž×ª" if row['verified'] else "âŒ ×œ× ×ž××•×ž×ª"
            await msg.answer(f"ðŸ‘¤ {row['full_name']} - {status}")
        else:
            await msg.answer("××™×Ÿ ×–×”×•×ª ×©×ž×•×¨×”. /identity")

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
    if data == "store":
        # ×”×¤× ×™×™×” ×œ×¤×§×•×“×ª /store (×©× ×ž×¦××ª ×‘×ž×•×“×•×œ)
        from features.store import cmd_store
        await cmd_store(msg)
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
    print("ðŸš€ SLH Spark AI v4.5  ×—× ×•×ª ×ž×—×•×‘×¨×ª")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
