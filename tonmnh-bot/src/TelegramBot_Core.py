# -*- coding: utf-8 -*-
import os
import logging
import aiohttp
import json
import time
import re
import sys
import subprocess
import atexit
import signal
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get('SLH_BOT_TOKEN')
RPC_URL = os.environ.get('RPC_URL', 'https://testnet.toncenter.com/api/v2')
USER_WALLET = os.environ.get('USER_WALLET', '')
TONCENTER_API_KEY = os.environ.get('TONCENTER_API_KEY', '')
TON_NETWORK = os.environ.get('TON_NETWORK', 'testnet')
ADMIN_ID = 224223270

VERSION = "2.1.0"
START_TIME = time.time()

if not TOKEN:
    raise ValueError("SLH_BOT_TOKEN not found in environment variables")

# ========== SINGLETON LOCK ==========
LOCK_FILE = os.path.join(os.path.dirname(__file__), '..', 'bot.lock')  # D:\TerminalCommandCenter\bot.lock

def check_lock_and_create():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = f.read().strip()
            # בדיקה אם התהליך עדיין רץ (ב-Windows)
            result = subprocess.run(f'ps -p {pid}', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"❌ Bot already running (PID: {pid}). Exiting.")
                sys.exit(1)
            else:
                # קובץ נעילה ישן – מוחק וממשיך
                os.remove(LOCK_FILE)
                print(f"⚠️ Removed stale lock file from PID {pid}.")
        except Exception as e:
            print(f"⚠️ Error checking lock file: {e}. Continuing anyway?")
            # מחיקת הקובץ השבור
            try:
                os.remove(LOCK_FILE)
            except:
                pass
    # כתיבת PID נוכחי
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print(f"🔒 Lock file created with PID: {os.getpid()}")

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("🔓 Lock file removed.")

atexit.register(remove_lock)

def signal_handler(sig, frame):
    remove_lock()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# הפעל את הבדיקה מיד
check_lock_and_create()

# ========== LOGGING ==========
log_file = r'D:\TerminalCommandCenter\logs\bot_integration.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

DATA_DIR = r'D:\TerminalCommandCenter\data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(file, default):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

users = load_json(USERS_FILE, {})
products = load_json(PRODUCTS_FILE, {
    '1': {'name': 'Affiliate Link + SLH VIP Group', 'price': 5.0, 'group_link': ''},
    '2': {'name': 'ORG', 'price': 0.3, 'group_link': ''},
    '3': {'name': 'STRAT', 'price': 0.5, 'group_link': ''},
})
orders = load_json(ORDERS_FILE, {})

# ========== TON BALANCE ==========
async def get_ton_balance(address: str) -> float | None:
    if not TONCENTER_API_KEY:
        logging.error("TONCENTER_API_KEY missing")
        return None
    url = f"{RPC_URL}/getAddressInformation"
    params = {'address': address, 'api_key': TONCENTER_API_KEY}
    logging.info(f"Request URL: {url}")
    logging.info(f"Request Params: {params}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                logging.info(f"Response status: {resp.status}")
                if resp.status != 200:
                    logging.error(f"HTTP error {resp.status}")
                    return None
                data = await resp.json()
                logging.info(f"Response data: {data}")
                if data.get('ok'):
                    balance_nano = int(data['result']['balance'])
                    return balance_nano / 1_000_000_000
                else:
                    logging.error(f"TON Center error: {data}")
                    return None
    except Exception as e:
        logging.exception(f"Exception in get_ton_balance: {e}")
        return None

# ========== USER COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in users:
        users[str(user_id)] = {
            'referrer': None,
            'balance': 0.0,
            'joined': time.time(),
            'username': update.effective_user.username,
            'first_name': update.effective_user.first_name
        }
        save_json(USERS_FILE, users)
    await update.message.reply_text(
        "Welcome to SLH Command Center!\nUse /menu to see options.",
        reply_markup=ReplyKeyboardMarkup([['/menu']], resize_keyboard=True)
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['My Link', 'VIP Group'],
        ['Updates', 'Account'],
        ['/balance', '/status'],
        ['/help']
    ]
    await update.message.reply_text(
        "Main menu:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(f"Your personal referral link:\nhttps://t.me/{bot_username}?start={user_id}")

async def vip_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = products.get('1', {}).get('group_link')
    await update.message.reply_text(link or "No group link found. Contact admin.")

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Updates will appear here soon.")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_orders = [o for o in orders.values() if o['user_id'] == user_id]
    if not user_orders:
        await update.message.reply_text("No recent orders.")
        return
    msg = "Your recent orders:\n"
    for o in user_orders[-5:]:
        product = products.get(o['product_id'], {}).get('name', 'Unknown')
        msg += f" {o['order_id']} | {product} | {o['amount']} TON\n"
    await update.message.reply_text(msg)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not USER_WALLET:
        await update.message.reply_text("Wallet address not set")
        return
    waiting = await update.message.reply_text("Fetching balance...")
    bal = await get_ton_balance(USER_WALLET)
    if bal is None:
        # נסיון חוזר אחד
        bal = await get_ton_balance(USER_WALLET)
    if bal is None:
        await waiting.edit_text("Cannot get balance after retry. Check connection and API key.")
    elif bal == 0:
        await waiting.edit_text("Your wallet balance is 0 TON. Time to top up?")
    else:
        await waiting.edit_text(f"Your wallet balance:\n{bal:.2f} TON", parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(r'D:\TerminalCommandCenter\TODO.md', 'r', encoding='utf-8') as f:
            todo = f.read()
    except FileNotFoundError:
        todo = "TODO.md file not found."
    await update.message.reply_text(f"Active tasks:\n\n{todo}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Available commands:*\n"
        "/start - Main menu\n"
        "/menu - Show menu\n"
        "/balance - Show TON balance\n"
        "/status - Project status\n"
        "/mylink - Get referral link\n"
        "/vipgroup - Get VIP group link\n"
        "/updates - Latest updates\n"
        "/account - Your orders\n"
        "/buy <id> - Purchase a product\n"
        "/admin - Admin panel\n"
        "/version - Bot version and uptime\n"
        "/help - This help"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        product_id = context.args[0]
        product = products.get(product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return
        price = product['price']
        memo = f"slh_payment_{user_id}_{int(time.time())}"
        order_id = f"SLH-{int(time.time())}"
        orders[order_id] = {
            'order_id': order_id,
            'user_id': str(user_id),
            'product_id': product_id,
            'amount': price,
            'status': 'pending',
            'memo': memo,
            'timestamp': time.time()
        }
        save_json(ORDERS_FILE, orders)
        await update.message.reply_text(
            f"To purchase {product['name']}, send exactly {price} TON\n"
            f"to address {USER_WALLET}\n"
            f"with memo: {memo}"
        )  # ללא parse_mode כדי למנוע שגיאות Markdown
    except IndexError:
        await update.message.reply_text("Usage: /buy <product_id>")

# ========== ADMIN COMMANDS ==========
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    keyboard = [
        ['Statistics', 'Last users'],
        ['Pending payments', 'Settings'],
        ['System', 'Processes'],
        ['Kill', 'Restart', 'Stop'],
        ['/help']
    ]
    await update.message.reply_text(
        "Admin panel - choose action:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total = len(users)
    paid = len([o for o in orders.values() if o.get('status') == 'paid'])
    pending = len([o for o in orders.values() if o.get('status') == 'pending'])
    affiliates = len([u for u in users.values() if u.get('referrer')])
    await update.message.reply_text(
        f"*Statistics*\n"
        f"Registered: {total}\n"
        f"Paid: {paid}\n"
        f"Pending: {pending}\n"
        f"Affiliates: {affiliates}",
        parse_mode='Markdown'
    )

async def admin_last_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    last = list(users.keys())[-15:]
    await update.message.reply_text("Last 15 users:\n" + "\n".join(last))

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    pending = [o for o in orders.values() if o.get('status') == 'pending']
    if not pending:
        await update.message.reply_text("No pending payments.")
        return
    msg = "Pending payments:\n"
    for p in pending:
        msg += f"#{p.get('order_id')}: {p.get('amount')} TON from user {p.get('user_id')} (memo: {p.get('memo')})\n"
    await update.message.reply_text(msg)

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "Settings:\n"
        "/set_price <product_id> <price>\n"
        "/set_group <product_id> <link>"
    )

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        price = float(context.args[1])
        if pid in products:
            products[pid]['price'] = price
            save_json(PRODUCTS_FILE, products)
            await update.message.reply_text(f"Price for product {pid} updated to {price} TON.")
        else:
            await update.message.reply_text("Product not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_price <product_id> <price>")

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        link = context.args[1]
        if pid in products:
            products[pid]['group_link'] = link
            save_json(PRODUCTS_FILE, products)
            await update.message.reply_text(f"Group link for product {pid} updated.")
        else:
            await update.message.reply_text("Product not found.")
    except IndexError:
        await update.message.reply_text("Usage: /set_group <product_id> <link>")

# ========== MESSAGE HANDLER (for admin buttons) ==========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if text == 'Statistics':
        await admin_stats(update, context)
    elif text == 'Last users':
        await admin_last_users(update, context)
    elif text == 'Pending payments':
        await admin_pending(update, context)
    elif text == 'Settings':
        await admin_settings(update, context)
    elif text == 'System':
        await update.message.reply_text("Usage: /system <command> (type manually)")
    elif text == 'Processes':
        await ps_list(update, context)
    elif text == 'Kill':
        await update.message.reply_text("Usage: /kill <PID> (type manually)")
    elif text == 'Restart':
        await restart_bot(update, context)
    elif text == 'Stop':
        await stop_bot(update, context)
    elif text == 'VIP Group':
        await vip_group(update, context)
    elif text == 'Updates':
        await updates(update, context)
    elif text == 'Account':
        await account(update, context)

# ========== LOG FILTERING ==========
def filter_tokens(text):
    # תבנית לטוקן רגיל: 10 ספרות:35 תווים
    token_pattern = re.compile(r'\b\d{9,10}:[A-Za-z0-9_-]{35}\b')
    text = token_pattern.sub('[BOT_TOKEN_FILTERED]', text)
    # תבנית לטוקן בנתיב URL: /bot<TOKEN>/
    url_token_pattern = re.compile(r'/bot\d{9,10}:[A-Za-z0-9_-]{35}/')
    text = url_token_pattern.sub('/bot[BOT_TOKEN_FILTERED]/', text)
    return text

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send last 30 lines of bot log to admin (token filtered)"""
    if update.effective_user.id != ADMIN_ID:
        return
    log_file = "D:/TerminalCommandCenter/logs/bot_integration.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        filtered_lines = [filter_tokens(line) for line in lines]
        log_text = ''.join(filtered_lines[-30:])
        if not log_text.strip():
            log_text = "No recent log entries (after filtering)."
        if len(log_text) > 3500:
            for i in range(0, len(log_text), 3500):
                await update.message.reply_text(f"`\n{log_text[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{log_text}\n`", parse_mode='Markdown')
        print(f"Admin {update.effective_user.id} requested logs.")
    except FileNotFoundError:
        await update.message.reply_text("Log file not found.")
    except Exception as e:
        await update.message.reply_text(f"Error reading logs: {e}")

async def logs_raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get raw logs (with token) - admin only"""
    if update.effective_user.id != ADMIN_ID:
        return
    log_file = "D:/TerminalCommandCenter/logs/bot_integration.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        log_text = ''.join(lines[-30:])
        if not log_text.strip():
            log_text = "No recent log entries."
        if len(log_text) > 3500:
            for i in range(0, len(log_text), 3500):
                await update.message.reply_text(f"`\n{log_text[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{log_text}\n`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# ========== VERSION COMMAND ==========
async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = int(time.time() - START_TIME)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    await update.message.reply_text(
        f"*SLH Bot v{VERSION}*\n"
        f"Uptime: {hours}h {minutes}m {seconds}s\n"
        f"Admin: @osifungar\n"
        f"Repo: [GitHub](https://github.com/your/repo)",  # החלף בקישור אמיתי
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========== ADVANCED ADMIN COMMANDS ==========
async def system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute a system command (admin only) - use with caution!"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /system <command>")
        return
    cmd = ' '.join(context.args)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        if not output:
            output = "Command executed (no output)."
        if len(output) > 3500:
            for i in range(0, len(output), 3500):
                await update.message.reply_text(f"`\n{output[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{output}\n`", parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Command timed out after 10 seconds.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot (admin only) - watchdog will restart it."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    logging.warning(f"Bot restart triggered by admin {update.effective_user.id}")
    await update.message.reply_text("Restarting bot... Watchdog will bring it back.")
    sys.exit(0)

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the bot (admin only) - watchdog will restart it."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    logging.warning(f"Bot stopped by admin {update.effective_user.id}")
    await update.message.reply_text("Stopping bot... Watchdog will restart it.")
    sys.exit(0)

async def ps_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List running python processes (admin only)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    try:
        result = subprocess.run('ps aux | grep python', shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        await update.message.reply_text(f"`\n{output}\n`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def kill_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill a python process by PID (admin only)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /kill <PID>")
        return
    try:
        pid = int(context.args[0])
        subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
        await update.message.reply_text(f"Process {pid} killed.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mylink", my_link))
    app.add_handler(CommandHandler("vipgroup", vip_group))
    app.add_handler(CommandHandler("updates", updates))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("version", version_command))

    # Admin commands
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("set_price", set_price))
    app.add_handler(CommandHandler("set_group", set_group))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("logs_raw", logs_raw))
    app.add_handler(CommandHandler("system", system_command))
    app.add_handler(CommandHandler("restart", restart_bot))
    app.add_handler(CommandHandler("stop", stop_bot))
    app.add_handler(CommandHandler("ps", ps_list))
    app.add_handler(CommandHandler("kill", kill_process))

    # Message handler for admin buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logging.info("--- SLH BOT ENGINE: FULL VERSION LOADED ---")
    print("Bot is running with full features!")
    app.run_polling()

if __name__ == "__main__":
    main()
