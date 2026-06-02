import asyncio, logging, os, json, datetime, random
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
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
        await conn.execute("""CREATE TABLE IF NOT EXISTS payments (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, plan TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, user_id BIGINT, name TEXT, description TEXT, price NUMERIC, created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id BIGINT, message TEXT, created_at TIMESTAMP DEFAULT NOW())""")
        
        # ALTER TABLE for existing databases
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW()")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW()")
        await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS user_id BIGINT")
        await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS name TEXT")
        await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT")
        await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS price NUMERIC")
    print("DB ready")

async def ensure_user(uid, username):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (telegram_id, username, referral_code) VALUES ($1, $2, $3) ON CONFLICT (telegram_id) DO UPDATE SET username = $2, last_seen = NOW()", uid, username, f"SLH{uid}")

async def update_energy(uid):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int), last_energy_update = NOW() WHERE telegram_id = $1", uid)

def get_multiplier(tier):
    return 2.0 if tier == "business" else 1.5 if tier == "pro" else 1.0

# ------------------------------ MAIN MENU ------------------------------
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Status", callback_data="status"), types.InlineKeyboardButton(text="⭐ Points", callback_data="points"))
    builder.row(types.InlineKeyboardButton(text="✅ Check-in", callback_data="checkin"), types.InlineKeyboardButton(text="⚡ Tap", callback_data="tap"))
    builder.row(types.InlineKeyboardButton(text="💰 Crypto", callback_data="crypto"), types.InlineKeyboardButton(text="🤝 Donate", callback_data="donate"))
    builder.row(types.InlineKeyboardButton(text="💎 Upgrade", callback_data="upgrade"), types.InlineKeyboardButton(text="📋 Tasks", callback_data="tasks"))
    builder.row(types.InlineKeyboardButton(text="🔮 Oracle", callback_data="oracle"), types.InlineKeyboardButton(text="☮️ Peace", callback_data="peace"))
    builder.row(types.InlineKeyboardButton(text="👛 Wallet", callback_data="wallet"), types.InlineKeyboardButton(text="🔗 Referral", callback_data="referral"))
    builder.row(types.InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"), types.InlineKeyboardButton(text="👑 Admin", callback_data="admin"))
    builder.row(types.InlineKeyboardButton(text="❓ Help", callback_data="help"))
    return builder.as_markup()

# ------------------------------ START ------------------------------
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    # referral
    parts = msg.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            ref_uid = int(parts[1][4:])
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT referred_by FROM users WHERE telegram_id=$1", uid)
                if row and row['referred_by'] is None and ref_uid != uid:
                    await conn.execute("UPDATE users SET referred_by=$1 WHERE telegram_id=$2", ref_uid, uid)
                    await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id=$1", ref_uid)
                    await bot.send_message(ref_uid, "New user via your referral! +50 points")
        except: pass
    logo = (
        "╔════════════════════════════╗\n"
        "║           ✨  SLH SPARK AI v3.3  ✨              ║\n"
        "║     ███████╗██╗              ██╗     ██╗    ║\n"
        "║     ██╔════╝██║              ██║     ██║    ║\n"
        "║     ███████╗██║              ███████║    ║\n"
        "║     ╚════██║██║              ██╔══██║    ║\n"
        "║     ███████║███████╗ ██║      ██║   ║\n"
        "║     ╚══════╝╚══════╝ ╚═╝      ╚═╝   ║\n"
        "║         INTELLIGENT PROJECT ENGINE       ║\n"
        "╚════════════════════════════╝"
    )
    await msg.answer(f"<pre>{logo}</pre>", parse_mode=ParseMode.HTML)
    await msg.answer("SLH Spark AI v3.3 - Welcome!", reply_markup=main_menu())

@dp.message(Command("register"))
async def cmd_register(msg: types.Message):
    await ensure_user(msg.from_user.id, msg.from_user.username or "unknown")
    await msg.answer("Registered! Use /identity to set your profile.")

# ------------------------------ CALLBACK FUNCTIONS (ALL REQUIRED) ------------------------------
async def cmd_status(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    await update_energy(uid)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT points, energy, tier, streak, balance FROM users WHERE telegram_id=$1", uid)
        if not row: return await msg.answer("Register with /register")
        await msg.answer(f"📊 Status\n⭐ Points: {row['points']}\n🔋 Energy: {row['energy']}/100\n🏆 Tier: {row['tier'].upper()}\n🔥 Streak: {row['streak']} days\n💎 Balance: {row['balance']:.2f} TON")

async def cmd_points(msg: types.Message):
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
    await msg.answer(f"⭐ Your points: {pts}")

async def cmd_checkin(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    today = datetime.date.today()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT points, streak, last_checkin FROM users WHERE telegram_id=$1", uid)
        if row and row['last_checkin'] == today: return await msg.answer("✅ Already checked in today!")
        streak = (row['streak'] + 1) if row else 1
        bonus = min(streak, 7) * 5
        new_points = (row['points'] + bonus) if row else bonus
        await conn.execute("UPDATE users SET points=$1, streak=$2, last_checkin=$3 WHERE telegram_id=$4", new_points, streak, today, uid)
    await msg.answer(f"✅ +{bonus} points! Total: {new_points} | Streak: {streak} days")

async def cmd_tap(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT energy, points, tier FROM users WHERE telegram_id=$1", uid)
        if not user or user['energy'] < 5: return await msg.answer("❌ Not enough energy. Wait a few seconds.")
        multiplier = get_multiplier(user['tier'])
        gain = int(5 * multiplier)
        new_energy = user['energy'] - 5
        new_points = user['points'] + gain
        await conn.execute("UPDATE users SET energy=$1, points=$2, last_energy_update=NOW() WHERE telegram_id=$3", new_energy, new_points, uid)
    await msg.answer(f"⚡ +{gain} points! Total: {new_points} | Energy: {new_energy}")

async def cmd_crypto(msg: types.Message):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network&vs_currencies=usd")
            data = r.json()
            await msg.answer(f"💰 Crypto: BTC ${data['bitcoin']['usd']} | ETH ${data['ethereum']['usd']} | TON ${data['the-open-network']['usd']}")
    except:
        await msg.answer("⚠️ Crypto prices unavailable.")

async def cmd_donate(msg: types.Message):
    await msg.answer(f"🤝 Donate TON: {TON_WALLET}\nUSDT (TRC20): TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ")

async def cmd_upgrade(msg: types.Message):
    await msg.answer(f"💎 Premium: Pro 9.9 TON/month, Business 29 TON/month.\nSend TON to {TON_WALLET}\nMemo: {msg.from_user.id}\nAfter payment use /paid")

async def cmd_tasks(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", uid)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES ($1,$2)", uid, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", uid)
        text = "📋 Daily Tasks:\n\n" + "\n".join(f"{'✅' if r['done'] else '❌'} {r['description']} (ID:{r['id']})" for r in rows)
        await msg.answer(text + "\n\nUse /done [task_id] to complete.")

async def cmd_oracle(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Ask Oracle", callback_data="oracle_ask"))
    builder.row(types.InlineKeyboardButton(text="🖥️ System Scan", callback_data="oracle_scan"))
    builder.row(types.InlineKeyboardButton(text="📈 Prediction", callback_data="oracle_predict"))
    builder.row(types.InlineKeyboardButton(text="📜 Daily Mission", callback_data="oracle_mission"))
    await msg.answer("🔮 Oracle+", reply_markup=builder.as_markup())

async def cmd_peace(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🕊️ Peace Path", callback_data="peace_path"))
    builder.row(types.InlineKeyboardButton(text="💡 Innovation Path", callback_data="innovation_path"))
    builder.row(types.InlineKeyboardButton(text="❤️ Humanity Path", callback_data="humanity_path"))
    await msg.answer("☮️ Peace Game - Choose path:", reply_markup=builder.as_markup())

async def cmd_wallet(msg: types.Message):
    async with pool.acquire() as conn:
        bal = await conn.fetchval("SELECT balance FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
    await msg.answer(f"👛 Wallet\nBalance: {bal:.2f} TON")

async def cmd_referral(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        code = await conn.fetchval("SELECT referral_code FROM users WHERE telegram_id=$1", uid)
        count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE referred_by=$1", uid)
    code = code or f"SLH{uid}"
    link = f"https://t.me/SLH_Claude_bot?start=ref_{uid}"
    await msg.answer(f"🔗 Your referral link:\n{link}\n👥 Invited: {count} users\n⭐ +50 points per invite")

async def cmd_dashboard(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        urow = await conn.fetchrow("SELECT points, tier, streak, balance FROM users WHERE telegram_id=$1", uid)
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        active = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
        rank = await conn.fetchval("SELECT COUNT(*)+1 FROM users WHERE points > (SELECT points FROM users WHERE telegram_id=$1)", uid) or 1
        open_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE user_id=$1 AND done=FALSE", uid)
        done_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE user_id=$1 AND done=TRUE", uid)
        await msg.answer(
            f"📋 Dashboard\n\n👤 Your Profile\n⭐ Points: {urow['points']}\n🏆 Tier: {urow['tier'].upper()}\n"
            f"🥇 Rank: #{rank}\n🔥 Streak: {urow['streak']}\n💎 Balance: {urow['balance']:.2f} TON\n\n"
            f"👥 Community\n👥 Users: {total}\n✅ Active today: {active}\n\n📝 Tasks: {open_tasks} open / {done_tasks} done"
        )

async def cmd_admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("👑 Admin only.")
    await msg.answer("👑 Admin panel. Use /users, /broadcast, /morning, /doctor, /statusapi, /setreminder, /backup, /crm, /stats, /events, /segments")

async def cmd_help(msg: types.Message):
    await msg.answer("📘 Commands: /start, /register, /tap, /tasks, /done, /checkin, /points, /wallet, /deposit, /transfer, /upgrade, /paid, /referral, /leaderboard, /dashboard, /addcustomer, /customers, /addnote, /notes, /vip, /invite, /crypto, /donate, /guide, /oracle, /peace, /admin, /users, /broadcast, /morning, /doctor, /statusapi, /setreminder, /backup, /crm, /stats, /events, /segments, /profile, /myid, /identity, /myidentity, /simdeposit")

# ------------------------------ ADDITIONAL COMMANDS (existing from your backup) ------------------------------
@dp.message(Command("addcustomer"))
async def cmd_addcustomer(msg: types.Message):
    parts = msg.text.split(" ", 2)
    if len(parts) < 3: return await msg.answer("Usage: /addcustomer [name] [phone]")
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO crm_notes (user_id, note) VALUES ($1,$2)", msg.from_user.id, f"CUSTOMER: {parts[1]} | PHONE: {parts[2]}")
    await msg.answer(f"Customer {parts[1]} added!")

@dp.message(Command("customers"))
async def cmd_customers(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE 'CUSTOMER:%' ORDER BY created_at DESC LIMIT 20", msg.from_user.id)
        if not rows: return await msg.answer("No customers yet.")
        text = "Your Customers:\n\n" + "\n".join(f"{i+1}. {r['note']} | {r['created_at'].strftime('%d/%m/%Y')}" for i, r in enumerate(rows))
    await msg.answer(text)

@dp.message(Command("addnote"))
async def cmd_addnote(msg: types.Message):
    parts = msg.text.split(" ", 2)
    if len(parts) < 3: return await msg.answer("Usage: /addnote [customer_id] [note]")
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO crm_notes (user_id, note) VALUES ($1,$2)", msg.from_user.id, f"NOTE:{parts[1]}:{parts[2]}")
    await msg.answer("Note added.")

@dp.message(Command("notes"))
async def cmd_notes(msg: types.Message):
    parts = msg.text.split(" ", 1)
    if len(parts) < 2: return await msg.answer("Usage: /notes [customer_id]")
    cid = parts[1]
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE $2 ORDER BY created_at DESC LIMIT 10", msg.from_user.id, f"NOTE:{cid}:%")
        if not rows: return await msg.answer("No notes.")
        text = f"Notes for {cid}:\n\n" + "\n".join(f"[{r['created_at'].strftime('%H:%M')}] {r['note'].split(':',2)[-1]}" for r in rows)
    await msg.answer(text)

@dp.message(Command("vip"))
async def cmd_vip(msg: types.Message):
    await msg.answer(f"💎 VIP Group\nCost: 18 ILS\nSend TON to {TON_WALLET}\nMemo: VIP+{msg.from_user.id}")

@dp.message(Command("invite"))
async def cmd_invite(msg: types.Message):
    link = f"https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}"
    await msg.answer(f"🔗 Invite link: {link}\n⭐ +50 points per friend!")

@dp.message(Command("identity"))
async def cmd_identity(msg: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.name)
    await msg.answer("What is your name?")

class IdentityForm(StatesGroup):
    name = State()
    vision = State()
    values = State()

@dp.message(IdentityForm.name)
async def identity_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await state.set_state(IdentityForm.vision)
    await msg.answer("What is your vision? (one sentence)")

@dp.message(IdentityForm.vision)
async def identity_vision(msg: types.Message, state: FSMContext):
    await state.update_data(vision=msg.text.strip())
    await state.set_state(IdentityForm.values)
    await msg.answer("Choose 3 values (separated by commas)")

@dp.message(IdentityForm.values)
async def identity_values(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    name, vision = data['name'], data['vision']
    values = [v.strip() for v in msg.text.split(",")[:3]]
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO identity (user_id, name, vision, values) VALUES ($1,$2,$3,$4) ON CONFLICT (user_id) DO UPDATE SET name=$2, vision=$3, values=$4", msg.from_user.id, name, vision, values)
        await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id=$1", msg.from_user.id)
    await state.clear()
    await msg.answer(f"Identity created!\nName: {name}\nVision: {vision}\nValues: {', '.join(values)}\n+50 points!")

@dp.message(Command("myidentity"))
async def cmd_myidentity(msg: types.Message):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name, vision, values FROM identity WHERE user_id=$1", msg.from_user.id)
        if not row: await msg.answer("Not set. Use /identity")
        else: await msg.answer(f"Name: {row['name']}\nVision: {row['vision']}\nValues: {', '.join(row['values'])}")

@dp.message(Command("done"))
async def cmd_done(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("Usage: /done [task_id]")
    try: task_id = int(parts[1])
    except: return await msg.answer("Invalid ID")
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id=$1 AND user_id=$2", task_id, uid)
        if not task or task['done']: return await msg.answer("Task not found or already done.")
        await conn.execute("UPDATE tasks SET done = TRUE WHERE id=$1", task_id)
        await conn.execute("UPDATE users SET points = points + 10 WHERE telegram_id=$1", uid)
    await msg.answer("✅ Task completed! +10 points.")

@dp.message(Command("deposit"))
async def cmd_deposit(msg: types.Message):
    await msg.answer(f"📥 Deposit TON to:\n{TON_WALLET}\nMemo: {msg.from_user.id}")

@dp.message(Command("transfer"))
async def cmd_transfer(msg: types.Message):
    await msg.answer("↗️ Internal transfer coming soon.")

@dp.message(Command("paid"))
async def cmd_paid(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    parts = msg.text.split()
    if len(parts) < 3: return await msg.answer("Usage: /paid [user_id] [pro/business]")
    target = int(parts[1]); plan = parts[2].lower()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET tier=$1 WHERE telegram_id=$2", plan, target)
    await msg.answer(f"User {target} upgraded to {plan}.")
    await bot.send_message(target, f"🎉 Your account upgraded to {plan.upper()}!")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users WHERE points>0 ORDER BY points DESC LIMIT 10")
        if not rows: return await msg.answer("No users yet.")
        board = "\n".join(f"{i+1}. {r['username']} – {r['points']} pts" for i, r in enumerate(rows))
    await msg.answer(f"🏆 Leaderboard\n{board}")

@dp.message(Command("users"))
async def cmd_users(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id, username, tier, points FROM users ORDER BY points DESC LIMIT 20")
        text = "\n".join(f"{r['username']} ({r['telegram_id']}) | {r['tier']} | {r['points']} pts" for r in rows)
    await msg.answer(f"👥 Users\n{text}")

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    text = msg.text.replace("/broadcast", "", 1).strip()
    if not text: return await msg.answer("Usage: /broadcast [message]")
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM users")
        sent = 0
        for (uid,) in users:
            try: await bot.send_message(uid, text); sent += 1; await asyncio.sleep(0.05)
            except: pass
    await msg.answer(f"📢 Broadcast sent to {sent} users.")

@dp.message(Command("morning"))
async def cmd_morning(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    today = datetime.date.today()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        new = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at::date = $1", today)
        checked = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_checkin = $1", today)
    await msg.answer(f"☀️ Morning Report {today}\n👥 Total: {total} (+{new})\n✅ Checked in: {checked}")

@dp.message(Command("doctor"))
async def cmd_doctor(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    try:
        async with pool.acquire() as conn: await conn.fetchval("SELECT 1")
        db_status = "✅ Connected"
    except: db_status = "❌ Error"
    await msg.answer(f"🩺 System Health\nDB: {db_status}\nBot: ✅ Running\nRailway: ✅")

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    await msg.answer("📡 API Status\n✅ Railway online\n✅ DB online\n✅ Telegram online")

@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("Usage: /setreminder HH:MM")
    await msg.answer(f"⏰ Reminder set for {parts[1]} (coming soon)")

@dp.message(Command("backup"))
async def cmd_backup(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks")
        notes = await conn.fetchval("SELECT COUNT(*) FROM crm_notes")
    await msg.answer(f"💾 Backup status\n👥 Users: {users}\n📝 Tasks: {tasks}\n📋 Notes: {notes}\n✅ Auto-backup daily")

@dp.message(Command("crm"))
async def cmd_crm(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    async with pool.acquire() as conn:
        tiers = await conn.fetch("SELECT tier, COUNT(*) FROM users GROUP BY tier")
        text = "\n".join(f"{r['tier']}: {r['count']}" for r in tiers)
    await msg.answer(f"🗂️ CRM Tiers\n{text}")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        active = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
        pro = await conn.fetchval("SELECT COUNT(*) FROM users WHERE tier='pro'")
        biz = await conn.fetchval("SELECT COUNT(*) FROM users WHERE tier='business'")
        total_pts = await conn.fetchval("SELECT SUM(points) FROM users") or 0
    await msg.answer(f"📊 Stats\n👥 Users: {total}\n✅ Active today: {active}\n💎 Pro: {pro} | Business: {biz}\n⭐ Total points: {total_pts}")

@dp.message(Command("events"))
async def cmd_events(msg: types.Message):
    await msg.answer("📅 Upcoming events:\n🔜 NFT Launch\n🔜 Token Sale Q3\n🔜 Community AMA")

@dp.message(Command("segments"))
async def cmd_segments(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only.")
    async with pool.acquire() as conn:
        active = await conn.fetchval("SELECT COUNT(*) FROM users WHERE points >= 100")
        loyal = await conn.fetchval("SELECT COUNT(*) FROM users WHERE streak >= 7")
        premium = await conn.fetchval("SELECT COUNT(*) FROM users WHERE tier != 'free'")
    await msg.answer(f"🎯 Segments\nActive (100+ pts): {active}\nLoyal (7+ streak): {loyal}\nPremium: {premium}")

@dp.message(Command("profile"))
async def cmd_profile(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT username, tier, points, streak, balance FROM users WHERE telegram_id=$1", uid)
        if not row: return await msg.answer("Register with /register")
        await msg.answer(f"👤 Profile\nName: {row['username']}\nTier: {row['tier'].upper()}\nPoints: {row['points']}\nStreak: {row['streak']}\nBalance: {row['balance']:.2f} TON")

@dp.message(Command("myid"))
async def cmd_myid(msg: types.Message):
    await msg.answer(f"🆔 Your ID: {msg.from_user.id}")

@dp.message(Command("guide"))
async def cmd_guide(msg: types.Message):
    await msg.answer("📖 Economic Guide: Use non‑custodial wallets, stablecoins, avoid CBDC. Support via /donate")

@dp.message(Command("faq"))
async def cmd_faq(msg: types.Message):
    await msg.answer("❓ FAQ: /checkin for points, /deposit for TON, /upgrade for premium")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: types.Message):
    await msg.answer("📚 Tutorial: 1. /register 2. /checkin 3. /deposit 4. /upgrade")

@dp.message(Command("simdeposit"))
async def cmd_simdeposit(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("Usage: /simdeposit [amount]")
    try: amount = float(parts[1])
    except: return await msg.answer("Invalid amount.")
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE telegram_id = $2", amount, msg.from_user.id)
        new_balance = await conn.fetchval("SELECT balance FROM users WHERE telegram_id = $1", msg.from_user.id)
        await conn.execute("UPDATE users SET tier = CASE WHEN $1 >= 29 THEN 'business' WHEN $1 >= 9.9 THEN 'pro' ELSE 'free' END WHERE telegram_id = $2", new_balance, msg.from_user.id)
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id = $1", msg.from_user.id)
    await msg.answer(f"💰 Simulated deposit: {amount} TON\nBalance: {new_balance:.2f} TON\nTier: {tier.upper()}")

@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(msg: types.Message):
    if not GROQ_API_KEY: return await msg.answer("🤖 AI is disabled (GROQ_API_KEY missing).")
    await bot.send_chat_action(msg.chat.id, "typing")
    try:
        client = groq.Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":msg.text}],
            max_tokens=400, temperature=0.7
        )
        await msg.answer(resp.choices[0].message.content[:4096])
    except Exception as e:
        await msg.answer(f"⚠️ AI error: {str(e)[:200]}")

# ------------------------------ MAIN CALLBACK HANDLER ------------------------------
@dp.callback_query()
async def main_callback(call: types.CallbackQuery):
    await call.answer()
    try:
        data = call.data
        msg = call.message
        handlers = {
            "status": cmd_status, "points": cmd_points, "checkin": cmd_checkin, "tap": cmd_tap,
            "crypto": cmd_crypto, "donate": cmd_donate, "upgrade": cmd_upgrade, "tasks": cmd_tasks,
            "oracle": cmd_oracle, "peace": cmd_peace, "wallet": cmd_wallet, "referral": cmd_referral,
            "dashboard": cmd_dashboard, "admin": cmd_admin, "help": cmd_help
        }
        if data in handlers:
            await handlers[data](msg)
        else:
            await msg.answer("✨ Feature coming soon")
    except Exception as e:
        await call.message.answer(f"⚠️ Error: {str(e)[:200]}")

# ------------------------------ MAIN ------------------------------
async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())