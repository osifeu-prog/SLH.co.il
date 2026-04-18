# handlers/user_commands.py
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import USER_WALLET, VERSION, START_TIME, ADMIN_USERNAME
from utils.json_utils import save_json
from utils.ton_api import get_ton_balance


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, users, USERS_FILE):
    user_id = update.effective_user.id
    if str(user_id) not in users:
        users[str(user_id)] = {
            "referrer": None,
            "balance": 0.0,
            "joined": time.time(),
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
        }
        save_json(USERS_FILE, users)

    await update.message.reply_text(
        "Welcome to SLH Command Center!\nUse /menu to see options.",
        reply_markup=ReplyKeyboardMarkup([["/menu"]], resize_keyboard=True),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["My Link", "VIP Group"],
        ["Updates", "Account"],
        ["/balance", "/status"],
        ["/products", "/help"],
    ]
    await update.message.reply_text(
        "Main menu:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(
        f"Your personal referral link:\nhttps://t.me/{bot_username}?start={user_id}"
    )


async def vip_group(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    link = products.get("1", {}).get("group_link")
    await update.message.reply_text(link or "No group link found. Contact admin.")


async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Updates will appear here soon.")


async def account(update: Update, context: ContextTypes.DEFAULT_TYPE, users, orders, products):
    user_id = str(update.effective_user.id)
    user_orders = [o for o in orders.values() if o["user_id"] == user_id]

    if not user_orders:
        await update.message.reply_text("No recent orders.")
        return

    lines = ["Your recent orders:"]
    for order in user_orders[-5:]:
        product = products.get(order["product_id"], {}).get("name", "Unknown")
        lines.append(f"{order['order_id']} | {product} | {order['amount']} TON")

    await update.message.reply_text("\n".join(lines))


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not USER_WALLET:
        await update.message.reply_text("Wallet address not set")
        return

    waiting = await update.message.reply_text("Fetching balance...")
    bal = await get_ton_balance(USER_WALLET)

    if bal is None:
        bal = await get_ton_balance(USER_WALLET)

    if bal is None:
        await waiting.edit_text("Cannot get balance after retry. Check connection and API key.")
    elif bal == 0:
        await waiting.edit_text("Your wallet balance is 0 TON. Time to top up?")
    else:
        await waiting.edit_text(f"Your wallet balance:\n{bal:.2f} TON")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(r"D:\TerminalCommandCenter\TODO.md", "r", encoding="utf-8") as f:
            todo = f.read()
    except FileNotFoundError:
        todo = "TODO.md file not found."

    await update.message.reply_text(f"Active tasks:\n\n{todo}")


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    lines = ["Available Products:"]
    for pid, product in products.items():
        lines.append(f"{pid}: {product['name']}  {product['price']} TON")
    lines.append("")
    lines.append("Use /buy <id> to purchase.")

    await update.message.reply_text("\n".join(lines))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "SLH Bot Commands:\n"
        "/start - Main menu\n"
        "/menu - Show menu\n"
        "/balance - Show TON balance\n"
        "/status - Project status\n"
        "/mylink - Get referral link\n"
        "/vipgroup - Get VIP group link\n"
        "/updates - Latest updates\n"
        "/account - Your orders\n"
        "/products - List products\n"
        "/buy <id> - Purchase a product\n"
        "/admin - Admin panel\n"
        "/version - Bot info\n"
        "/docs - Full documentation\n"
        "/help - This help"
    )
    await update.message.reply_text(help_text)


async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = int(time.time() - START_TIME)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60

    text = (
        f"SLH Bot v{VERSION}\n"
        f"Uptime: {hours}h {minutes}m {seconds}s\n"
        f"Admin: {ADMIN_USERNAME}\n"
        f"Repo: https://github.com/your/repo"
    )
    await update.message.reply_text(text, disable_web_page_preview=True)


async def docs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    docs_text = (
        "SLH Bot Documentation\n\n"
        "Core Features:\n"
        "- Singleton lock prevents multiple instances\n"
        "- Advanced logging with token filtering\n"
        "- Watchdog auto-restart on crash\n"
        "- User system with referral links\n"
        "- TON balance checking\n"
        "- Product purchase flow\n\n"
        "Admin Commands:\n"
        "- /admin open admin panel\n"
        "- /set_price <id> <price> update product price\n"
        "- /set_group <id> <link> set VIP group link\n"
        "- /logs filtered logs (token hidden)\n"
        "- /logs_raw raw logs (admin only)\n"
        "- /system <cmd> execute system command\n"
        "- /ps list python processes\n"
        "- /kill <PID> terminate process\n"
        "- /restart restart bot (watchdog)\n"
        "- /stop stop bot (watchdog)\n\n"
        "User Commands:\n"
        "- /start, /menu navigation\n"
        "- /balance check wallet\n"
        "- /status project status\n"
        "- /mylink get referral link\n"
        "- /vipgroup access VIP group\n"
        "- /updates latest news\n"
        "- /account order history\n"
        "- /products list products\n"
        "- /buy <id> purchase\n"
        "- /version bot info\n"
        "- /docs this documentation\n\n"
        "Security:\n"
        "All logs are filtered to hide the bot token.\n"
        "Admin panel is restricted to authorized ID.\n\n"
        "Last updated: 2026-03-14"
    )
    await update.message.reply_text(docs_text)