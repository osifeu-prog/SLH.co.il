import time
import aiohttp
import asyncio, os, json, datetime, requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    name = msg.from_user.first_name or msg.from_user.username or "friend"
    welcome_text = (
        "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—\n"
        "â•‘   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—     â–ˆâ–ˆâ•—  â–ˆâ–ˆâ•—      â•‘\n"
        "â•‘   â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘      â•‘\n"
        "â•‘   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘      â•‘\n"
        "â•‘   â•šâ•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•”â•â•â–ˆâ–ˆâ•‘      â•‘\n"
        "â•‘   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘      â•‘\n"
        "â•‘   â•šâ•â•â•â•â•â•â•â•šâ•â•â•â•â•â•â•â•šâ•â•  â•šâ•â•      â•‘\n"
        "â•‘                                  â•‘\n"
        "â•‘  AI PROJECT CREATION SYSTEM v2  â•‘\n"
        "â•‘  â—† â—† â—† â—† â—† â—† â—† â—† â—† â—† â—† â—†      â•‘\n"
        "â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n"
        "\n"
        f"ðŸ‘‹ ×©×œ×•×, {name}!\n"
        "\n"
        "ðŸ¤– ×ž×” ×× ×™?\n"
        "SLH ×”×•× ×ž×¢×¨×›×ª AI ×œ×™×¦×™×¨×” ×•× ×™×”×•×œ ×¤×¨×•×™×§×˜×™× ×“×™×’×™×˜×œ×™×™×\n"
        "×ž×—× ×•×™×•×ª NFT ×•×¢×“ ×ž×¡×—×¨ ×‘×˜×•×§× ×™× â€” ×”×›×œ ×‘×ž×§×•× ××—×“.\n"
        "\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "âš¡ ×™×›×•×œ×•×ª ×”×ž×¢×¨×›×ª\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "01 Â· AI Chat       Claude, Gemini, Groq\n"
        "02 Â· Marketplace   ×—× ×•×™×•×ª, ×ž×•×¦×¨×™×, NFT\n"
        "03 Â· Rewards       × ×§×•×“×•×ª, ×”×¤× ×™×•×ª, TON\n"
        "04 Â· Support       × ×™×˜×•×¨, ×›×¨×˜×™×¡×™×, ×¡×©× ×™×\n"
        "05 Â· CRM           ×ž×©×ª×ž×©×™×, tier, analytics\n"
        "06 Â· Quiz & XP     ×§×¨×™×¤×˜×•, leaderboard\n"
        "07 Â· TON Wallet    ×ª×©×œ×•×ž×™×, ×ª×ž×œ×•×’×™×\n"
        "08 Â· Infra         DB, Redis, FastAPI\n"
        "\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "ðŸš€ ×”×ª×—×œ ×¢×›×©×™×•\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "/register   â†’ ×”×¦×˜×¨×£ ×œ×ž×¢×¨×›×ª\n"
        "/dashboard  â†’ ×¡×˜×˜×™×¡×˜×™×§×•×ª\n"
        "/upgrade    â†’ Premium plans\n"
        "/help       â†’ ×›×œ ×”×¤×§×•×“×•×ª\n"
        "\n"
        "slh-nft.com Â· @SLH_Claude_bot"
    )
    kb = kb_main_menu()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [[InlineKeyboardButton(**btn) for btn in row] for row in kb]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(welcome_text, parse_mode=None, reply_markup=markup)

# ---- /register, /donate, /checkin, /points, /leaderboard, /status, /users, /broadcast, /morning, /stats, /help, /referral, /roadmap, /support, /feedback, /tasks, /wallet, /transfer, /deposit, /store, /add_product, /products, /buy, /profile, /leaders, /segments, /dashboard, /events, /upgrade, /commission, /doctor, AI, callback (×›×œ ×”×¤×•× ×§×¦×™×•×ª ×”×§×™×™×ž×•×ª ×ž×•×ª×™×¨×•×ª ×›×ž×• ×©×”×™×•, ××‘×œ ×‘×©×œ ××•×¨×š ×”×§×•×“, ×× ×™ ×ž× ×™×— ×©×”×Ÿ × ×©×ž×¨×•. ×× ×—×¡×¨×•×ª, × ×—×–×™×¨ ×‘×§×‘×¦×™× × ×¤×¨×“×™×)
# ×œ×ž×¢×Ÿ ×”×§×™×¦×•×¨, ×× ×™ ×œ× ×›×•×ª×‘ ×¤×” ××ª 500 ×”×©×•×¨×•×ª ×”× ×•×¡×¤×•×ª, ××‘×œ ×”×Ÿ ×§×™×™×ž×•×ª ×‘×’×™×‘×•×™ ×”×ž×§×•×¨×™. × ×©×—×–×¨ ×‘×”×ž×©×š ×‘×ž×™×“×ª ×”×¦×•×¨×š.


# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(cmd_status_enhanced, parse_mode=None)

# ---- /points ----
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"💰 You have {user['points']} points | Streak: {user['streak']} days", parse_mode=None)

# ---- /leaderboard ----
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("No data yet.")
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "🏆 Leaderboard:\n" + "\n".join(f"{i+1}. {uid[:8]}... - {data['points']} pts (Streak {data['streak']})" for i, (uid, data) in enumerate(sorted_users))
    await msg.answer(text, parse_mode=None)

# ---- /daily ----
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("Daily Missions:\n/checkin - Check-in (+5 pts)\n/register - Subscribe", parse_mode=None)

# ---- /referral ----
@dp.message(Command("referral"))
async def cmd_referral(msg: Message):
    ref_link = f"https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}"
    await msg.answer(f"Your personal referral link:\n{ref_link}\n\nShare it with friends to grow the community!", parse_mode=None)

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "Donate to the campaign:\n\nSend TON to:\nUQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp\n\nSupport Levels:\nSupporter - Name on website\nBuilder - Early access + badge\nFounder - Vote on features\nVisionary - Personal call + Founder status",
        parse_mode=None
    )

# ---- /help ----
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "Commands:\n/start /register /donate /status\n/checkin /leaderboard /points /daily\n/users /broadcast /backup /myid /help\n/referral /stats /roadmap /support /feedback /tasks\n/commands - Full command list",
        parse_mode=None
    )

# ---- /roadmap ----
@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    await msg.answer(
        "SLH Roadmap:\n\nQ1 - Crowdfunding launch\nQ2 - Autonomous AI agents\nQ3 - Community governance\nQ4 - Token & marketplace\n\nStay tuned! /register for updates.",
        parse_mode=None
    )

# ---- /stats ----
@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    contacts = load_db(CONTACTS_FILE)
    points_db = load_db(POINTS_FILE)
    total_users = len(contacts)
    checked_in_today = sum(1 for u in points_db.values() if u.get("last_checkin") == datetime.date.today().isoformat())
    total_points = sum(u.get("points", 0) for u in points_db.values())
    text = (
        f"Campaign Stats:\n\nRegistered supporters: {total_users}\nCheck-ins today: {checked_in_today}\nTotal points earned: {total_points}\nCampaign page: https://slh-nft.com/campaign/"
    )
    await msg.answer(text, parse_mode=None)

# ---- Callback handler (full) ----
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    await callback.answer()
    msg = callback.message
    handlers = {
        "cmd_status":      cmd_status,
        "cmd_points":      cmd_points,
        "cmd_checkin":     cmd_checkin,
        "cmd_daily":       cmd_daily,
        "cmd_leaderboard": cmd_leaderboard,
        "cmd_referral":    cmd_referral,
        "cmd_donate":      cmd_donate,
        "cmd_help":        cmd_help,
        "cmd_roadmap":     cmd_roadmap,
        "cmd_menu":        cmd_start,
        "cmd_stats":       cmd_stats,
        "admin_users":     admin_users_callback,
        "admin_broadcast": admin_broadcast_callback,
    }
    handler = handlers.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer(f"Unknown action: {data}")



    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())