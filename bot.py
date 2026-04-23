import logging
import os
import sys
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import psycopg2
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not TOKEN or not DATABASE_URL:
    logger.error("Missing environment variables")
    sys.exit(1)

def get_db():
    return psycopg2.connect(DATABASE_URL)

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
