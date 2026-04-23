import logging
import os
import sys
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is alive! 🚀")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("System online ✅")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    logger.info("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
