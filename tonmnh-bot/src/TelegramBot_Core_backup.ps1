import os
import logging
import json
from web3 import Web3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# טעינת כל ההגדרות מקובץ .env
load_dotenv()

TOKEN = os.getenv('SLH_BOT_TOKEN')
RPC_URL = os.getenv('RPC_URL', 'https://bsc-dataseed.binance.org/')
CONTRACT_ADDR = os.getenv('CONTRACT_ADDRESS', '')
USER_WALLET = os.getenv('USER_WALLET', '')
# אם ה-ABI נמצא בקובץ נפרד או כמחרוזת ב-.env – נטען אותו בהתאם
ABI_JSON = os.getenv('ABI', '[]')
ABI = json.loads(ABI_JSON)

if not TOKEN:
    raise ValueError("SLH_BOT_TOKEN not found in .env file")

# לוגים
log_file = r'D:\TerminalCommandCenter\logs\bot_integration.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', 
                    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()])

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# פונקציית התחלה עם כפתורים
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['/balance', '/status'], ['/help']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f" ברוך הבא ל-SLH Command Center!\n\nהארנק המוגדר: `{USER_WALLET[:6]}...{USER_WALLET[-4:]}`\nמה תרצה לבדוק?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDR), abi=ABI)
        raw_balance = contract.functions.balanceOf(w3.to_checksum_address(USER_WALLET)).call()
        decimals = contract.functions.decimals().call()
        final_balance = raw_balance / (10 ** decimals)
        await update.message.reply_text(f" יתרת SLH עבור {update.effective_user.first_name}:\n`{final_balance:,.2f} SLH`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f" שגיאה: {str(e)[:50]}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(r'D:\TerminalCommandCenter\TODO.md', 'r', encoding='utf-8') as f:
        todo = f.read()
    await update.message.reply_text(f" משימות פעילות:\n\n{todo}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("status", status))
    logging.info("--- SLH BOT ENGINE: UI UPDATED ---")
    app.run_polling()