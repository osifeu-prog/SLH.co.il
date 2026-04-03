import os, sqlite3, logging, shutil, datetime
from web3 import Web3
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# --- הגדרות ליבה ---
TOKEN = "8530795944:AAHUaDYR_jf2AjGyaLx5-fmQfxa9IQUH2ag"
ADMIN_ID = "224223270"
BASE_DIR = r'D:\ExpertNet_Core'
DB_PATH = os.path.join(BASE_DIR, 'vault', 'expertnet.db')
KEY_PATH = os.path.join(BASE_DIR, 'vault', 'master.key')
LOG_FILE = os.path.join(BASE_DIR, 'vault', 'system.log')
BSC_RPC = "https://bsc-dataseed.binance.org/"

# --- מנגנון גיבוי אוטומטי ---
def backup_system():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BASE_DIR, 'backups', f'bot_backup_{timestamp}.py')
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    current_file = os.path.join(BASE_DIR, 'scripts', 'telegram_bot.py')
    if os.path.exists(current_file):
        shutil.copy2(current_file, backup_path)
        return backup_path
    return None

# --- הצפנה ו-Web3 ---
w3 = Web3(Web3.HTTPProvider(BSC_RPC))
def get_fernet():
    return Fernet(open(KEY_PATH, "rb").read())

def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall() if fetch else conn.commit()

# --- ממשק משתמש מאוחד (V12) ---
def get_main_menu(uid):
    keyboard = [
        [InlineKeyboardButton(" פתח Mini-App", web_app=WebAppInfo(url="https://expertnet-app.vercel.app"))],
        [InlineKeyboardButton(" פרופיל", callback_data='me'), InlineKeyboardButton(" שוק חי", callback_data='market')],
        [InlineKeyboardButton(" עדכון ארנק", callback_data='reg_wallet'), InlineKeyboardButton(" Vault", callback_data='vault_info')]
    ]
    if str(uid) == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(" ניהול אדמין", callback_data='admin_panel')])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db_query("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (uid,))
    await update.message.reply_html(
        "<b> EXPERTNET EXECUTIVE CORE V12</b>\nהמערכת המאוחדת פעילה עם הגנה מלאה.",
        reply_markup=get_main_menu(uid)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()

    if query.data == 'me':
        res = db_query("SELECT wallet_address, encrypted_key FROM users WHERE telegram_id = ?", (uid,), fetch=True)
        wallet = res[0][0] if res and res[0][0] else "לא מוגדר"
        bal = w3.from_wei(w3.eth.get_balance(wallet), 'ether') if wallet != "לא מוגדר" else 0
        msg = f"<b> פרופיל משתמש:</b>\n ארנק: <code>{wallet}</code>\n יתרה: <b>{bal:.4f} BNB</b>"
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=get_main_menu(uid))

    elif query.data == 'market':
        # שליחת מחירים מהירה
        msg = "<b> מחירי שוק (Live):</b>\nBNB: <code>$626.00</code>\nBTC: <code>$68,300</code>"
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=get_main_menu(uid))

    elif query.data == 'admin_panel' and uid == ADMIN_ID:
        kb = [[InlineKeyboardButton(" הגדר מפתח Vault", callback_data='admin_set_key')],
              [InlineKeyboardButton(" שידור הודעה", callback_data='admin_broadcast')],
              [InlineKeyboardButton(" חזרה", callback_data='back_main')]]
        await query.edit_message_text("<b> פאנל ניהול אדמין</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'back_main':
        await query.edit_message_text("תפריט ראשי:", reply_markup=get_main_menu(uid))

# --- הרצה ---
if __name__ == '__main__':
    b_file = backup_system()
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
    print(f"--- BACKUP CREATED: {b_file} ---")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("--- V12 CORE READY ---")
    app.run_polling()