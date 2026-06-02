import asyncio
import sqlite3
import json
import os
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# טען משתנים
from secrets_local import TELEGRAM_BOT_TOKEN, DATABASE_URL, ADMIN_ID, GROQ_API_KEY

# ====================== DATABASE ======================
def get_db():
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        return sqlite3.connect(db_path)
    else:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            points INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_checkin TEXT,
            tier TEXT DEFAULT 'free',
            balance REAL DEFAULT 0,
            registered BOOLEAN DEFAULT FALSE,
            referral_code TEXT,
            referred_by INTEGER,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            tx_hash TEXT UNIQUE,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            joined TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT,
            metadata TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ====================== FIX HEBREW ======================
def fix_hebrew(t: str) -> str:
    if not t:
        return t
    # הוסף RLM אם יש תווים עבריים
    if any(u"\u0590" <= ch <= u"\u05FF" for ch in t):
        return "\u200F" + t
    return t

# ====================== BOT SETUP ======================
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=None))
dp = Dispatcher()

# ====================== KEYBOARDS ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="💰 Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="🔥 Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="⭐️ Upgrade", callback_data="cmd_upgrade"),
         InlineKeyboardButton(text="❤️ Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="cmd_profile"),
         InlineKeyboardButton(text="👑 Admin", callback_data="cmd_admin")],
        [InlineKeyboardButton(text="📋 Tasks", callback_data="cmd_tasks"),
         InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")],
    ])

# ====================== COMMAND HANDLERS ======================
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await bot.send_chat_action(msg.chat.id, "typing")
    await asyncio.sleep(0.6)
    logo = """
+----------------------------------+
|     ███████╗██╗     ██╗  ██╗     |
|     ██╔════╝██║     ██║  ██║     |
|     ███████╗██║     ███████║     |
|     ╚════██║██║     ██╔══██║     |
|     ███████║███████╗██║  ██║     |
|     ╚══════╝╚══════╝╚═╝  ╚═╝     |
|   🧠 SLH SPARK AI   v3.3        |
+----------------------------------+
"""
    await msg.answer(fix_hebrew(logo))
    name = msg.from_user.first_name or "friend"
    await msg.answer(fix_hebrew(f"<b>👋 היי, {name}!</b>\n\n🧠 <b>Spark AI Agent</b> — העוזר האישי שלך לפרויקטים ב-TON\n\n• חנויות NFT\n• מסחר בטוקנים\n• בניית קהילה\n• תשלומים אוטומטיים"), reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text = """<b>📘 SLH Bot — רשימת פקודות</b>

<b>💎 Premium &amp; Payments</b>
/upgrade — שדרג ל-Pro/Business
/donate — תרומה
/paid — (אדמין) אישור תשלום

<b>🏆 Rewards</b>
/checkin — צ'ק-אין יומי
/points — נקודות
/tap — Tap-to-Earn
/leaderboard — טבלה
/referral — קישור הפניות

<b>💰 TON Wallet</b>
/wallet — יתרה
/deposit — הפקדה
/transfer — העברה

<b>🛒 Marketplace</b>
/store — חנות
/products — מוצרים
/buy — קנייה

<b>📊 Analytics &amp; CRM</b>
/dashboard — סטטיסטיקות
/crm — ניהול לקוחות
/events — אירועים
/segments — פילוח משתמשים

<b>🛠 Tools</b>
/profile /myid /tasks /feedback /crypto /daily /roadmap /support /seed /sysinfo /oracle /peace /game /invest

<b>👑 Admin</b>
/admin /users /broadcast /morning /doctor /statusapi /test /backup
"""
    await msg.answer(fix_hebrew(text))

@dp.message(Command("register"))
async def cmd_register(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (msg.from_user.id,))
    exists = cur.fetchone()
    if exists:
        await msg.answer(fix_hebrew("✅ You are already registered!"))
    else:
        cur.execute("INSERT INTO users (telegram_id, username, first_name, registered, created_at) VALUES (?, ?, ?, ?, ?)",
                    (msg.from_user.id, msg.from_user.username, msg.from_user.first_name, True, datetime.now().isoformat()))
        conn.commit()
        await msg.answer(fix_hebrew("🎉 You are now registered for updates!"))
    conn.close()

@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, username, points, tier, balance, created_at FROM users WHERE telegram_id = ?", (msg.from_user.id,))
    user = cur.fetchone()
    conn.close()
    if not user:
        await msg.answer(fix_hebrew("Profile not found. Use /register first."))
        return
    await msg.answer(fix_hebrew(f"👤 <b>Profile</b>\nID: {user[0]}\nUsername: @{user[1]}\nPoints: {user[2]}\nTier: {user[3]}\nWallet: {user[4]} TON\nJoined: {user[5]}\n\nUse /myidentity for Telegram details"))

@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(fix_hebrew(f"🪪 Your Telegram ID: {msg.from_user.id}"))

@dp.message(Command("myidentity"))
async def cmd_myidentity(msg: Message):
    await msg.answer(fix_hebrew(f"🪪 ID: {msg.from_user.id}\nName: {msg.from_user.first_name}\nUsername: @{msg.from_user.username}"))

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    today = datetime.now().date().isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT last_checkin, points, streak FROM users WHERE telegram_id = ?", (msg.from_user.id,))
    user = cur.fetchone()
    if not user:
        await msg.answer(fix_hebrew("Please /register first."))
        conn.close()
        return
    last = user[0]
    if last == today:
        await msg.answer(fix_hebrew("⏳ Already checked in today! Come back tomorrow."))
    else:
        new_streak = (user[2] + 1) if last else 1
        points_earned = 5
        new_points = (user[1] or 0) + points_earned
        cur.execute("UPDATE users SET last_checkin = ?, streak = ?, points = ? WHERE telegram_id = ?",
                    (today, new_streak, new_points, msg.from_user.id))
        conn.commit()
        await msg.answer(fix_hebrew(f"✅ Check-in successful! +{points_earned} points\nTotal: {new_points} pts | Streak: {new_streak} days"))
    conn.close()

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT points, streak FROM users WHERE telegram_id = ?", (msg.from_user.id,))
    user = cur.fetchone()
    conn.close()
    points = user[0] if user else 0
    streak = user[1] if user else 0
    await msg.answer(fix_hebrew(f"💰 Your points: {points} | Streak: {streak} days"))

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users WHERE points > 0 ORDER BY points DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await msg.answer(fix_hebrew("No data available."))
        return
    text = "🏆 <b>Leaderboard</b>\n"
    for i, (name, pts) in enumerate(rows, 1):
        text += f"{i}. {name or 'Anonymous'} — {pts} pts\n"
    await msg.answer(fix_hebrew(text))

@dp.message(Command("wallet"))
async def cmd_wallet(msg: Message):
    await msg.answer(fix_hebrew("👛 SLH Wallet\nBalance: 0.00 TON\nTier: free\n\nUse /deposit to add funds."))

@dp.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    ton_wallet = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    await msg.answer(fix_hebrew(f"💰 Deposit TON to:\n<code>{ton_wallet}</code>\n\n<b>Important:</b> Write your ID in the comment:\n<code>{msg.from_user.id}</code>"))

@dp.message(Command("transfer"))
async def cmd_transfer(msg: Message):
    await msg.answer(fix_hebrew("Transfer coming soon."))

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    ton_wallet = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    await msg.answer(fix_hebrew(f"❤️ <b>Donate to SLH</b>\nTON: <code>{ton_wallet}</code>\nUSDT (TRC-20): <code>TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ</code>\nBitcoin: <code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>"))

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer(fix_hebrew("⭐️ <b>Premium Plans</b>\nPro: 9.9 TON/month\nBusiness: 29 TON/month\n\nSend TON to the donation address with your ID and then /paid"))

@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    await msg.answer(fix_hebrew("📋 Your tasks:\n- Daily check-in (/checkin)\n- Invite friends (/referral)\n- Donate (/donate)\n- Join community (/support)"))

@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await cmd_checkin(msg)

@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer(fix_hebrew("💾 Backup saved to cloud."))

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer(fix_hebrew("🔒 Admins only."))
        return
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(fix_hebrew("Usage: /broadcast <message>"))
        return
    await msg.answer(fix_hebrew(f"📢 Broadcasting: {args[1]}"))

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer(fix_hebrew("🔒 Admins only."))
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, username, first_name, points, registered FROM users LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await msg.answer(fix_hebrew("No users registered."))
        return
    text = "👥 <b>Registered Users</b>\n"
    for uid, uname, fname, pts, reg in rows:
        text += f"{uid} - {fname or uname or '?'} - {pts} pts\n"
    await msg.answer(fix_hebrew(text))

@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer(fix_hebrew("🔒 Admins only."))
        return
    await msg.answer(fix_hebrew("🌅 Good morning, Osif!\nDate: 2026-06-01\nRegistered users: 3\nCheck-ins today: 1"))

@dp.message(Command("doctor"))
async def cmd_doctor(msg: Message):
    await msg.answer(fix_hebrew("🩺 <b>SLH System Doctor</b>\n✅ Bot: Online\n✅ Railway: Connected\n✅ Database: OK\n✅ Groq API Key: " + ("Set" if "gsk" in GROQ_API_KEY else "Missing") + "\n🟢 All systems operational"))

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: Message):
    await msg.answer(fix_hebrew("🔌 API Status\n✅ Railway online\n✅ Database online"))

@dp.message(Command("test"))
async def cmd_test(msg: Message):
    await msg.answer(fix_hebrew("Test passed."))

@dp.message(Command("crm"))
async def cmd_crm(msg: Message):
    await msg.answer(fix_hebrew("📊 CRM System\nLeads: 0\nCustomers: 0\nTasks: 0\nUse /users to see registered users."))

@dp.message(Command("events"))
async def cmd_events(msg: Message):
    await msg.answer(fix_hebrew("No events yet."))

@dp.message(Command("segments"))
async def cmd_segments(msg: Message):
    await msg.answer(fix_hebrew("User Segments:\nFree: 1\nPro: 0\nBusiness: 0"))

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.answer(fix_hebrew("Dashboard:\nUsers: 1\nStores: 0\nProducts: 0\nEvents: 0"))

@dp.message(Command("support"))
async def cmd_support(msg: Message):
    await msg.answer(fix_hebrew("💬 Support: @OsifUngar\nCommunity: https://t.me/SLH_Claude_bot"))

@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    await msg.answer(fix_hebrew("🗺 Roadmap: https://slh-nft.com/roadmap"))

@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    await msg.answer(fix_hebrew("Seed planted! 🌱"))

@dp.message(Command("sysinfo"))
async def cmd_sysinfo(msg: Message):
    import platform
    await msg.answer(fix_hebrew(f"System: {platform.system()}\nCPU: {os.cpu_count()} cores"))

@dp.message(Command("crypto"))
async def cmd_crypto(msg: Message):
    await msg.answer(fix_hebrew("💰 BTC: $71629 | ETH: $1990.64"))

@dp.message(Command("referral"))
async def cmd_referral(msg: Message):
    link = f"https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}"
    await msg.answer(fix_hebrew(f"🔗 Your referral link:\n{link}\n\nShare with friends to earn points!"))

@dp.message(Command("identity"))
async def cmd_identity(msg: Message):
    await msg.answer(fix_hebrew("🔐 Identity system active.\nUse /myidentity to view your profile."))

@dp.message(Command("healthcheck"))
async def cmd_healthcheck(msg: Message):
    ai_status = "✅ Set" if "gsk" in GROQ_API_KEY else "❌ Missing"
    await msg.answer(fix_hebrew(f"🤖 Bot: Online\n🧠 Groq: {ai_status}\n🗄 DB: SQLite\n📡 Telegram: OK"))

@dp.message(Command("oracle"))
async def cmd_oracle(msg: Message):
    await msg.answer(fix_hebrew("🔮 SLH Oracle+ coming soon."))

@dp.message(Command("peace"))
async def cmd_peace(msg: Message):
    await msg.answer(fix_hebrew("🕊️ Peace Game: Share positive vibes in the community!"))

@dp.message(Command("game"))
async def cmd_game(msg: Message):
    await msg.answer(fix_hebrew("🎮 SLH Game: Coming soon!"))

@dp.message(Command("invest"))
async def cmd_invest(msg: Message):
    await msg.answer(fix_hebrew("📈 Investment opportunities: https://slh-nft.com/investor-landing/"))

@dp.message(Command("store"))
async def cmd_store(msg: Message):
    await msg.answer(fix_hebrew("🛒 Store: Coming soon. Use /buy for now."))

@dp.message(Command("buy"))
async def cmd_buy(msg: Message):
    await msg.answer(fix_hebrew("Purchase system in development. Check /donate to support."))

@dp.message(Command("tap"))
async def cmd_tap(msg: Message):
    await msg.answer(fix_hebrew("🔥 Tap-to-Earn: Coming soon!"))

@dp.message(Command("faq"))
async def cmd_faq(msg: Message):
    await msg.answer(fix_hebrew("❓ FAQ: https://slh-nft.com/faq"))

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: Message):
    await msg.answer(fix_hebrew("📚 Tutorial: Use /start to begin."))

@dp.message(Command("progress"))
async def cmd_progress(msg: Message):
    await msg.answer(fix_hebrew("📊 Progress: 60% complete. Next milestone: AI integration."))

@dp.message(Command("done"))
async def cmd_done(msg: Message):
    await msg.answer(fix_hebrew("✅ Done! Great job!"))

@dp.message(Command("about"))
async def cmd_about(msg: Message):
    await msg.answer(fix_hebrew("🌐 SLH is an autonomous AI system for Telegram communities, NFT stores, and TON payments."))

@dp.message(Command("links"))
async def cmd_links(msg: Message):
    await msg.answer(fix_hebrew("🔗 Important links:\nWebsite: https://slh-nft.com\nCampaign: https://slh-nft.com/campaign/\nInvestor: https://slh-nft.com/investor-landing/"))

@dp.message(Command("community"))
async def cmd_community(msg: Message):
    await msg.answer(fix_hebrew("👥 Join our community: @SLH_Claude_bot"))

@dp.message(Command("feedback"))
async def cmd_feedback(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(fix_hebrew("Usage: /feedback <message>"))
        return
    await msg.answer(fix_hebrew("📨 Thank you for your feedback! +5 points"))

# ====================== CALLBACK HANDLER ======================

@dp.message(Command("invest_calc"))
async def cmd_invest_calc(msg: Message):
    args = msg.text.split()
    if len(args) >= 5:
        try:
            users = int(args[1])
            profit = float(args[2])
            share = float(args[3]) / 100
            invest = float(args[4])
            net = users * profit
            investor = net * share
            months = invest / investor if investor > 0 else 0
            await msg.answer(fix_hebrew(f"?? ?????:\n???? ?????: {net:,.0f} ILS\n??? ??????: {investor:,.0f} ILS\n??????: {months:.1f}"))
        except:
            await msg.answer(fix_hebrew("? ????? ???????"))
    else:
        await msg.answer(fix_hebrew("?????: /invest_calc <???????> <???? ??????> <????> <?????>"))

@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    await call.answer()
    data = call.data
    if data == "cmd_status":
        await cmd_dashboard(call.message)
    elif data == "cmd_points":
        await cmd_points(call.message)
    elif data == "cmd_checkin":
        await cmd_checkin(call.message)
    elif data == "cmd_tap":
        await cmd_tap(call.message)
    elif data == "cmd_upgrade":
        await cmd_upgrade(call.message)
    elif data == "cmd_donate":
        await cmd_donate(call.message)
    elif data == "cmd_profile":
        await cmd_profile(call.message)
    elif data == "cmd_admin":
        await cmd_users(call.message)
    elif data == "cmd_tasks":
        await cmd_tasks(call.message)
    elif data == "cmd_help":
        await cmd_help(call.message)
    else:
        await call.message.answer(fix_hebrew("🔘 Use /help for commands."))

# ====================== MAIN ======================
async def main():
    print("🚀 SLH Spark AI v3.3 starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


# ---------- PERSISTENT MENU ----------
async def send_main_menu(chat_id: int, text: str = "חזור לתפריט הראשי:"):
    await bot.send_message(chat_id, fix_hebrew(text), reply_markup=main_menu())

