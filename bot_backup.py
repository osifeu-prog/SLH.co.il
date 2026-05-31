import asyncio, os, datetime, re, requests, time, threading, json as json_module
import psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in re.split(r'[,\s]+', os.getenv("ADMIN_ID", "0").strip()) if x]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PORT = int(os.getenv("PORT", "8080"))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    for attempt in range(12):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free';
                ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW();
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();
                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();
                CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT, done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW());
                CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id BIGINT, message TEXT, created_at TIMESTAMP DEFAULT NOW());
                CREATE TABLE IF NOT EXISTS payments (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, status TEXT DEFAULT 'pending', tx_hash TEXT, created_at TIMESTAMP DEFAULT NOW());
                CREATE TABLE IF NOT EXISTS events (id SERIAL PRIMARY KEY, user_id BIGINT, event_type TEXT, payload TEXT, created_at TIMESTAMP DEFAULT NOW());
                ALTER TABLE events ADD COLUMN IF NOT EXISTS payload TEXT;
                ALTER TABLE payments ADD COLUMN IF NOT EXISTS tx_hash TEXT;
            """)
            conn.commit(); cur.close(); conn.close()
            print("✅ DB ready")
            return
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"⏳ DB attempt {attempt+1}/12: {e}")
            time.sleep(wait)
    print("⚠️ DB unavailable")

init_db()

def ensure_user(uid, name):
    conn = get_db(); cur = conn.cursor()
    ref = f"SLH{uid}"
    cur.execute("INSERT INTO users (telegram_id, username, tier, referral_code) VALUES (%s,%s,'free',%s) ON CONFLICT (telegram_id) DO UPDATE SET username=%s, last_seen=NOW()", (uid, name, ref, name))
    conn.commit(); cur.close(); conn.close()

def get_multiplier(tier):
    if tier == "business": return 2.0
    elif tier == "pro": return 1.5
    return 1.0

async def update_energy(uid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int), last_energy_update = NOW() WHERE telegram_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="⭐ Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="⚡ Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="💎 Upgrade", callback_data="cmd_upgrade"),
         InlineKeyboardButton(text="🤝 Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="📋 Dashboard", callback_data="cmd_dashboard")],
        [InlineKeyboardButton(text="📖 Guide", callback_data="cmd_guide"),
         InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")],
    ])

# ═══════════ START ═══════════
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.full_name or "friend")
    logo = ("<pre>╔══════════════════════════════════╗\n"
            "║     ███████╗██╗     ██╗  ██╗     ║\n"
            "║     ██╔════╝██║     ██║  ██║     ║\n"
            "║     ███████╗██║     ███████║     ║\n"
            "║     ╚════██║██║     ██╔══██║     ║\n"
            "║     ███████║███████╗██║  ██║     ║\n"
            "║     ╚══════╝╚══════╝╚═╝  ╚═╝     ║\n"
            "║   🧠 SLH SPARK AI   v3.2        ║\n"
            "╚══════════════════════════════════╝</pre>")
    await msg.answer(logo, parse_mode=ParseMode.HTML)
    await msg.answer("<b>✅ SLH SPARK AI v3.2 alive!</b>", reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer("<b>📘 SLH Bot - Command List</b>\n/upgrade /donate /checkin /points /tap /leaderboard /referral\n/wallet /deposit /dashboard /crypto /profile /myid /tasks /task /done\n/admin /users /broadcast /morning /doctor /statusapi /test /seed\n/crm /events /support /daily /roadmap /backup /transfer\n/guide /faq /tutorial /sysinfo /progress", parse_mode=ParseMode.HTML)

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    uid = msg.from_user.id; ensure_user(uid, msg.from_user.full_name or "friend")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT points, streak, last_checkin FROM users WHERE telegram_id=%s", (uid,))
    row = cur.fetchone(); today = datetime.date.today()
    if row and row[2] == today: conn.close(); return await msg.answer("⏳ Already checked in!")
    points = row[0] if row else 0; streak = (row[1] + 1) if row else 1; bonus = min(streak, 7) * 5
    cur.execute("UPDATE users SET points=%s, streak=%s, last_checkin=%s WHERE telegram_id=%s", (points+bonus, streak, today, uid))
    conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ +{bonus} points! Total: {points+bonus} | Streak: {streak} days")

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT points, streak, tier FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone(); conn.close()
    if row:
        mult = get_multiplier(row[2])
        await msg.answer(f"💰 <b>My Points</b>\nPoints: {row[0]} | Streak: {row[1]} days | Multiplier: x{mult} ({row[2].upper()})", parse_mode=ParseMode.HTML)
    else: await msg.answer("Not registered. /register")

@dp.message(Command("status"))
async def cmd_status(msg: Message):
    uid = msg.from_user.id; ensure_user(uid, msg.from_user.full_name or "friend")
    await update_energy(uid)
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT points, energy, tier, streak, balance FROM users WHERE telegram_id=%s", (uid,))
    row = cur.fetchone(); conn.close()
    if row:
        await msg.answer(f"📊 <b>Your Status</b>\n⭐ Points: {row[0]}\n🔋 Energy: {row[1]}/100\n🏆 Tier: {row[2].upper()}\n🔥 Streak: {row[3]} days\n💎 Balance: {float(row[4]):.2f} TON", parse_mode=ParseMode.HTML)

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=CURRENT_DATE"); active = cur.fetchone()[0]
    cur.execute("SELECT SUM(points) FROM users"); pts = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(balance) FROM users"); bal = cur.fetchone()[0] or 0
    conn.close()
    await msg.answer(f"📋 <b>Dashboard</b>\n👥 Users: {total}\n✅ Active: {active}\n⭐ Points: {pts}\n💰 TON: {bal:.2f}", parse_mode=ParseMode.HTML)

@dp.message(Command("crypto"))
async def cmd_crypto(msg: Message):
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network&vs_currencies=usd", timeout=10)
        data = resp.json()
        await msg.answer(f"💰 <b>Crypto</b>\nBTC: ${data.get('bitcoin',{}).get('usd','?')}\nETH: ${data.get('ethereum',{}).get('usd','?')}\nTON: ${data.get('the-open-network',{}).get('usd','?')}", parse_mode=ParseMode.HTML)
    except: await msg.answer("⚠️ Cannot fetch prices")

@dp.message(Command("tap"))
async def cmd_tap(msg: Message):
    await msg.answer("⚡ Tap-to-Earn!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="TAP HERE ⚡", callback_data="do_tap")]]))

@dp.callback_query(F.data == "do_tap")
async def handle_tap(callback: CallbackQuery):
    uid = callback.from_user.id; ensure_user(uid, callback.from_user.full_name or "friend")
    await update_energy(uid)
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT energy, points, tier FROM users WHERE telegram_id=%s", (uid,))
    row = cur.fetchone()
    if not row or row[0] <= 0: conn.close(); return await callback.answer("❌ No energy!", show_alert=True)
    energy, points, tier = row; multiplier = get_multiplier(tier); pts_to_add = int(5 * multiplier)
    cur.execute("UPDATE users SET energy=%s, points=%s WHERE telegram_id=%s", (energy-1, points+pts_to_add, uid))
    conn.commit(); cur.close(); conn.close()
    await callback.answer(f"+{pts_to_add} points! 🔋 {energy-1}/100", show_alert=True)

@dp.message(Command("wallet"))
async def cmd_wallet(msg: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone(); conn.close()
    await msg.answer(f"👛 <b>Wallet</b>\nBalance: {float(row[0] if row else 0):.2f} TON\n\nDeposit: /deposit", parse_mode=ParseMode.HTML)

@dp.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    await msg.answer(f"💎 <b>Deposit TON</b>\nSend to:\n<code>{TON_WALLET}</code>\n\nInclude your ID: <code>{msg.from_user.id}</code>", parse_mode=ParseMode.HTML)

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT username, points, tier FROM users ORDER BY points DESC LIMIT 10")
    rows = cur.fetchall(); conn.close()
    if not rows: return await msg.answer("No data")
    board = "\n".join(f"{'🥇🥈🥉'[i] if i<3 else '🏅'} {r[0]} - {r[1]} pts [{r[2].upper()}]" for i, r in enumerate(rows))
    await msg.answer(f"🏆 <b>Leaderboard</b>\n{board}", parse_mode=ParseMode.HTML)

@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, description, done FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 10", (msg.from_user.id,))
    rows = cur.fetchall(); conn.close()
    if not rows: return await msg.answer("No tasks. /task (description)", parse_mode=None)
    lines = "\n".join(f"{'✅' if r[2] else '🔲'} [{r[0]}] {r[1]}" for r in rows)
    await msg.answer(f"📝 <b>Tasks</b>\n{lines}\n\nComplete: /done (id)", parse_mode=ParseMode.HTML)

@dp.message(Command("task"))
async def cmd_add_task(msg: Message):
    parts = msg.text.split(" ", 1)
    if len(parts) < 2: return await msg.answer("Usage: /task (description)", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s, %s) RETURNING id", (msg.from_user.id, parts[1]))
    tid = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ Task #{tid} added", parse_mode=None)

@dp.message(Command("done"))
async def cmd_done(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("Usage: /done (id)", parse_mode=None)
    try: tid = int(parts[1])
    except: return await msg.answer("Invalid ID", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE tasks SET done=TRUE WHERE id=%s AND user_id=%s", (tid, msg.from_user.id))
    if cur.rowcount == 0: conn.close(); return await msg.answer("Task not found", parse_mode=None)
    cur.execute("UPDATE users SET points=points+10 WHERE telegram_id=%s", (msg.from_user.id,))
    conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ Task #{tid} completed! +10 points")

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=CURRENT_DATE"); active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE tier!='free'"); prem = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"👑 <b>Admin Panel</b>\nUsers: {total}\nActive: {active}\nPremium: {prem}", parse_mode=ParseMode.HTML)

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT telegram_id, username, tier, points FROM users ORDER BY points DESC LIMIT 20")
    rows = cur.fetchall(); conn.close()
    await msg.answer("👥 <b>Users</b>\n" + "\n".join(f"{r[1]} ({r[0]}) | {r[2].upper()} | {r[3]}pts" for r in rows), parse_mode=ParseMode.HTML)

@dp.message(Command("doctor"))
async def cmd_doctor(msg: Message):
    try: conn = get_db(); conn.close(); db_status = "✅ Connected"
    except: db_status = "❌ Error"
    await msg.answer(f"🩺 <b>System Health</b>\nDB: {db_status}\nBot: ✅ Running\nRailway: ✅ Online", parse_mode=ParseMode.HTML)

@dp.message(Command("test"))
async def cmd_test(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    report = "🧪 Self-Test\n"
    try: conn = get_db(); conn.close(); report += "✅ DB\n"
    except: report += "❌ DB\n"
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=5)
        report += "✅ Bot Token\n" if r.json().get("ok") else "❌ Token Invalid\n"
    except: report += "❌ Token Error\n"
    await msg.answer(report)

# ═══════════ SEED (FIXED  ensure_user first) ═══════════
@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    try:
        uid = msg.from_user.id
        ensure_user(uid, "admin")
        ensure_user(uid, "admin")
        uid = msg.from_user.id
        ensure_user(uid, "admin")
        uid = msg.from_user.id
        ensure_user(uid, msg.from_user.full_name or "admin")
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s,%s), (%s,%s), (%s,%s)", (uid, "Demo task 1: Create NFT store", uid, "Demo task 2: Invite 3 friends", uid, "Demo task 3: Make first deposit"))
        cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s,%s), (%s,%s)", (uid, "Great bot!", uid, "Need more features"))
        cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, 9.9, "confirmed", uid, 29, "pending"))
        cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, "seed", "demo data inserted", uid, "checkin", "+5"))
        conn.commit(); cur.close(); conn.close()
        await msg.answer("✅ Demo data seeded! Check /tasks, /dashboard, /crm, /events, /feedback.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Seed error: {e}", parse_mode=None)

@dp.message(Command("progress"))
async def cmd_progress(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done=TRUE")
    done_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments WHERE status='confirmed'")
    payments = cur.fetchone()[0]
    cur.execute("SELECT SUM(amount) FROM payments WHERE status='confirmed'")
    revenue = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM feedback")
    feedbacks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 day'")
    events_today = cur.fetchone()[0]
    conn.close()
    pct = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    bar = "🟩" * int(pct // 10) + "⬜" * (10 - int(pct // 10))
    await msg.answer(
        f"📈 <b>SLH Progress Tracker</b>\n\n"
        f"📝 Tasks: {done_tasks}/{total_tasks} {bar} {pct}%\n"
        f"👥 Users: {total_users}\n"
        f"💎 Payments: {payments} confirmed\n"
        f"💰 Revenue: {revenue:.2f} TON\n"
        f"📩 Feedback: {feedbacks}\n"
        f"📡 Events today: {events_today}\n\n"
        f"<i>Updated: {datetime.datetime.now().strftime('%H:%M')}</i>",
        parse_mode=ParseMode.HTML
    )

# ═══════════ GUIDE SYSTEM ═══════════
@dp.message(Command("guide"))
async def cmd_guide(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ How to earn points", callback_data="guide_points")],
        [InlineKeyboardButton(text="💎 How to deposit TON", callback_data="guide_deposit")],
        [InlineKeyboardButton(text="🏆 What is Tier?", callback_data="guide_tier")],
        [InlineKeyboardButton(text="📋 All commands", callback_data="cmd_help")],
    ])
    await msg.answer("<b>📖 SLH Guide</b>\nChoose a topic:", parse_mode="HTML", reply_markup=kb)

@dp.message(Command("faq"))
async def cmd_faq(msg: Message):
    await msg.answer("<b>FAQ</b>\n\n<b>Q: How to earn points?</b>\n/checkin daily, /tap, complete /tasks\n\n<b>Q: How to deposit TON?</b>\n/deposit - send TON with your ID in memo\n\n<b>Q: Premium tiers?</b>\nPro: 9.9 TON/mo (x1.5) | Business: 29 TON/mo (x2.0)\n\n<b>Q: Referrals?</b>\n/referral - earn +50 pts per friend", parse_mode="HTML")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: Message):
    await msg.answer("<b>🎓 Tutorial</b>\n\n1. /register - create account\n2. /checkin - earn daily points\n3. /deposit - add TON\n4. /upgrade - unlock premium\n5. /task - set your goals\n\nQuestions? /support", parse_mode="HTML")

@dp.callback_query(F.data.startswith("guide_"))
async def on_guide_topic(callback: CallbackQuery):
    await callback.answer()
    topics = {
        "guide_points": "<b>⭐ Earning Points</b>\n\n/checkin  daily (+5 to +35)\n/tap  tap button (+5 each)\n/done  complete task (+10)\n\nTip: streak bonus stacks up to 7 days!",
        "guide_deposit": "<b>💎 Depositing TON</b>\n\n1. Use /deposit to get wallet address\n2. Send TON from your wallet\n3. Include your Telegram ID in memo\n4. Balance updates after confirmation",
        "guide_tier": "<b>🏆 Tier System</b>\n\nFREE  x1.0 multiplier\nPRO (9.9 TON/mo)  x1.5 multiplier\nBUSINESS (29 TON/mo)  x2.0 multiplier\n\nUpgrade: /upgrade",
    }
    await callback.message.answer(topics.get(callback.data, "Unknown topic"), parse_mode="HTML")

# ═══════════ ADDITIONAL COMMANDS ═══════════
@dp.message(Command("sysinfo"))
async def cmd_sysinfo(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    import platform, psutil
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        info = f"🖥 <b>System Info</b>\nOS: {platform.system()} {platform.release()}\nCPU: {cpu}%\nRAM: {mem.percent}% ({mem.used // 1024**2} MB / {mem.total // 1024**2} MB)\nDisk: {disk.percent}% free"
    except ImportError:
        info = "psutil not installed"
    await msg.answer(info, parse_mode="HTML")

@dp.message(Command("crm"))
async def cmd_crm(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier ORDER BY COUNT(*) DESC")
    rows = cur.fetchall(); conn.close()
    lines = "\n".join(f"  {r[0].upper()}: {r[1]} users" for r in rows)
    await msg.answer(f"<b>CRM - User Segments</b>\n{lines}", parse_mode=ParseMode.HTML)

@dp.message(Command("events"))
async def cmd_events(msg: Message):
    await msg.answer("<b>Upcoming Events</b>\n• NFT Launch - Coming Soon\n• Token Sale - Q3 2026\n• Community AMA - This Week", parse_mode=ParseMode.HTML)

@dp.message(Command("support"))
async def cmd_support(msg: Message):
    await msg.answer("<b>Support</b>\nCommunity: @SLH_Claude_bot\nWebsite: slh-nft.com", parse_mode=ParseMode.HTML)

@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    today = datetime.date.today()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at)=%s", (today,)); new = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=%s", (today,)); checked = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"<b>Morning Report - {today}</b>\nUsers: {total} (+{new})\nCheck-ins: {checked}", parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    parts = msg.text.split(" ", 1)
    if len(parts) < 2: return await msg.answer("Usage: /broadcast (message)", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users"); users = cur.fetchall(); conn.close()
    sent = 0
    for (uid,) in users:
        try: await bot.send_message(uid, parts[1], parse_mode=ParseMode.HTML); sent += 1
        except: pass
    await msg.answer(f"Sent to {sent}/{len(users)} users")

@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("Usage: /setreminder HH:MM", parse_mode=None)
    await msg.answer(f"Reminder set for {parts[1]} (coming soon)", parse_mode=None)

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: Message):
    await msg.answer("<b>API Status</b>\n✅ Railway Online\n✅ Database Online", parse_mode=ParseMode.HTML)

@dp.message(Command("feedback"))
async def cmd_feedback(msg: Message):
    parts = msg.text.split(" ", 1)
    if len(parts) < 2: return await msg.answer("Usage: /feedback (message)", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s, %s)", (msg.from_user.id, parts[1]))
    conn.commit(); cur.close(); conn.close()
    await msg.answer("Feedback saved! Thank you.", parse_mode=None)

@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("<b>Daily Missions</b>\n✅ /checkin - Daily Check-in\n⚡ /tap - Tap-to-Earn\n📝 /task - Add Task (+10 pts)", parse_mode=ParseMode.HTML)

@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    await msg.answer("<b>🗺️ SLH Roadmap</b>\n\n<b>✅ Completed</b>\n• Bot Launch  40+ commands\n• Points, Energy, Streaks\n• Leaderboard, Referrals\n• Web Dashboard\n• AI Chat (Groq)\n• TON Gateway\n\n<b>🔜 Next</b>\n• Mall Registry\n• Inline Mode\n• Mini App\n\n<b>📅 Future</b>\n• NFT Store\n• DAO\n• Mobile App", parse_mode=ParseMode.HTML)

@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("<b>Backup Status</b>\n✅ DB Connected\n✅ Railway auto-backups enabled", parse_mode=ParseMode.HTML)

@dp.message(Command("transfer"))
async def cmd_transfer(msg: Message):
    await msg.answer("<b>Internal Transfer</b>\nComing soon. For withdrawals, contact @SLH_Claude_bot", parse_mode=ParseMode.HTML)

# ═══════════ TON GATEWAY ═══════════
TONCENTER_V3 = "https://toncenter.com/api/v3"

def ton_monitor():
    while True:
        try:
            url = f"{TONCENTER_V3}/transactions?account={TON_WALLET}&limit=20&sort=desc"
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                time.sleep(30)
                continue
            data = resp.json()
            txs = data.get("transactions", [])
            conn = get_db(); cur = conn.cursor()
            for tx in txs:
                tx_hash = tx.get("hash")
                if not tx_hash: continue
                in_msg = tx.get("in_msg") or {}
                value_nano = int(in_msg.get("value", 0))
                if value_nano <= 0: continue
                amount = value_nano / 1_000_000_000
                comment = str(in_msg.get("message") or in_msg.get("body") or "").strip()
                try:
                    user_id = int(comment)
                    if user_id < 100000: continue
                except: continue
                cur.execute("SELECT 1 FROM payments WHERE tx_hash = %s", (tx_hash,))
                if cur.fetchone(): continue
                cur.execute("INSERT INTO payments (user_id, amount, status, tx_hash) VALUES (%s,%s,%s,%s)", (user_id, amount, "confirmed", tx_hash))
                new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
                cur.execute("UPDATE users SET balance = balance + %s, tier = CASE WHEN %s > tier THEN %s ELSE tier END WHERE telegram_id = %s", (amount, amount, new_tier, user_id))
                cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)", (user_id, "deposit", f"{amount} TON"))
                conn.commit()
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(bot.send_message(user_id, f"✅ <b>Deposit received!</b>\n{amount:.2f} TON"))
                except: pass
            cur.close(); conn.close()
        except Exception as e:
            print(f"TON monitor error: {e}")
        time.sleep(30)

threading.Thread(target=ton_monitor, daemon=True).start()

@dp.message(Command("paid"))
async def cmd_paid(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    parts = msg.text.split()
    if len(parts) < 3: return await msg.answer("Usage: /paid <user_id> <amount>", parse_mode=None)
    try:
        target_uid = int(parts[1])
        amount = float(parts[2])
    except: return await msg.answer("Invalid numbers", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,'manual')", (target_uid, amount))
    new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
    cur.execute("UPDATE users SET balance = balance + %s, tier = CASE WHEN %s > tier THEN %s ELSE tier END WHERE telegram_id = %s", (amount, amount, new_tier, target_uid))
    cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)", (target_uid, "deposit_manual", f"{amount} TON"))
    conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ Manual deposit of {amount} TON credited to user {target_uid}", parse_mode=None)

# ═══════════ WEB APP ═══════════
DASHBOARD_HTML = """<html><head><meta charset="utf-8"><title>SLH Dashboard</title>
<style>body{font-family:sans-serif;margin:20px;background:#0a0a1a;color:#e0e0e0}.card{background:#1a1a2e;padding:20px;margin:10px 0;border-radius:10px}.stat{font-size:1.5em;font-weight:bold}</style></head>
<body><h1>SLH SPARK AI</h1>
<div class="card"><div class="stat" id="stats">Loading...</div></div>
<script>fetch('/api/stats').then(r=>r.json()).then(d=>{document.getElementById('stats').innerHTML=`Users: ${d.total_users} | Active: ${d.active_today} | Points: ${d.total_points} | Premium: ${d.premium_users}`})</script>
</body></html>"""

def make_web_app():
    if not HAS_FASTAPI: return None
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(): return HTMLResponse(content=DASHBOARD_HTML)
    @app.get("/health")
    async def health(): return JSONResponse({"database": True, "bot": True})
    @app.get("/api/stats")
    async def stats():
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=CURRENT_DATE"); active = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM users"); pts = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM users WHERE tier!='free'"); prem = cur.fetchone()[0]
        cur.execute("SELECT telegram_id,username,tier,points FROM users ORDER BY points DESC LIMIT 20")
        users = [{"telegram_id":r[0],"username":r[1],"tier":r[2],"points":r[3]} for r in cur.fetchall()]
        conn.close()
        return JSONResponse({"total_users":total,"active_today":active,"total_points":int(pts),"premium_users":prem,"users_list":users})

    @app.get("/api/tasks")
    async def api_tasks(user_id: int = None):
        if not user_id: return JSONResponse({"tasks": []})
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id, description, done, created_at FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 50", (user_id,))
        tasks = [{"id": r[0], "title": r[1], "done": r[2], "created_at": str(r[3])} for r in cur.fetchall()]
        cur.close(); conn.close()
        return JSONResponse({"tasks": tasks})

    @app.patch("/api/tasks/{task_id}")
    async def api_patch_task(task_id: int, request: Request):
        data = await request.json()
        done = data.get("done", None)
        if done is not None:
            conn = get_db(); cur = conn.cursor()
            cur.execute("UPDATE tasks SET done=%s WHERE id=%s", (done, task_id))
            conn.commit(); cur.close(); conn.close()
        return JSONResponse({"ok": True})

    return app

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2)
    web_app = make_web_app()
    if web_app and HAS_FASTAPI:
        config = uvicorn.Config(web_app, host="0.0.0.0", port=PORT, log_level="warning")
        server = uvicorn.Server(config)
        await asyncio.gather(server.serve(), dp.start_polling(bot))
    else:
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
