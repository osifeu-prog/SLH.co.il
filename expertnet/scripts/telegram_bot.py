import os, sqlite3, logging, datetime, csv, psutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
TOKEN = "8530795944:AAHUaDYR_jf2AjGyaLx5-fmQfxa9IQUH2ag"
BASE_DIR = r'D:\ExpertNet_Core'
DB_PATH = os.path.join(BASE_DIR, 'vault', 'expertnet.db')
CSV_PATH = os.path.join(BASE_DIR, 'vault', 'whitelist.csv')
LOGBOOK_PATH = os.path.join(BASE_DIR, 'docs', 'LOGBOOK.md')
VERCEL_URL = "https://expert-net-core.vercel.app"

def agent_log(action, details):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not os.path.exists(LOGBOOK_PATH):
        os.makedirs(os.path.dirname(LOGBOOK_PATH), exist_ok=True)
        with open(LOGBOOK_PATH, 'w', encoding='utf-8') as f:
            f.write("# ExpertNet Agent Logbook\n| Time | Action | Details |\n|---|---|---|\n")
    with open(LOGBOOK_PATH, 'a', encoding='utf-8') as f:
        f.write(f"| {timestamp} | {action} | {details} |\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    agent_log("START", f"User {uid} connected")
    
    keyboard = [
        [InlineKeyboardButton(" פתח ExpertNet App", web_app=WebAppInfo(url=VERCEL_URL))],
        [InlineKeyboardButton(" פרופיל", callback_data='me'), InlineKeyboardButton(" סטייקינג", callback_data='staking')],
        [InlineKeyboardButton(" העברה P2P", callback_data='p2p'), InlineKeyboardButton(" דוח CSV", callback_data='get_csv')],
        [InlineKeyboardButton(" סטטוס AI", callback_data='ai_status'), InlineKeyboardButton(" אבחון", callback_data='diag')]
    ]
    await update.message.reply_html("<b>ExpertNet Master v21.0</b>\nהמערכת אחודה, מתועדת ומוכנה.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    agent_log("CALLBACK", f"Action: {query.data}")

    if query.data == 'me':
        await query.edit_message_text(" <b>פרופיל משתמש</b>\nהנתונים נמשכים מה-Vault...", parse_mode='HTML', reply_markup=query.message.reply_markup)
    elif query.data == 'ai_status':
        await query.edit_message_text(" <b>סטטוס AI</b>\nתיעוד: פעיל\nסוכן: OpenClaw\nמצב: למידה", parse_mode='HTML', reply_markup=query.message.reply_markup)
    elif query.data == 'diag':
        await query.edit_message_text(f" <b>אבחון</b>\nCPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%", parse_mode='HTML', reply_markup=query.message.reply_markup)
    else:
        await query.edit_message_text(f"פונקציית {query.data} בהקמה...", reply_markup=query.message.reply_markup)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("--- SYSTEM ONLINE: V21.0 ---")
    app.run_polling()