import os, sqlite3, logging, shutil, datetime, time
from web3 import Web3
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, Defaults

# --- קונפיגורציה מתקדמת ---
TOKEN = "8530795944:AAHUaDYR_jf2AjGyaLx5-fmQfxa9IQUH2ag"
ADMIN_ID = 224223270 # כנאמבר לביצוע השוואות מהירות
BASE_DIR = r'D:\ExpertNet_Core'
DB_PATH = os.path.join(BASE_DIR, 'vault', 'expertnet.db')
KEY_PATH = os.path.join(BASE_DIR, 'vault', 'master.key')
LOG_FILE = os.path.join(BASE_DIR, 'vault', 'system.log')
BSC_RPC = "https://bsc-dataseed.binance.org/"

# --- אבטחה וניהול שגיאות ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger("ExpertNet_Core")

def get_fernet():
    try:
        with open(KEY_PATH, "rb") as f:
            return Fernet(f.read())
    except Exception as e:
        logger.error(f"Critical: Master Key missing! {e}")
        return None

# --- פונקציות ליבה משופרות ---
def db_query(query, params=(), fetch=False):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch: return cursor.fetchall()
            conn.commit()
    except Exception as e:
        logger.error(f"Database Error: {e}")
        return None

# --- חיבור בלוקצ'יין יציב ---
def get_w3():
    w3 = Web3(Web3.HTTPProvider(BSC_RPC))
    if not w3.is_connected():
        logger.warning("Primary RPC failed, retrying...")
        # כאן אפשר להוסיף RPC חלופי בעתיד
    return w3

# --- תפריטים ---
def get_main_menu(uid):
    keyboard = [
        [InlineKeyboardButton(" פתח ExpertNet App", web_app=WebAppInfo(url="https://expertnet-app.vercel.app"))],
        [InlineKeyboardButton(" פרופיל", callback_data='me'), InlineKeyboardButton(" שוק חי", callback_data='market')],
        [InlineKeyboardButton(" הגדר ארנק", callback_data='reg_wallet'), InlineKeyboardButton(" אבטחה", callback_data='vault_info')]
    ]
    if uid == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(" פאנל ניהול אדמין", callback_data='admin_panel')])
    return InlineKeyboardMarkup(keyboard)

# ---Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_query("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (str(user.id),))
    
    logger.info(f"User {user.id} started the bot")
    welcome_text = (
        f"<b>EXECUTIVE CORE V13.0 ACTIVATED</b>\n\n"
        f"שלום {user.first_name},\n"
        f"המערכת מאובטחת ומחוברת ל-BSC Mainnet."
    )
    await update.message.reply_html(welcome_text, reply_markup=get_main_menu(user.id))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == 'me':
        res = db_query("SELECT wallet_address, encrypted_key FROM users WHERE telegram_id = ?", (str(uid),), fetch=True)
        wallet = res[0][0] if res and res[0][0] else "לא הוגדר"
        key_status = " מוצפן" if res and res[0][1] else " לא מוגדר"
        
        w3 = get_w3()
        bal = 0
        if wallet != "לא הוגדר":
            try: bal = w3.from_wei(w3.eth.get_balance(wallet), 'ether')
            except: pass
            
        msg = (
            f"<b> מצב חשבון:</b>\n"
            f" כתובת: <code>{wallet}</code>\n"
            f" יתרה: <b>{bal:.4f} BNB</b>\n"
            f" Vault: <b>{key_status}</b>"
        )
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=get_main_menu(uid))

    elif query.data == 'admin_panel' and uid == ADMIN_ID:
        kb = [
            [InlineKeyboardButton(" עדכון Private Key", callback_data='admin_set_key')],
            [InlineKeyboardButton(" הורד לוגים", callback_data='admin_get_logs')],
            [InlineKeyboardButton(" חזרה", callback_data='back_main')]
        ]
        await query.edit_message_text("<b> פאנל ניהול אבטחה</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'admin_get_logs' and uid == ADMIN_ID:
        await context.bot.send_document(chat_id=uid, document=open(LOG_FILE, 'rb'), caption="System Logs - V13")

# --- הרצת המערכת ---
if __name__ == '__main__':
    # יצירת גיבוי לפני עליה
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(os.path.join(BASE_DIR, 'scripts', 'telegram_bot.py')):
        shutil.copy2(os.path.join(BASE_DIR, 'scripts', 'telegram_bot.py'), os.path.join(backup_dir, f'core_v13_bak_{timestamp}.py'))

    defaults = Defaults(parse_mode='HTML')
    app = ApplicationBuilder().token(TOKEN).defaults(defaults).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("--- EXPERTNET V13.0 IS RUNNING ---")
    app.run_polling(drop_pending_updates=True)