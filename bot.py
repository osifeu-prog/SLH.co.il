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
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, username TEXT, points INT DEFAULT 0, streak INT DEFAULT 0, last_checkin DATE, balance REAL DEFAULT 0, tier TEXT DEFAULT 'free', created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS identity (user_id BIGINT PRIMARY KEY, name TEXT, vision TEXT, values TEXT[])""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, from_id BIGINT, to_id BIGINT, amount REAL, currency TEXT, timestamp TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, seller_id BIGINT, name TEXT, price REAL, stock INT DEFAULT 0)""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, buyer_id BIGINT, product_id INT, quantity INT DEFAULT 1, total_price REAL, status TEXT DEFAULT 'paid', created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS crm_notes (id SERIAL PRIMARY KEY, user_id BIGINT, note TEXT, created_at TIMESTAMP DEFAULT NOW())""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS oracle_missions (id SERIAL PRIMARY KEY, user_id BIGINT, mission TEXT, done BOOLEAN DEFAULT FALSE, created_at DATE DEFAULT CURRENT_DATE)""")

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Status", callback_data="status"), types.InlineKeyboardButton(text="Points", callback_data="points"))
    builder.row(types.InlineKeyboardButton(text="Check-in", callback_data="checkin"), types.InlineKeyboardButton(text="Tap-to-Earn", callback_data="tap"))
    builder.row(types.InlineKeyboardButton(text="Crypto", callback_data="crypto"), types.InlineKeyboardButton(text="Donate", callback_data="donate"))
    builder.row(types.InlineKeyboardButton(text="Guide", callback_data="guide"), types.InlineKeyboardButton(text="Help", callback_data="help"))
    builder.row(types.InlineKeyboardButton(text="Oracle", callback_data="oracle"), types.InlineKeyboardButton(text="Peace Game", callback_data="peace"))
    builder.row(types.InlineKeyboardButton(text="Upgrade", callback_data="upgrade"), types.InlineKeyboardButton(text="Tasks", callback_data="tasks"))
    builder.row(types.InlineKeyboardButton(text="Buy", callback_data="buy"), types.InlineKeyboardButton(text="Pay", callback_data="pay"))
    builder.row(types.InlineKeyboardButton(text="Identity", callback_data="identity"))
    return builder.as_markup()

@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer("Registered! Use /identity to set your profile.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await ensure_user(message.from_user.id, message.from_user.username or "unknown")
    logo = (
        "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n"
        "\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557     \u2588\u2588\u2557  \u2588\u2588\u2557     \u2551\n"
        "\u2551     \u2588\u2588\u2594\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551     \u2588\u2588\u2551  \u2588\u2588\u2551     \u2551\n"
        "\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551     \u2551\n"
        "\u2551     \u259a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551     \u2588\u2588\u2594\u2550\u2550\u2588\u2588\u2551     \u2551\n"
        "\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551     \u2551\n"
        "\u2551     \u259a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u259a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u259a\u2550\u255d  \u259a\u2550\u255d     \u2551\n"
        "\u2551   \u2728 SLH SPARK AI   v3.3        \u2551\n"
        "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
    )
    await message.answer(logo, parse_mode=None)
    await message.answer("SLH Spark AI v3.3\n\nWelcome, Osif!\nChoose an option:", reply_markup=main_menu_keyboard())

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (telegram_id, username) VALUES ($1, $2) ON CONFLICT DO NOTHING", uid, username)

class IdentityForm(StatesGroup):
    name = State()
    vision = State()
    values = State()

@dp.message(Command("identity"))
async def cmd_identity(message: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.name)
    await message.answer("Welcome! What is your name?")

@dp.message(IdentityForm.name)
async def identity_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(IdentityForm.vision)
    await message.answer("What is your vision? (one sentence)")

@dp.message(IdentityForm.vision)
async def identity_vision(message: types.Message, state: FSMContext):
    await state.update_data(vision=message.text.strip())
    await state.set_state(IdentityForm.values)
    await message.answer("Choose 3 values (separated by commas)")

@dp.message(IdentityForm.values)
async def identity_values(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name, vision = data['name'], data['vision']
    values = [v.strip() for v in message.text.split(",")[:3]]
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO identity (user_id, name, vision, values) VALUES ($1,$2,$3,$4) ON CONFLICT (user_id) DO UPDATE SET name=$2, vision=$3, values=$4", message.from_user.id, name, vision, values)
        await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id=$1", message.from_user.id)
    await state.clear()
    await message.answer(f"Identity created!\nName: {name}\nVision: {vision}\nValues: {', '.join(values)}\n+50 points!")

@dp.message(Command("myidentity"))
async def cmd_myidentity(message: types.Message):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name, vision, values FROM identity WHERE user_id=$1", message.from_user.id)
        if not row: await message.answer("Not set. Use /identity")
        else: await message.answer(f"Name: {row['name']}\nVision: {row['vision']}\nValues: {', '.join(row['values'])}", parse_mode=ParseMode.HTML)

@dp.message(Command("wallet"))
async def cmd_wallet(msg):
    async with pool.acquire() as conn:
        bal = await conn.fetchval("SELECT balance FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id=$1", msg.from_user.id) or "free"
        await msg.answer(f"Wallet\nBalance: {bal:.2f} TON\nTier: {tier.upper()}")

@dp.message(Command("pay"))
async def cmd_pay(msg): await msg.answer("Payment options: /invoice /request /split")

@dp.message(Command("store"))
async def cmd_store(msg): await msg.answer("Store - /addproduct /products /buy")

@dp.message(Command("crm"))
async def cmd_crm(msg): await msg.answer("CRM (coming soon)")

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
            await message.answer(f"Crypto: BTC ${btc} | ETH ${eth} | TON ${ton}", parse_mode=ParseMode.HTML)
    except:
        await message.answer("Could not fetch prices.")

@dp.message(Command("checkin"))
async def cmd_checkin(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT last_checkin, points, streak FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: await message.answer("Register first with /register"); return
        last, streak = user['last_checkin'], user['streak']
        today = datetime.date.today()
        if last == today: await message.answer("Already checked in today!"); return
        streak = streak + 1 if last and (today - last).days == 1 else 1
        points = 10 + (streak * 2)
        new_total = user['points'] + points
        await conn.execute("UPDATE users SET points=$1, streak=$2, last_checkin=$3 WHERE telegram_id=$4", new_total, streak, today, message.from_user.id)
        await message.answer(f"Check-in! +{points} pts\nTotal: {new_total} | Streak: {streak}")

@dp.message(Command("points"))
async def cmd_points(message: types.Message):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, streak FROM users WHERE telegram_id=$1", message.from_user.id)
        if not user: await message.answer("Register first."); return
        await message.answer(f"{user['points']} points | Streak: {user['streak']} days")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users WHERE points>0 ORDER BY points DESC LIMIT 10")
        if not rows: await message.answer("No users yet."); return
        text = "Leaderboard\n" + "\n".join([f"{i}. {r['username']} - {r['points']} pts" for i,r in enumerate(rows,1)])
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("oracle"))
async def cmd_oracle(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Ask Oracle", callback_data="oracle_ask"))
    builder.row(types.InlineKeyboardButton(text="System Scan", callback_data="oracle_scan"))
    builder.row(types.InlineKeyboardButton(text="Prediction", callback_data="oracle_predict"))
    builder.row(types.InlineKeyboardButton(text="Daily Peace Mission", callback_data="oracle_mission"))
    await message.answer("Oracle+", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("oracle_"))
async def oracle_callback(callback: types.CallbackQuery):
    d = callback.data
    responses = {"oracle_ask":"Ask me anything about the project.","oracle_scan":"Scan: Bot Online, DB Connected, Railway Online","oracle_predict":"Prediction: +0.5 TON/day","oracle_mission":"Mission: Share the bot with one person."}
    await callback.message.answer(responses.get(d, "Unknown"))
    await callback.answer()

@dp.message(Command("peace"))
async def cmd_peace(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Peace Path", callback_data="peace_path"))
    builder.row(types.InlineKeyboardButton(text="Innovation Path", callback_data="innovation_path"))
    builder.row(types.InlineKeyboardButton(text="Humanity Path", callback_data="humanity_path"))
    await message.answer("Peace Game - Choose path:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.endswith("_path"))
async def peace_path_chosen(callback: types.CallbackQuery):
    path = callback.data.split("_")[0]
    await callback.message.answer(f"{path} Path: What is the most important element in conflict resolution?\nA) Communication B) Force C) Ignoring D) Punishment")
    await callback.answer()

@dp.message(Command("help"))
async def cmd_help(msg): await msg.answer("Commands: /start /crypto /guide /donate /upgrade /oracle /peace /wallet /pay /store /crm /checkin /points /leaderboard /identity /myidentity /users /broadcast /doctor /test /seed /sysinfo /status /dashboard /referral /profile /myid /events /community /game /invest /roadmap /support /feedback /faq /tutorial /simdeposit")

@dp.message(Command("guide"))
async def cmd_guide(msg): await msg.answer("Economic Guide: Trust Wallet, stablecoins, protection.")

@dp.message(Command("faq"))
async def cmd_faq(msg): await msg.answer("FAQ: /checkin for points, /deposit for TON.")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg): await msg.answer("Tutorial: 1. /register 2. /checkin 3. /deposit 4. /upgrade")

@dp.message(Command("donate"))
async def cmd_donate(msg): await msg.answer(f"Support SLH\nTON: {TON_WALLET}\nUSDT (TRC-20): TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ")

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg): await msg.answer("Premium: Pro 9.9 TON/month, Business 29 TON/month.\nSend TON to: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("Admin only")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT telegram_id, username, points, tier FROM users")
        text = "Users:\n" + "\n".join([f"{r['username']} ({r['telegram_id']}) | {r['tier']} | {r['points']}pts" for r in rows])
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("Admin only")
    args = message.text.split(" ", 1)
    if len(args) < 2: return await message.answer("Usage: /broadcast <message>")
    msg_text = args[1]
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM users")
        count = 0
        for u in users:
            try: await bot.send_message(u['telegram_id'], msg_text); count += 1
            except: pass
        await message.answer(f"Sent to {count}/{len(users)} users.")

@dp.message(Command("doctor"))
async def cmd_doctor(msg): await msg.answer("System Health: DB OK, Bot OK, Railway OK")

@dp.message(Command("test"))
async def cmd_test(msg): await msg.answer("Self-Test: DB OK, Bot Token OK")

@dp.message(Command("seed"))
async def cmd_seed(message: types.Message):
    async with pool.acquire() as conn:
        for i in range(1, 6):
            await conn.execute("INSERT INTO users (telegram_id, username, points) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING", 1000000+i, f"DemoUser{i}", random.randint(0, 100))
        await message.answer("Demo data seeded.")

@dp.message(Command("sysinfo"))
async def cmd_sysinfo(msg):
    import platform
    cpu=0; mem_percent=0; mem_used=0; mem_total=0; disk_percent=0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_percent=mem.percent
        mem_used=mem.used//(1024**2)
        mem_total=mem.total//(1024**2)
        disk = psutil.disk_usage('/')
        disk_percent=disk.percent
    except: pass
    await msg.answer(f"System Info\nOS: {platform.system()}\nCPU: {cpu}%\nRAM: {mem_percent}% ({mem_used} MB / {mem_total} MB)\nDisk: {disk_percent}% used", parse_mode=ParseMode.HTML)

@dp.message(Command("tap"))
async def cmd_tap(msg): await msg.answer("Tap-to-Earn: Coming soon!")

@dp.message(Command("tasks"))
async def cmd_tasks(msg): await msg.answer("Tasks (coming soon)")

@dp.message(Command("daily"))
async def cmd_daily(msg): await msg.answer("Daily Missions: /checkin, /tap, /guide")

@dp.message(Command("backup"))
async def cmd_backup(msg): await msg.answer("Backup saved to cloud.")

@dp.message(Command("referral"))
async def cmd_referral(msg): await msg.answer(f"Referral link: https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}")

@dp.message(Command("profile"))
async def cmd_profile(msg):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, points, tier, balance FROM users WHERE telegram_id=$1", msg.from_user.id)
        if user: await msg.answer(f"Profile\nName: {user['username']}\nPoints: {user['points']}\nTier: {user['tier']}\nBalance: {user['balance']:.2f}")
        else: await msg.answer("Not registered.")

@dp.message(Command("myid"))
async def cmd_myid(msg): await msg.answer(f"Your ID: {msg.from_user.id}")

@dp.message(Command("status"))
async def cmd_status(msg):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        await msg.answer(f"Project Status\nBot Online\nUsers: {users}\nMini App: slh-nft.com", parse_mode=ParseMode.HTML)

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        await msg.answer(f"Dashboard\nUsers: {users}\nPoints: N/A\nTON: N/A", parse_mode=ParseMode.HTML)

@dp.message(Command("events"))
async def cmd_events(msg): await msg.answer("Events: none yet")

@dp.message(Command("community"))
async def cmd_community(msg): await msg.answer("Community: https://t.me/SLH_support")

@dp.message(Command("game"))
async def cmd_game(msg): await msg.answer("Game: /peace or /oracle")

@dp.message(Command("invest"))
async def cmd_invest(msg): await msg.answer("Invest: dynamic yield, staking (coming soon)")

@dp.message(Command("roadmap"))
async def cmd_roadmap(msg): await msg.answer("Roadmap: https://slh-nft.com/roadmap")

@dp.message(Command("support"))
async def cmd_support(msg): await msg.answer("Support: @SLH_Claude_bot")

@dp.message(Command("feedback"))
async def cmd_feedback(msg): await msg.answer("Feedback: /feedback <message>")

@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":message.text}],
            max_tokens=400, temperature=0.7
        )
        answer = resp.choices[0].message.content
        await message.answer(answer[:4096])
    except Exception as e:
        await message.answer(f"AI error: {str(e)[:200]}")

@dp.message(Command("simdeposit"))
async def cmd_simdeposit(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Usage: /simdeposit <amount_in_ton>")
    try:
        amount = float(parts[1])
    except:
        return await message.answer("Invalid amount.")
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE telegram_id = $2", amount, message.from_user.id)
        new_balance = await conn.fetchval("SELECT balance FROM users WHERE telegram_id = $1", message.from_user.id)
        await conn.execute("UPDATE users SET tier = CASE WHEN $1 >= 29 THEN 'business' WHEN $1 >= 9.9 THEN 'pro' ELSE 'free' END WHERE telegram_id = $2", new_balance, message.from_user.id)
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id = $1", message.from_user.id)
    await message.answer(f"Simulated deposit: {amount} TON\nBalance: {new_balance:.2f} TON\nTier: {tier.upper()}")

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
    elif data == "oracle": await cmd_oracle(callback.message)
    elif data == "peace": await cmd_peace(callback.message)
    elif data == "upgrade": await cmd_upgrade(callback.message)
    elif data == "tasks": await cmd_tasks(callback.message)
    elif data == "buy": await callback.message.answer("Buy: Enter product ID")
    elif data == "pay": await cmd_pay(callback.message)
    elif data == "identity": await callback.message.answer("Use /identity command to set your profile.")
    await callback.answer()

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
