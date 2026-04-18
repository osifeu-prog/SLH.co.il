import os
import logging
import aiohttp
import json
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# ======================== משתני סביבה ========================
TOKEN = os.environ.get('SLH_BOT_TOKEN')
RPC_URL = os.environ.get('RPC_URL', 'https://testnet.toncenter.com/api/v2')
USER_WALLET = os.environ.get('USER_WALLET', '')
TONCENTER_API_KEY = os.environ.get('TONCENTER_API_KEY', '')
TON_NETWORK = os.environ.get('TON_NETWORK', 'testnet')
ADMIN_ID = 224223270  # המזהה שלך

if not TOKEN:
    raise ValueError("SLH_BOT_TOKEN not found in environment variables")

# ======================== לוגים ========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log_file = r'D:\TerminalCommandCenter\logs\bot_integration.log'
file_handler = logging.FileHandler(log_file, encoding='utf-8')
logging.getLogger().addHandler(file_handler)

# ======================== נתונים (קבצי JSON) ========================
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

# נתוני ברירת מחדל
users = load_json(USERS_FILE, {})          # user_id -> {'referrer': id, 'balance': 0, 'joined': timestamp}
products = load_json(PRODUCTS_FILE, {      # product_id -> {'name': str, 'price': float, 'group_link': str}
    '1': {'name': 'Affiliate Link + SLH VIP Group', 'price': 5.0, 'group_link': ''},
    '2': {'name': 'ORG', 'price': 0.3, 'group_link': ''},
    '3': {'name': 'STRAT', 'price': 0.5, 'group_link': ''},
})
orders = load_json(ORDERS_FILE, {})        # order_id -> {'user_id': id, 'product_id': id, 'amount': float, 'status': 'pending'|'paid', 'memo': str, 'timestamp': ...}

# ======================== פונקציות TON ========================
async def get_ton_balance(address: str) -> float | None:
    if not TONCENTER_API_KEY:
        logging.error("TONCENTER_API_KEY missing")
        return None
    url = f"{RPC_URL}/getAddressInformation"
    params = {'address': address, 'api_key': TONCENTER_API_KEY}
    logging.info(f"📤 Sending request to {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logging.error(f"HTTP error {resp.status}")
                    return None
                data = await resp.json()
                if data.get('ok'):
                    balance_nano = int(data['result']['balance'])
                    return balance_nano / 1_000_000_000
                else:
                    logging.error(f"TON Center error: {data}")
                    return None
    except Exception as e:
        logging.exception(f"❌ Error calling TON Center: {e}")
        return None

# ======================== פונקציות עזר ========================
def generate_memo(user_id):
    return f"slh_payment_{user_id}_{int(time.time())}"

def get_user_orders(user_id):
    return [o for o in orders.values() if o['user_id'] == user_id]

# ======================== פקודות ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    referrer = int(args[0]) if args and args[0].isdigit() else None

    # שמירת משתמש חדש
    if str(user_id) not in users:
        users[str(user_id)] = {
            'referrer': referrer,
            'balance': 0.0,
            'joined': time.time(),
            'username': update.effective_user.username,
            'first_name': update.effective_user.first_name
        }
        save_json(USERS_FILE, users)

    keyboard = [['/menu']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to SLH Command Center!\nUse /menu to see options.",
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['My Link', 'VIP Group'],
        ['Updates', 'Account'],
        ['/balance', '/status'],
        ['/help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Main menu:", reply_markup=reply_markup)

async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{(await context.bot.get_me()).username}?start={user_id}"
    await update.message.reply_text(f"Your personal referral link:\n{link}")

async def vip_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # מחפש מוצר 1 (קבוצת VIP)
    group_link = products.get('1', {}).get('group_link')
    if group_link:
        await update.message.reply_text(f"VIP Group link:\n{group_link}")
    else:
        await update.message.reply_text("No group link found. Contact admin.")

async def updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Updates will appear here soon.")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_orders = get_orders_by_user(user_id)
    if not user_orders:
        await update.message.reply_text("No recent orders.")
        return
    msg = "Your recent orders:\n"
    for o in user_orders[-5:]:  # 5 אחרונים
        product = products.get(o['product_id'], {}).get('name', 'Unknown')
        msg += f" {o['order_id']} | {product} | {o['amount']} TON\n"
    await update.message.reply_text(msg)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not USER_WALLET:
        await update.message.reply_text("❌ Wallet address not set")
        return
    waiting = await update.message.reply_text("🔍 Fetching balance...")
    bal = await get_ton_balance(USER_WALLET)
    if bal is None:
        await waiting.edit_text("❌ Cannot get balance. Check connection and API key.")
    else:
        await waiting.edit_text(f"💰 Your wallet balance:\n`{bal:.2f} TON`", parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(r'D:\TerminalCommandCenter\TODO.md', 'r', encoding='utf-8') as f:
            todo = f.read()
    except FileNotFoundError:
        todo = "TODO.md file not found."
    await update.message.reply_text(f"📋 Active tasks:\n\n{todo}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Available commands:*\n"
        "/start – Main menu\n"
        "/menu – Show menu\n"
        "/balance – Show TON balance\n"
        "/status – Project status\n"
        "/my link – Get referral link\n"
        "/vip group – Get VIP group link\n"
        "/updates – Latest updates\n"
        "/account – Your orders\n"
        "/admin – Admin panel\n"
        "/help – This help"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ======================== פקודות מנהל ========================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Access denied.")
        return
    keyboard = [
        ['Statistics', 'Last users'],
        ['Pending payments', 'Settings'],
        ['/help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Admin panel – choose action:", reply_markup=reply_markup)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total_users = len(users)
    paid_orders = len([o for o in orders.values() if o['status'] == 'paid'])
    pending = len([o for o in orders.values() if o['status'] == 'pending'])
    affiliates = len([u for u in users.values() if u.get('referrer')])
    msg = (
        f"📊 *Statistics*\n"
        f"Registered: {total_users}\n"
        f"Paid: {paid_orders}\n"
        f"Pending: {pending}\n"
        f"Affiliates: {affiliates}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def admin_last_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    last = list(users.keys())[-15:]
    msg = "Last 15 users:\n" + "\n".join(last)
    await update.message.reply_text(msg)

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    pending = [o for o in orders.values() if o['status'] == 'pending']
    if not pending:
        await update.message.reply_text("No pending payments.")
        return
    msg = "Pending payments:\n"
    for p in pending:
        user = p['user_id']
        amount = p['amount']
        memo = p['memo']
        msg += f"#{p['order_id']}: {amount} TON from user {user} (memo: {memo})\n"
    await update.message.reply_text(msg)

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = (
        "Settings:\n"
        "/set_price <product_id> <price>\n"
        "/set_group <product_id> <link>"
    )
    await update.message.reply_text(msg)

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        price = float(context.args[1])
        if pid in products:
            products[pid]['price'] = price
            save_json(PRODUCTS_FILE, products)
            await update.message.reply_text(f"✅ Price for product {pid} updated to {price} TON.")
        else:
            await update.message.reply_text("❌ Product not found.")
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
            await update.message.reply_text(f"✅ Group link for product {pid} updated.")
        else:
            await update.message.reply_text("❌ Product not found.")
    except IndexError:
        await update.message.reply_text("Usage: /set_group <product_id> <link>")

# ======================== טיפול בכפתורים (לניהול) ========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    # כאן ניתן להוסיף טיפול בכפתורים אינטראקטיביים (למשל אישור תשלום)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    # טיפול בתפריטים פשוטים (ללא פקודות)
    if text == 'Statistics':
        await admin_stats(update, context)
    elif text == 'Last users':
        await admin_last_users(update, context)
    elif text == 'Pending payments':
        await admin_pending(update, context)
    elif text == 'Settings':
        await admin_settings(update, context)
    elif text == 'My Link':
        await my_link(update, context)
    elif text == 'VIP Group':
        await vip_group(update, context)
    elif text == 'Updates':
        await updates(update, context)
    elif text == 'Account':
        await account(update, context)

# ======================== הרצת הבוט ========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # פקודות בסיסיות
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mylink", my_link))
    app.add_handler(CommandHandler("vipgroup", vip_group))
    app.add_handler(CommandHandler("updates", updates))
    app.add_handler(CommandHandler("account", account))

    # פקודות מנהל
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("set_price", set_price))
    app.add_handler(CommandHandler("set_group", set_group))

    # טיפול בכפתורים וטקסט כללי
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logging.info("--- SLH BOT ENGINE: FULL VERSION LOADED ---")
    print("✅ Bot is running with full features!")
    app.run_polling()

if __name__ == "__main__":
    main()