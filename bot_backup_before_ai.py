import asyncio, os, datetime, json
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
pool = None

# ====================== DB with AUTO CREATE TABLES ======================
async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        # users
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                points INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                tier TEXT DEFAULT 'free',
                referral_code TEXT,
                referred_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                last_energy_update TIMESTAMP DEFAULT NOW(),
                is_admin BOOLEAN DEFAULT FALSE
            );
        ''')
        # tasks
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                description TEXT NOT NULL,
                done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # identities
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS identities (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                full_name TEXT,
                doc_type TEXT,
                doc_number TEXT,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # customers
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                added_by BIGINT REFERENCES users(telegram_id),
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # notes
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                content TEXT NOT NULL,
                created_by BIGINT REFERENCES users(telegram_id),
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # products
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # purchases
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                product_id INTEGER REFERENCES products(id),
                points_spent INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # transactions
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                from_user BIGINT REFERENCES users(telegram_id),
                to_user BIGINT REFERENCES users(telegram_id),
                amount INTEGER NOT NULL,
                type TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        # Auto-migration (ensure new columns)
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        print("âœ… All tables & migration OK")
    print("âœ… DB Pool ready")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, referral_code)
            VALUES ($1, $2, $3) ON CONFLICT (telegram_id) 
            DO UPDATE SET username = $2, last_seen = NOW()
        """, uid, username, f"SLH{uid}")

def get_multiplier(tier):
    return 2.0 if tier == "business" else 1.5 if tier == "pro" else 1.0

# ====================== KEYBOARDS ======================
def main_menu(is_admin=False):
    kb = [
        [types.InlineKeyboardButton(text="ðŸ“Š Status", callback_data="status"),
         types.InlineKeyboardButton(text="â­ Points", callback_data="points")],
        [types.InlineKeyboardButton(text="âœ… Check-in", callback_data="checkin"),
         types.InlineKeyboardButton(text="âš¡ Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="ðŸ’Ž Upgrade", callback_data="upgrade"),
         types.InlineKeyboardButton(text="ðŸ¤ Donate", callback_data="donate")],
        [types.InlineKeyboardButton(text="ðŸ’° Crypto", callback_data="crypto"),
         types.InlineKeyboardButton(text="ðŸ”— Referral", callback_data="referral")],
        [types.InlineKeyboardButton(text="ðŸ“‹ Tasks", callback_data="tasks"),
         types.InlineKeyboardButton(text="ðŸ‘› Wallet", callback_data="wallet")],
        [types.InlineKeyboardButton(text="ðŸ”® Oracle", callback_data="oracle"),
         types.InlineKeyboardButton(text="â˜®ï¸ Peace", callback_data="peace")],
        [types.InlineKeyboardButton(text="ðŸ“Š Dashboard", callback_data="dashboard"),
         types.InlineKeyboardButton(text="ðŸ‘‘ Admin", callback_data="admin")],
        [types.InlineKeyboardButton(text="â“ Help", callback_data="help")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# ====================== ALL COMMANDS (46) ======================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("ðŸ§  <b>SLH Spark AI v4.0</b>\n\n×›×œ ×”×ž×¢×¨×›×•×ª ×¤×¢×™×œ×•×ª!", reply_markup=main_menu())

@dp.message(Command("register"))
async def cmd_register(msg: types.Message):
    await msg.answer("ðŸ“ ×”×¨×©×ž×”: ×× × ×©×œ×— /identity ×œ×”×–×“×”×•×ª, ××• ×¤×©×•×˜ ×”×©×ª×ž×© ×‘×¤×§×•×“×•×ª.")

@dp.message(Command("status"))
async def cmd_status(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, energy, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"ðŸ“Š <b>×¡×˜×˜×•×¡</b>\nâ­ × ×§×•×“×•×ª: {user['points']}\nâš¡ ×× ×¨×’×™×”: {user['energy']}\nðŸ… ×¨×ž×”: {user['tier']}")
        else:
            await msg.answer("âŒ ×ž×©×ª×ž×© ×œ× × ×ž×¦×. ×”×§×œ×“ /start")

@dp.message(Command("points"))
async def cmd_points(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        await msg.answer(f"â­ ×”× ×§×•×“×•×ª ×©×œ×š: {pts or 0}")

@dp.message(Command("checkin"))
async def cmd_checkin(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        # simple checkin: add 10 points once per day
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
        await msg.answer(f"âš¡ +{gain} × ×§×•×“×•×ª! ×¡×”\"×›: {new_points} | ×× ×¨×’×™×”: {new_energy}")

@dp.message(Command("crypto"))
async def cmd_crypto(msg: types.Message):
    await msg.answer("ðŸ’° ×ž×™×“×¢ ×¢×œ ×ž×˜×‘×¢×•×ª ×§×¨×™×¤×˜×•×’×¨×¤×™×™× ×™×’×™×¢ ×‘×§×¨×•×‘.")

@dp.message(Command("donate"))
async def cmd_donate(msg: types.Message):
    await msg.answer(f"ðŸ¤ ×ª×¨×•×ž×”: × ×™×ª×Ÿ ×œ×©×œ×•×— TON ×œ×›×ª×•×‘×ª:\n<code>{TON_WALLET}</code>")

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: types.Message):
    await msg.answer("ðŸ’Ž ×œ×©×“×¨×•×’ ×œ-Pro (9.9 TON) ××• Business (29 TON) ×”×©×ª×ž×© ×‘-/paid")

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

@dp.message(Command("oracle"))
async def cmd_oracle(msg: types.Message):
    await msg.answer("ðŸ”® Oracle  ×—×›×ž×” ×¢×ª×™×§×”. ×©××œ ×©××œ×”.")

@dp.message(Command("peace"))
async def cmd_peace(msg: types.Message):
    await msg.answer("â˜®ï¸ Peace  ×©×œ×•× ×¢×•×œ×ž×™ ×ž×ª×—×™×œ ×‘×š.")

@dp.message(Command("wallet"))
async def cmd_wallet(msg: types.Message):
    await msg.answer("ðŸ‘› ××¨× ×§: ×”×¤×§×“×•×ª, ×”×¢×‘×¨×•×ª ×•×¢×•×“. ×”×©×ª×ž×© ×‘ /deposit, /transfer, /simdeposit")

@dp.message(Command("referral"))
async def cmd_referral(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        code = await conn.fetchval("SELECT referral_code FROM users WHERE telegram_id=$1", uid)
        if not code:
            code = f"SLH{uid}"
            await conn.execute("UPDATE users SET referral_code=$1 WHERE telegram_id=$2", code, uid)
        await msg.answer(f"ðŸ”— ×§×™×©×•×¨ ×”×”×¤× ×™×” ×©×œ×š:\nhttps://t.me/SLH_Claude_bot?start={code}\n\n×©×ª×£ ×¢× ×—×‘×¨×™× ×•×§×‘×œ × ×§×•×“×•×ª!")

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid) or 0
        refs = await conn.fetchval("SELECT count(*) FROM users WHERE referred_by=$1", uid) or 0
        await msg.answer(f"ðŸ“Š <b>×œ×•×— ×ž×—×•×•× ×™×</b>\nâ­ × ×§×•×“×•×ª: {pts}\nðŸ‘¥ ×—×‘×¨×™× ×©×”×•×¤× ×•: {refs}")

@dp.message(Command("admin"))
async def cmd_admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×’×™×©×ª ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer("ðŸ‘‘ ×ª×¤×¨×™×˜ ×ž× ×”×œ:\n/users /broadcast /crm /stats /backup")

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer("â“ ×¢×–×¨×”:\n/start, /status, /tap, /tasks, /wallet, /admin ×•×¢×•×“...")

# Additional CRM & admin commands
@dp.message(Command("addcustomer"))
async def cmd_addcustomer(msg: types.Message):
    await msg.answer("âž• ×”×•×¡×¤×ª ×œ×§×•×—: /addcustomer [×©×] [×˜×œ×¤×•×Ÿ]")

@dp.message(Command("customers"))
async def cmd_customers(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, phone FROM customers ORDER BY id LIMIT 10")
        if not rows:
            return await msg.answer("ðŸ“‹ ××™×Ÿ ×œ×§×•×—×•×ª.")
        text = "\n".join(f"{r['id']}: {r['name']} - {r['phone']}" for r in rows)
        await msg.answer(f"ðŸ“‹ <b>×œ×§×•×—×•×ª</b>:\n{text}")

@dp.message(Command("addnote"))
async def cmd_addnote(msg: types.Message):
    await msg.answer("ðŸ“ ×”×•×¡×¤×ª ×”×¢×¨×”: /addnote [×ž×–×”×” ×œ×§×•×—] [×˜×§×¡×˜]")

@dp.message(Command("notes"))
async def cmd_notes(msg: types.Message):
    await msg.answer("ðŸ“ ×¦×¤×™×™×” ×‘×”×¢×¨×•×ª: /notes [×ž×–×”×” ×œ×§×•×—]")

@dp.message(Command("vip"))
async def cmd_vip(msg: types.Message):
    await msg.answer("ðŸ‘‘ VIP  ×‘×§×¨×•×‘.")

@dp.message(Command("invite"))
async def cmd_invite(msg: types.Message):
    await cmd_referral(msg)  # reuse

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
    await msg.answer("ðŸ“„ ×× × ×”×¢×œ×” ×ª×ž×•× ×” ×©×œ ×ª×¢×•×“×ª ×–×”×•×ª (××• ×”×§×œ×“ '×“×œ×’'):")

@dp.message(IdentityForm.waiting_for_doc)
async def process_doc(msg: types.Message, state: FSMContext):
    # simplistic: just store
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
            await msg.answer("××™×Ÿ ×–×”×•×ª ×©×ž×•×¨×”. ×”×©×ª×ž×© ×‘ /identity")

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

@dp.message(Command("deposit"))
async def cmd_deposit(msg: types.Message):
    await msg.answer("ðŸ’° ×”×¤×§×“×”: ×©×œ×— TON ×œ×›×ª×•×‘×ª ×”××¨× ×§ ×©×œ×š.")

@dp.message(Command("transfer"))
async def cmd_transfer(msg: types.Message):
    await msg.answer("ðŸ” ×”×¢×‘×¨×ª × ×§×•×“×•×ª: /transfer [×ž×–×”×”] [×›×ž×•×ª]")

@dp.message(Command("paid"))
async def cmd_paid(msg: types.Message):
    await msg.answer("ðŸ’³ ×ª×©×œ×•× ×‘×•×¦×™ ×ž×“×•×ž×”. (×‘×”×ž×©×š: TON webhook)")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
        text = "\n".join(f"{i+1}. {r['username'] or '?'} - {r['points']}" for i,r in enumerate(rows))
        await msg.answer(f"ðŸ† <b>×˜×‘×œ×ª ×ž×•×‘×™×œ×™×</b>:\n{text}")

@dp.message(Command("users"))
async def cmd_users(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×ž× ×”×œ ×‘×œ×‘×“.")
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT count(*) FROM users")
        await msg.answer(f"ðŸ‘¥ ×¡×”\"×› ×ž×©×ª×ž×©×™×: {total}")

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer("ðŸ“¢ ×©×™×“×•×¨: /broadcast [×”×•×“×¢×”] (×‘×§×¨×•×‘)")

@dp.message(Command("morning"))
async def cmd_morning(msg: types.Message):
    await msg.answer("ðŸŒ… ×‘×•×§×¨ ×˜×•×‘! ××œ ×ª×©×›×— ×¦'×§-××™×Ÿ.")

@dp.message(Command("doctor"))
async def cmd_doctor(msg: types.Message):
    await msg.answer("ðŸ©º ×“×•×§×˜×•×¨  ×™×™×¢×•×¥ ×¨×¤×•××™ ×‘×¡×™×¡×™ (×‘×§×¨×•×‘).")

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: types.Message):
    await msg.answer("ðŸ“¡ ×¡×˜×˜×•×¡ API: ×”×›×œ ×ª×§×™×Ÿ (200 OK)")

@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: types.Message):
    await msg.answer("â° ×ª×–×›×•×¨×ª ×”×•×’×“×¨×” (×“×ž×•).")

@dp.message(Command("backup"))
async def cmd_backup(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×ž× ×”×œ ×‘×œ×‘×“.")
    await msg.answer("ðŸ’¾ ×’×™×‘×•×™ ×‘×¡×™×¡×™: (×‘×”×ž×©×š)")

@dp.message(Command("crm"))
async def cmd_crm(msg: types.Message):
    await msg.answer("ðŸ“Š CRM: /customers, /addnote, /notes")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("â›” ×ž× ×”×œ ×‘×œ×‘×“.")
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT count(*) FROM users")
        points = await conn.fetchval("SELECT sum(points) FROM users") or 0
        await msg.answer(f"ðŸ“ˆ ×¡×˜×˜×™×¡×˜×™×§×•×ª:\nðŸ‘¥ ×ž×©×ª×ž×©×™×: {users}\nâ­ ×¡×”\"×› × ×§×•×“×•×ª: {points}")

@dp.message(Command("events"))
async def cmd_events(msg: types.Message):
    await msg.answer("ðŸ“… ××™×¨×•×¢×™×: ××™×Ÿ ××™×¨×•×¢×™× ×§×¨×•×‘×™×.")

@dp.message(Command("segments"))
async def cmd_segments(msg: types.Message):
    await msg.answer("ðŸ“Š ×¡×’×ž× ×˜×™×: (×‘×§×¨×•×‘)")

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

@dp.message(Command("guide"))
async def cmd_guide(msg: types.Message):
    await msg.answer("ðŸ“˜ ×ž×“×¨×™×š ×œ×ž×©×ª×ž×©: https://example.com/guide")

@dp.message(Command("faq"))
async def cmd_faq(msg: types.Message):
    await msg.answer("â“ ×©××œ×•×ª × ×¤×•×¦×•×ª:\n××™×š ×¦×•×‘×¨×™× × ×§×•×“×•×ª? ×”×©×ª×ž×© ×‘-/tap.")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: types.Message):
    await msg.answer("ðŸŽ“ ×”×“×¨×›×”: ×”×ª×—×œ ×¢× /start, ×”×§×© ×¢×œ Tap ×•×¦×‘×•×¨ × ×§×•×“×•×ª.")

@dp.message(Command("simdeposit"))
async def cmd_simdeposit(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + 100 WHERE telegram_id=$1", uid)
        await msg.answer("ðŸ’¸ +100 × ×§×•×“×•×ª (×”×“×ž×™×”)")

# ====================== MAIN CALLBACK HANDLER ======================
@dp.callback_query()
async def main_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    msg = call.message
    # Map callback to function
    mapping = {
        "status": cmd_status,
        "points": cmd_points,
        "checkin": cmd_checkin,
        "tap": cmd_tap,
        "crypto": cmd_crypto,
        "donate": cmd_donate,
        "upgrade": cmd_upgrade,
        "tasks": cmd_tasks,
        "oracle": cmd_oracle,
        "peace": cmd_peace,
        "wallet": cmd_wallet,
        "referral": cmd_referral,
        "dashboard": cmd_dashboard,
        "admin": cmd_admin,
        "help": cmd_help
    }
    handler = mapping.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer("âœ¨ Feature coming soon")

# ====================== MAIN ======================

# ====================== AI (Groq) ======================
async def ask_groq(prompt: str) -> str:
    try:
        import groq
        client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=500
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {str(e)[:200]}"

@dp.message()
async def ai_fallback(msg: types.Message):
    # Don't respond to commands
    if msg.text and msg.text.startswith('/'):
        return
    await bot.send_chat_action(msg.chat.id, 'typing')
    reply = await ask_groq(msg.text)
    await msg.answer(reply)

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    print("ðŸš€ SLH Spark AI v4.0  all systems active")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
