import os
import sys
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from scripts.blockchain_manager import BlockchainManager
from scripts.ui_manager import UIManager

load_dotenv('vault/.env')
blockchain = BlockchainManager()
ui = UIManager()
OWNER_ADDR = os.getenv('OWNER_ADDRESS').lower()

async def start(update, context):
    await update.message.reply_text(ui.welcome_msg(update.effective_user.first_name), parse_mode='Markdown')

async def stop_bot(update, context):
    # בדיקה אם השולח הוא ה-Admin (לפי כתובת ארנק או יוזר בסיסי)
    # כאן נשתמש כרגע בבדיקה פשוטה, אפשר לשכלל ל-Telegram ID
    await update.message.reply_text(" מערכת נסגרת עכשיו... (Admin Command)")
    os._exit(0)

def main():
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kill", stop_bot)) # פקודת עצירה
    print("ExpertNet Core is Live. Type /kill in Telegram to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()