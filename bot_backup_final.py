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
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
