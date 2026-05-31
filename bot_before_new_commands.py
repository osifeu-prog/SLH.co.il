import time
import aiohttp
import asyncio, os, json, datetime, requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from ux.responses import msg_welcome, msg_help, msg_checkin_success, msg_checkin_already, msg_points, msg_leaderboard, msg_status, msg_daily, msg_referral, msg_donate, msg_register_success, msg_register_already, msg_feedback_success, msg_roadmap, msg_error_generic
from ux.keyboards import kb_main_menu, kb_after_checkin, kb_after_points, kb_donate, kb_status, kb_leaderboard, kb_daily, kb_help, kb_referral, kb_roadmap, kb_back_to_menu, kb_admin_panel

from services.wallet import get_balance, add_balance, transfer
from services.ledger import log_transaction
from services.event import emit_event
from services.store import create_store, get_store
from services.product import add_product, list_products
from services.order import create_order
from services.db import init_db, get_db

load_dotenv()
init_db()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
dp = Dispatcher()

# ---- DB ----
CONTACTS_FILE = "contacts.json"
POINTS_FILE = "points.json"

def load_db(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x.strip()]

# ---- ASCII Logo ----
SLH_LOGO = r"""
   SLH - AUTONOMOUS SYSTEM
   crowdfunding & AI assistant
"""

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    name = msg.from_user.first_name or msg.from_user.username or "friend"
    welcome_text = (
        "╔══════════════════════════════════╗\n"
        "║   ███████╗██╗     ██╗  ██╗      ║\n"
        "║   ██╔════╝██║     ██║  ██║      ║\n"
        "║   ███████╗██║     ███████║      ║\n"
        "║   ╚════██║██║     ██╔══██║      ║\n"
        "║   ███████║███████╗██║  ██║      ║\n"
        "║   ╚══════╝╚══════╝╚═╝  ╚═╝      ║\n"
        "║                                  ║\n"
        "║  AI PROJECT CREATION SYSTEM v2  ║\n"
        "║  ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆      ║\n"
        "╚══════════════════════════════════╝\n"
        "\n"
        f"👋 שלום, {name}!\n"
        "\n"
        "🤖 מה אני?\n"
        "SLH הוא מערכת AI ליצירה וניהול פרויקטים דיגיטליים\n"
        "מחנויות NFT ועד מסחר בטוקנים — הכל במקום אחד.\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ יכולות המערכת\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "01 · AI Chat       Claude, Gemini, Groq\n"
        "02 · Marketplace   חנויות, מוצרים, NFT\n"
        "03 · Rewards       נקודות, הפניות, TON\n"
        "04 · Support       ניטור, כרטיסים, סשנים\n"
        "05 · CRM           משתמשים, tier, analytics\n"
        "06 · Quiz & XP     קריפטו, leaderboard\n"
        "07 · TON Wallet    תשלומים, תמלוגים\n"
        "08 · Infra         DB, Redis, FastAPI\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 התחל עכשיו\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/register   → הצטרף למערכת\n"
        "/dashboard  → סטטיסטיקות\n"
        "/upgrade    → Premium plans\n"
        "/help       → כל הפקודות\n"
        "\n"
        "slh-nft.com · @SLH_Claude_bot"
    )
    kb = kb_main_menu()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [[InlineKeyboardButton(**btn) for btn in row] for row in kb]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(welcome_text, parse_mode=None, reply_markup=markup)
@dp.message(Command("commands"))
async def cmd_commands(msg: Message):
    text = (
        "Full Command Reference:\n\n"
        "/start - Main menu\n"
        "/register - Subscribe to updates\n"
        "/donate - Donation info & TON address\n"
        "/status - System status\n"
        "/checkin - Daily check-in (+5 pts, streak)\n"
        "/leaderboard - Top 5 users\n"
        "/points - Your points\n"
        "/daily - Daily missions\n"
        "/backup - Save data to cloud\n"
        "/broadcast <msg> - (Admin) Send message to all subscribers\n"
        "/users - (Admin) List all registered users\n"
        "/myid - Show your Telegram ID\n"
        "/help - Quick command list\n"
        "/commands - This full reference\n"
        "/referral - Your personal referral link\n"
        "/stats - Campaign statistics\n"
        "/roadmap - SLH Roadmap\n"
        "/support - Join our community\n"
        "/feedback <msg> - Send feedback\n"
        "/tasks - Your weekend tasks\n"
        "/morning - Daily report (Admin)\n"
        "Any other text -> AI chat (Groq)"
    )
    await msg.answer(text, parse_mode=None)

# ---- /register ----
@dp.message(Command("register"))
async def cmd_register(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.username or "unknown"
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (telegram_id, username, tier) VALUES (%s,%s,'free') ON CONFLICT (telegram_id) DO UPDATE SET username=%s, last_seen=NOW()",
            (user_id, username, username)
        )
        conn.commit()
        await msg.answer("You are now registered for updates!", parse_mode=None)
    except Exception as e:
        conn.rollback()
        await msg.answer(f"Registration error: {str(e)[:100]}", parse_mode=None)
    finally:
        conn.close()
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "Donate to the campaign:\n\n"
        "Send TON to:\n"
        "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp\n\n"
        "Support Levels:\n"
        "Supporter () - Name on website\n"
        "Builder () - Early access + badge\n"
        "Founder () - Vote on features\n"
        "Visionary () - Personal call + Founder status",
        parse_mode=None
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status_enhanced(msg: Message):
    text = (
        "Project Status:\n"
        "Bot: Online\n"
        "Crowdfunding: Active\n"
        "Mini App: slh-nft.com\n\n"
        "Next steps:\n"
        "1. /upgrade — monetize\n"
        "2. /store create — open shop\n"
        "3. /broadcast — promote\n"
        "4. /dashboard — track growth"
    )
    await msg.answer(text, parse_mode=None)
# ---- /upgrade ----
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer(
        "Premium Plans:\n\n"
        "⭐ Pro — $9.99/month\n"
        "  • AI priority access\n"
        "  • Create unlimited stores\n"
        "  • Advanced analytics\n\n"
        "💼 Business — $29.99/month\n"
        "  • All Pro features\n"
        "  • Custom branding\n"
        "  • Priority support\n\n"
        "To upgrade, send TON to:\n"
        f"{os.getenv('TON_WALLET', 'UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp')}\n\n"
        "Contact admin after payment.",
        parse_mode=None
    )

# ---- /commission (admin) ----
@dp.message(Command("commission"))
async def cmd_commission(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    await msg.answer("Commission rate: 5% per marketplace transaction.\nSet via /set_commission <rate>", parse_mode=None)

# ---- Main ----

@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        await msg.answer("AI not configured.")
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are SLH AI assistant. Rules: 1) Never summarize 2) Give ONE decision 3) Max 4 lines 4) End with next action 5) Hebrew first."},
                    {"role": "user", "content": msg.text}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}")



@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("?? Admin only")
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked_today = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 day'")
    events_today = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='purchase' AND type='debit' AND created_at > NOW() - INTERVAL '1 day'")
    revenue_today = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM wallet_balances WHERE balance > 0")
    active_wallets = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stores")
    stores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM products")
    products = cur.fetchone()[0]
    conn.close()
    text = (
        f"?? *SLH Admin Panel*
?????????????????????

"
        f"?? *Users*: {total_users} total, {checked_today} checked in today
"
        f"?? *Activity*: {events_today} events today
"
        f"?? *Revenue (24h)*: ${revenue_today:.2f}
"
        f"?? *Active wallets*: {active_wallets}
"
        f"?? *Marketplace*: {stores} stores, {products} products

"
        f"?? *Quick actions:*
"
        f"/users  list all users
"
        f"/broadcast  send message
"
        f"/doctor  full health check
"
        f"/dashboard  stats
"
    )
    # Create inline buttons for admin actions
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="?? Users", callback_data="admin_users"),
         InlineKeyboardButton(text="?? Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="?? Dashboard", callback_data="cmd_dashboard"),
         InlineKeyboardButton(text="?? Doctor", callback_data="cmd_doctor")]
    ])
    await msg.answer(text, parse_mode="MarkdownV2", reply_markup=keyboard)



@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    await callback.answer()
    await cmd_users(callback.message)

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Send /broadcast <message>")



@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stores")
    total_stores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events")
    total_events = cur.fetchone()[0]
    conn.close()
    text = f"?? *SLH Dashboard*
?????????????????????

?? Users: {total_users}
?? Stores: {total_stores}
?? Products: {total_products}
?? Events: {total_events}"
    await msg.answer(text, parse_mode="MarkdownV2")



# ======================= /statusapi (health indicator) =======================
@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("🔒 Admin only")
        return
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1")
        db_ok = "✅"
    except:
        db_ok = "❌"
    conn.close()
    redis_ok = "✅" if os.getenv("REDIS_URL") else "⚪"
    ai_ok = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    text = f"🩺 *API & System Health*\n━━━━━━━━━━━━━━━━━━━━━\n\nDatabase: {db_ok}\nRedis: {redis_ok}\nAI (Groq): {ai_ok}\nBot online: ✅"
    await msg.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

# ======================= /setreminder (set daily reminder time) =======================
@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("🔒 Admin only")
        return
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Usage: /setreminder <HH:MM> (UTC)\nExample: /setreminder 14:00")
        return
    time_str = parts[1]
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS bot_config (key TEXT PRIMARY KEY, value TEXT)")
        cur.execute("INSERT INTO bot_config (key, value) VALUES ('reminder_time', %s) ON CONFLICT (key) DO UPDATE SET value = %s", (time_str, time_str))
        conn.commit()
        conn.close()
        await msg.answer(f"✅ Daily reminder set to {time_str} UTC. I will send report every day at that time.")
    except:
        await msg.answer("❌ Invalid time format. Use HH:MM (24h).")

# ======================= Daily reminder sender (to be called by cron) =======================
async def send_daily_reminder():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_config WHERE key='reminder_time'")
    row = cur.fetchone()
    reminder_time = row[0] if row else "14:00"
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='purchase' AND type='debit' AND created_at > NOW() - INTERVAL '1 day'")
    revenue = cur.fetchone()[0] or 0
    conn.close()
    text = f"🌅 *Daily SLH Report*  {datetime.date.today()}\n\n✅ Check-ins today: {checked}/{total}\n💰 Revenue (24h): ${revenue:.2f}\n\n👉 /start to engage!"
    await bot.send_message(ADMIN_IDS[0], text, parse_mode=ParseMode.MARKDOWN_V2)



    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
