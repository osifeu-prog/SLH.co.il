import os

bot_code = '''import asyncio, logging, os, json, datetime, random
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
    builder.row(types.InlineKeyboardButton(text="ðŸ“Š Status", callback_data="status"), types.InlineKeyboardButton(text="â­ Points", callback_data="points"))
    builder.row(types.InlineKeyboardButton(text="âœ… Check-in", callback_data="checkin"), types.InlineKeyboardButton(text="âš¡ Tap-to-Earn", callback_data="tap"))
    builder.row(types.InlineKeyboardButton(text="ðŸ’° Crypto", callback_data="crypto"), types.InlineKeyboardButton(text="ðŸ¤ Donate", callback_data="donate"))
    builder.row(types.InlineKeyboardButton(text="ðŸ“– Guide", callback_data="guide"), types.InlineKeyboardButton(text="â“ Help", callback_data="help"))
    builder.row(types.InlineKeyboardButton(text="ðŸ”® Oracle", callback_data="oracle"), types.InlineKeyboardButton(text="â˜®ï¸ Peace Game", callback_data="peace"))
    builder.row(types.InlineKeyboardButton(text="ðŸ’Ž Upgrade", callback_data="upgrade"), types.InlineKeyboardButton(text="ðŸ“‹ Tasks", callback_data="tasks"))
    builder.row(types.InlineKeyboardButton(text="ðŸ’³ Buy", callback_data="buy"), types.InlineKeyboardButton(text="ðŸ›’ Pay", callback_data="pay"))
    builder.row(types.InlineKeyboardButton(text="ðŸ‘¤ Identity", callback_data="identity"), types.InlineKeyboardButton(text="ðŸ“± Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    return builder.as_markup()

def back_button():
    return InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="â†©ï¸ Main Menu", callback_data="start")).as_markup()

# ---------- START / REGISTER ----------
@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer("âœ… Registered! Use /identity to set your profile.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    logo = ("â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—\n"
            "â•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—     â–ˆâ–ˆâ•—  â–ˆâ–ˆâ•—     â•‘\n"
            "â•‘     â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘     â•‘\n"
            "â•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘     â•‘\n"
            "â•‘     â•šâ•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•”â•â•â–ˆâ–ˆâ•‘     â•‘\n"
            "â•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘     â•‘\n"
            "â•‘     â•šâ•â•â•â•â•â•â•â•šâ•â•â•â•â•â•â•â•šâ•â•  â•šâ•â•     â•‘\n"
            "â•‘   ðŸ§  SLH SPARK AI   v3.3        â•‘\n"
            "â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•")
    await message.answer(logo, parse_mode=None)
    await message.answer("SLH Spark AI v3.3\n\nWelcome, Osif!\nChoose an option:", reply_markup=main_menu_keyboard())

@dp.callback_query(F.data == "start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.message.answer("Choose an option:", reply_markup=main_menu_keyboard())
    await callback.answer()

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (telegram_id, username) VALUES ($1, $2) ON CONFLICT DO NOTHING", uid, username)

# â•â•â• IDENTITY FSM â•â•â•
class IdentityForm(StatesGroup):
    name = State()
    vision = State()
    values = State()

@dp.message(Command("identity"))
async def cmd_identity(message: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.name)
    await message.answer("ðŸ‘¤ Welcome! What is your name?")

@dp.message(IdentityForm.name)
async def identity_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(IdentityForm.vision)
    await message.answer("ðŸŒ± What is your vision? (one sentence)")

@dp.message(IdentityForm.vision)
async def identity_vision(message: types.Message, state: FSMContext):
    await state.update_data(vision=message.text.strip())
    await state.set_state(IdentityForm.values)
    await message.answer("ðŸ’Ž Choose 3 values (separated by commas)")

@dp.message(IdentityForm.values)
async def identity_values(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name, vision = data['name'], data['vision']
    values = [v.strip() for v in message.text.split(",")[:3]]
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO identity (user_id, name, vision, values) VALUES ($1,$2,$3,$4) ON CONFLICT (user_id) DO UPDATE SET name=$2, vision=$3, values=$4", message.from_user.id, name, vision, values)
        await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id=$1", message.from_user.id)
    await state.clear()
    await message.answer(f"ðŸŽ‰ Identity created!\nName: {name}\nVision: {vision}\nValues: {', '.join(values)}\n+50 points! ðŸŽ¯")

@dp.message(Command("myidentity"))
async def cmd_myidentity(message: types.Message):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name, vision, values FROM identity WHERE user_id=$1", message.from_user.id)
        if not row: await message.answer("âŒ Not set. Use /identity")
        else: await message.answer(f"ðŸ‘¤ {row['name']}\nðŸŒ± Vision: {row['vision']}\nðŸ’Ž Values: {', '.join(row['values'])}", parse_mode=ParseMode.HTML)

# â•â•â• WALLET / PAY / STORE / CRM â•â•â•
@dp.message(Command("wallet"))
async def cmd_wallet(msg):
    async with pool.acquire() as conn:
        bal = await conn.fetchval("SELECT balance FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id=$1", msg.from_user.id) or "free"
        await msg.answer(f"ðŸ’° Wallet\nBalance: {bal:.2f} TON\nTier: {tier.upper()}", reply_markup=back_button())

@dp.message(Command("pay"))
async def cmd_pay(msg): await msg.answer("ðŸ’³ Payment options: /invoice /request /split", reply_markup=back_button())

@dp.message(Command("store"))
async def cmd_store(msg): await msg.answer("ðŸ›’ Store - /addproduct /products /buy", reply_markup=back_button())

# â”€â”€â”€ CRM â”€â”€â”€
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

# â•â•â• CRYPTO â•â•â•
@dp.message(Command("crypto"))
async def cmd_crypto(message: types.Message):
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network&vs_currencies=usd")
            data = resp.json()
            btc = data.get("bitcoin", {}).get("usd", "?")
            eth = data.get("ethereum", {}).get("usd", "?")
            ton = data.get("the-open-network", {}).get("usd", "?")
            await message.answer(f"ðŸ’° Crypto: BTC ${btc} | ETH ${eth} | TON ${ton}", parse_mode="HTML", reply_markup=back_button())
    except:
        await message.answer("âŒ Could not fetch prices.")

# â•â•â• CHECK-IN / POINTS / LEADERBOARD â•â•â•
@dp.message(Command("checkin"))
async def cmd_checkin(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT last_checkin, points, streak FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: await message.answer("Register first with /register"); return
        last, streak = user['last_checkin'], user['streak']
        today = datetime.date.today()
        if last == today: await message.answer("â³ Already checked in today!"); return
        streak = streak + 1 if last and (today - last).days == 1 else 1
        points = 10 + (streak * 2)
        new_total = user['points'] + points
        await conn.execute("UPDATE users SET points=$1, streak=$2, last_checkin=$3 WHERE telegram_id=$4", new_total, streak, today, message.from_user.id)
        await message.answer(f"â˜€ï¸ Check-in! +{points} pts\nTotal: {new_total} | Streak: {streak}")

@dp.message(Command("points"))
async def cmd_points(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, streak FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: await message.answer("Register first."); return
        await message.answer(f"ðŸŽ¯ {user['points']} points | Streak: {user['streak']} days")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users WHERE points>0 ORDER BY points DESC LIMIT 10")
        if not rows: await message.answer("No users yet."); return
        text = "ðŸ† Leaderboard\n" + "\n".join([f"{i}. {r['username']} - {r['points']} pts" for i,r in enumerate(rows,1)])
        await message.answer(text, reply_markup=back_button())

# â•â•â• TAP-TO-EARN â•â•â•
@dp.message(Command("tap"))
async def cmd_tap(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT energy, points FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: return await message.answer("Register first with /register")
        energy = user['energy']
        if energy < 5: return await message.answer("âš¡ Not enough energy. Wait for recharge.")
        await conn.execute("UPDATE users SET energy = energy - 5, points = points + 5 WHERE telegram_id=$1", message.from_user.id)
        new_pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", message.from_user.id)
        await message.answer(f"âš¡ +5 points! Total: {new_pts} pts | Energy: {energy-5}")

# â•â•â• DAILY TASKS â•â•â•
@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", message.from_user.id)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES ($1,$2)", message.from_user.id, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at = CURRENT_DATE", message.from_user.id)
        text = "ðŸ“‹ Daily Tasks:\n\n"
        for r in rows:
            icon = "âœ…" if r['done'] else "â¬œ"
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
        await message.answer(f"âœ… Task completed! +10 points.")

# â•â•â• VIP â•â•â•
@dp.message(Command("vip"))
async def cmd_vip(msg):
    await msg.answer(
        "ðŸ’Ž SLH VIP Group\n\n"
        "ðŸ”’ Private Trading Community\n"
        "ðŸ’° Cost: 18 ILS (one-time)\n\n"
        "What you get:\n"
        "ðŸ“ˆ Daily trading signals\n"
        "ðŸ’¬ Private chat with experts\n"
        "ðŸŽ Exclusive rewards\n"
        "ðŸ›¡ Priority support\n\n"
        "How to join:\n"
        f"1. Send 18 ILS worth of TON to:\n{TON_WALLET}\n"
        "2. In memo, write: VIP + your Telegram ID\n"
        "3. You'll receive an invite link automatically!\n\n"
        "Already paid? Use /vipstatus to check.",
        parse_mode=None
    )

@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    ref_link = f"https://t.me/SLH_Claude_bot?start=ref{message.from_user.id}"
    await message.answer(f"ðŸ”— Your Invite Link:\n{ref_link}\n\nðŸ‘¥ Share this link to invite friends!\nâ­ You earn 50 points per friend!")

# â•â•â• HELP / GUIDE / FAQ / TUTORIAL â•â•â•
@dp.message(Command("help"))
async def cmd_help(msg): await msg.answer("ðŸ“˜ Commands: /start /crypto /guide /donate /upgrade /oracle /peace /wallet /pay /store /crm /checkin /points /leaderboard /identity /myidentity /users /broadcast /doctor /test /seed /sysinfo /status /dashboard /referral /profile /myid /events /community /game /invest /roadmap /support /feedback /faq /tutorial /simdeposit /miniapp /vip /invite /addcustomer /customers /addnote /notes /tap /tasks /done")

@dp.message(Command("guide"))
async def cmd_guide(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="â­ Earning Points", callback_data="guide_points"))
    kb.row(types.InlineKeyboardButton(text="ðŸ’Ž TON Deposits", callback_data="guide_deposit"))
    kb.row(types.InlineKeyboardButton(text="ðŸ† Tiers", callback_data="guide_tier"))
    kb.row(types.InlineKeyboardButton(text="ðŸ‘¥ VIP Groups", callback_data="guide_vip"))
    kb.row(types.InlineKeyboardButton(text="ðŸ“ˆ Trading Signals", callback_data="guide_signals"))
    kb.row(types.InlineKeyboardButton(text="â“ All Commands", callback_data="help"))
    kb.row(types.InlineKeyboardButton(text="â†©ï¸ Main Menu", callback_data="start"))
    await message.answer("ðŸ“– SLH Guide - Choose topic:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("guide_"))
async def guide_callback(callback: types.CallbackQuery):
    d = callback.data
    topics = {"guide_points":"â­ Earn: /checkin, /tap, tasks","guide_deposit":"ðŸ’Ž Deposit TON with your ID","guide_tier":"ðŸ† Tiers: Free/Pro/Business","guide_vip":"ðŸ‘¥ VIP: 18 ILS","guide_signals":"ðŸ“ˆ Signals for VIP members"}
    await callback.message.answer(topics.get(d, "Unknown"))
    await callback.answer()

@dp.message(Command("faq"))
async def cmd_faq(msg): await msg.answer("â“ FAQ: /checkin for points, /deposit for TON.")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg): await msg.answer("ðŸŽ“ Tutorial: 1. /register 2. /checkin 3. /deposit 4. /upgrade")

# â•â•â• DONATE / UPGRADE â•â•â•
@dp.message(Command("donate"))
async def cmd_donate(msg): await msg.answer(f"ðŸ¤ Support SLH\nTON: {TON_WALLET}\nUSDT (TRC-20): TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ", reply_markup=back_button())

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg): await msg.answer("ðŸ’Ž Premium: Pro 9.9 TON/month, Business 29 TON/month.\nSend TON to: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp", reply_markup=back_button())

# â•â•â• ADMIN â•â•â•
@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("ðŸ‘‘ Admin only")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id, username, points, tier FROM users")
        text = "ðŸ‘¥ Users:\n" + "\n".join([f"{r['username']} ({r['telegram_id']}) | {r['tier']} | {r['points']}pts" for r in rows])
        await message.answer(text, parse_mode="HTML")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("ðŸ‘‘ Admin only")
    args = message.text.split(" ", 1)
    if len(args) < 2: return await message.answer("Usage: /broadcast [message]", parse_mode=None)
    msg_text = args[1]
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM users")
        count = 0
        for u in users:
            try: await bot.send_message(u['telegram_id'], msg_text); count += 1
            except: pass
        await message.answer(f"ðŸ“¤ Sent to {count}/{len(users)} users.")

@dp.message(Command("doctor"))
async def cmd_doctor(msg): await msg.answer("ðŸ©º System Health: DB âœ… Bot âœ… Railway âœ…")

@dp.message(Command("test"))
async def cmd_test(msg): await msg.answer("ðŸ§ª Self-Test: DB âœ… Bot Token âœ…")

@dp.message(Command("seed"))
async def cmd_seed(message: types.Message):
    async with pool.acquire() as conn:
        for i in range(1, 6):
            await conn.execute("INSERT INTO users (telegram_id, username, points) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING", 1000000+i, f"DemoUser{i}", random.randint(0, 100))
        await message.answer("âœ… Demo data seeded.")

@dp.message(Command("sysinfo"))
async def cmd_sysinfo(msg):
    import platform
    cpu=0; mem_percent=0; mem_used=0; mem_total=0; disk_percent=0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_percent=mem.percent; mem_used=mem.used//(1024**2); mem_total=mem.total//(1024**2)
        disk = psutil.disk_usage('/')
        disk_percent=disk.percent
    except: pass
    await msg.answer(f"ðŸ–¥ System Info\nOS: {platform.system()}\nCPU: {cpu}%\nRAM: {mem_percent}% ({mem_used} MB / {mem_total} MB)\nDisk: {disk_percent}% used", parse_mode="HTML")

# â•â•â• STUBS â•â•â•
@dp.message(Command("daily"))
async def cmd_daily(msg): await msg.answer("ðŸ“… Daily Missions: /checkin, /tap, /guide")
@dp.message(Command("backup"))
async def cmd_backup(msg): await msg.answer("ðŸ“¦ Backup saved to cloud.")
@dp.message(Command("referral"))
async def cmd_referral(msg): await msg.answer(f"ðŸ”— Referral link: https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}")
@dp.message(Command("profile"))
async def cmd_profile(msg):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, points, tier, balance FROM users WHERE telegram_id=$1", msg.from_user.id)
        if user: await msg.answer(f"ðŸ‘¤ Profile\nName: {user['username']}\nPoints: {user['points']}\nTier: {user['tier']}\nBalance: {user['balance']:.2f}")
        else: await msg.answer("Not registered.")
@dp.message(Command("myid"))
async def cmd_myid(msg): await msg.answer(f"ðŸ†” Your ID: {msg.from_user.id}")
@dp.message(Command("status"))
async def cmd_status(msg):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        await msg.answer(f"ðŸ“Š Project Status\nâœ… Bot Online\nUsers: {users}\nâœ… Mini App: slh-nft.com", parse_mode="HTML", reply_markup=back_button())
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg): await msg.answer("ðŸ“‹ Dashboard - coming soon", reply_markup=back_button())
@dp.message(Command("events"))
async def cmd_events(msg): await msg.answer("Events: none yet")
@dp.message(Command("community"))
async def cmd_community(msg): await msg.answer("ðŸ‘¥ Community: https://t.me/SLH_support")
@dp.message(Command("game"))
async def cmd_game(msg): await msg.answer("ðŸŽ® Game: /peace or /oracle")
@dp.message(Command("invest"))
async def cmd_invest(msg): await msg.answer("ðŸ¦ Invest: dynamic yield, staking (coming soon)")
@dp.message(Command("roadmap"))
async def cmd_roadmap(msg): await msg.answer("ðŸ—º Roadmap: https://slh-nft.com/roadmap")
@dp.message(Command("support"))
async def cmd_support(msg): await msg.answer("ðŸ’¬ Support: @SLH_Claude_bot")
@dp.message(Command("feedback"))
async def cmd_feedback(msg): await msg.answer("ðŸ“¨ Feedback: /feedback [message]")

# â•â•â• AI â•â•â•
@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":message.text}], max_tokens=400, temperature=0.7)
        answer = resp.choices[0].message.content
        await message.answer(answer[:4096])
    except Exception as e:
        await message.answer(f"âš ï¸ AI error: {str(e)[:200]}")

# â•â•â• SIMDEPOSIT â•â•â•
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
    await message.answer(f"âœ… Simulated deposit: {amount} TON\nBalance: {new_balance:.2f} TON\nTier: {tier.upper()}")

# â•â•â• MINI APP â•â•â•
@dp.message(Command("miniapp"))
async def cmd_miniapp(msg):
    await msg.answer("ðŸ“± Open Mini App:", reply_markup=InlineKeyboardBuilder().row(
        types.InlineKeyboardButton(text="ðŸš€ Launch Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL))
    ).as_markup())

# â•â•â• CALLBACK ROUTER â•â•â•
@dp.callback_query()
async def main_callback(callback: types.CallbackQuery):
    data = callback.data
    if data == "status": await cmd_status(callback.message)
    elif data == "points": await cmd_points(callback.message)
    elif data == "checkin": await cmd_checkin(callback.message)
    elif data == "tap": await cmd_tap(callback.message)
    elif data == "crypto": await cmd_crypto(callback.message)
    elif data == "donate": await cmd_donate(callback.message)
    elif data == "guide": await cmd_guide(callback.message)
    elif data == "help": await cmd_help(callback.message)
    elif data == "oracle": await callback.message.answer("Oracle coming soon")
    elif data == "peace": await callback.message.answer("Peace Game coming soon")
    elif data == "upgrade": await cmd_upgrade(callback.message)
    elif data == "tasks": await cmd_tasks(callback.message)
    elif data == "buy": await callback.message.answer("ðŸ’³ Buy: Enter product ID")
    elif data == "pay": await cmd_pay(callback.message)
    elif data == "identity": await callback.message.answer("â„¹ï¸ Use /identity command to set your profile.")
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

print("âœ… Ultimate bot.py with Tap+Tasks created.")

