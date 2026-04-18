# main.py
import os
import sys
import time
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

# תצורה
from config import TOKEN, LOCK_FILE, LOG_FILE, DATA_DIR, USERS_FILE, PRODUCTS_FILE, ORDERS_FILE, ADMIN_ID, START_TIME

# יבוא פונקציות עזר
from utils.lock import setup_lock
from utils.json_utils import load_json, save_json
from utils.ton_api import get_ton_balance
from utils.notifications import notify_admin

# יבוא handlers
from handlers import user_commands, admin_commands, logs_handler, purchase_flow, message_handler

# ========== טעינת נתונים ==========
os.makedirs(DATA_DIR, exist_ok=True)
users = load_json(USERS_FILE, {})
products = load_json(PRODUCTS_FILE, {
    '1': {'name': 'Affiliate Link + SLH VIP Group', 'price': 5.0, 'group_link': ''},
    '2': {'name': 'ORG', 'price': 0.3, 'group_link': ''},
    '3': {'name': 'STRAT', 'price': 0.5, 'group_link': ''},
})
orders = load_json(ORDERS_FILE, {})

# ========== נעילה ==========
setup_lock(LOCK_FILE)

# ========== לוגים ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ========== פונקציות שעוטפות את ה-handlers עם הפרמטרים הנדרשים ==========
def get_user_handlers():
    async def start_wrapper(update, context):
        await user_commands.start(update, context, users, USERS_FILE)
    async def vip_group_wrapper(update, context):
        await user_commands.vip_group(update, context, products)
    async def account_wrapper(update, context):
        await user_commands.account(update, context, users, orders, products)
    async def products_wrapper(update, context):
        await user_commands.products_command(update, context, products)
    return {
        'start': start_wrapper,
        'menu': user_commands.menu,
        'my_link': user_commands.my_link,
        'vip_group': vip_group_wrapper,
        'updates': user_commands.updates,
        'account': account_wrapper,
        'balance': user_commands.balance,
        'status': user_commands.status,
        'products': products_wrapper,
        'help': user_commands.help_command,
        'version': user_commands.version_command,
        'docs': user_commands.docs_command,
    }

def get_admin_handlers():
    async def admin_stats_wrapper(update, context):
        await admin_commands.admin_stats(update, context, users, orders)
    async def admin_last_users_wrapper(update, context):
        await admin_commands.admin_last_users(update, context, users)
    async def admin_pending_wrapper(update, context):
        await admin_commands.admin_pending(update, context, orders)
    async def set_price_wrapper(update, context):
        await admin_commands.set_price(update, context, products, PRODUCTS_FILE)
    async def set_group_wrapper(update, context):
        await admin_commands.set_group(update, context, products, PRODUCTS_FILE)
    return {
        'admin': admin_commands.admin,
        'admin_stats': admin_stats_wrapper,
        'admin_last_users': admin_last_users_wrapper,
        'admin_pending': admin_pending_wrapper,
        'admin_settings': admin_commands.admin_settings,
        'set_price': set_price_wrapper,
        'set_group': set_group_wrapper,
        'system': admin_commands.system_command,
        'restart': admin_commands.restart_bot,
        'stop': admin_commands.stop_bot,
        'ps': admin_commands.ps_list,
        'kill': admin_commands.kill_process,
    }

def get_purchase_handlers():
    async def buy_start_wrapper(update, context):
        return await purchase_flow.buy_start(update, context, products)
    async def confirm_purchase_wrapper(update, context):
        return await purchase_flow.confirm_purchase(update, context, products)
    async def finalize_purchase_wrapper(update, context):
        return await purchase_flow.finalize_purchase(update, context, users, orders, products, USER_WALLET, ORDERS_FILE)
    return {
        'buy_start': buy_start_wrapper,
        'confirm': confirm_purchase_wrapper,
        'finalize': finalize_purchase_wrapper,
        'cancel': purchase_flow.cancel,
    }

# ========== הגדרת האפליקציה ==========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    user = get_user_handlers()
    admin = get_admin_handlers()
    purchase = get_purchase_handlers()

    # פקודות משתמש
    app.add_handler(CommandHandler("start", user['start']))
    app.add_handler(CommandHandler("menu", user['menu']))
    app.add_handler(CommandHandler("balance", user['balance']))
    app.add_handler(CommandHandler("status", user['status']))
    app.add_handler(CommandHandler("mylink", user['my_link']))
    app.add_handler(CommandHandler("vipgroup", user['vip_group']))
    app.add_handler(CommandHandler("updates", user['updates']))
    app.add_handler(CommandHandler("account", user['account']))
    app.add_handler(CommandHandler("products", user['products']))
    app.add_handler(CommandHandler("version", user['version']))
    app.add_handler(CommandHandler("docs", user['docs']))
    app.add_handler(CommandHandler("help", user['help']))

    # פקודות מנהל
    app.add_handler(CommandHandler("admin", admin['admin']))
    app.add_handler(CommandHandler("set_price", admin['set_price']))
    app.add_handler(CommandHandler("set_group", admin['set_group']))
    app.add_handler(CommandHandler("system", admin['system']))
    app.add_handler(CommandHandler("restart", admin['restart']))
    app.add_handler(CommandHandler("stop", admin['stop']))
    app.add_handler(CommandHandler("ps", admin['ps']))
    app.add_handler(CommandHandler("kill", admin['kill']))
    app.add_handler(CommandHandler("logs", logs_handler.logs_command))
    app.add_handler(CommandHandler("logs_raw", logs_handler.logs_raw))

    # שיחת רכישה
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("buy", purchase['buy_start'])],
        states={
            purchase_flow.PRODUCT_SELECT: [CallbackQueryHandler(purchase['confirm'], pattern=r'^buy_')],
            purchase_flow.CONFIRM: [CallbackQueryHandler(purchase['finalize'], pattern=r'^confirm_')],
        },
        fallbacks=[CommandHandler("cancel", purchase['cancel'])],
    )
    app.add_handler(conv_handler)

    # כפתורי אדמין
    async def msg_wrapper(update, context):
        handlers_dict = {
            'admin_stats': admin['admin_stats'],
            'admin_last_users': admin['admin_last_users'],
            'admin_pending': admin['admin_pending'],
            'admin_settings': admin['admin_settings'],
            'ps_list': admin['ps'],
            'restart_bot': admin['restart'],
            'stop_bot': admin['stop'],
            'vip_group': user['vip_group'],
            'updates': user['updates'],
            'account': user['account'],
        }
        await message_handler.message_handler(update, context, handlers_dict)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_wrapper))

    logging.info("--- SLH BOT ENGINE: VERSION 3.0 LOADED ---")
    print("Bot is running with full features! Type /docs for documentation.")
    app.run_polling()

if __name__ == "__main__":
    main()
