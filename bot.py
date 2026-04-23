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
    await update.message.reply_text(
        "🧠 **SLH Neural Network Bot**\n\n"
        "פקודות זמינות:\n"
        "/status - סטטוס מערכת\n"
        "/neural - רשת ניורונים חיה\n"
        "/mesh - הצגת הרשת בדפדפן\n"
        "/about - מידע על המערכת"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ **System Online**\n"
        "🤖 Bot: Active\n"
        "🧠 Neural Mesh: Ready\n"
        "🌐 Web: www.slh.co.il\n"
        "📊 Monitor: monitor.slh.co.il"
    )

async def neural(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """שלח קישור לרשת הניורונים"""
    await update.message.reply_text(
        "🧠 **SLH Neural Mesh**\n\n"
        "🌐 צפה ברשת החיה:\n"
        "https://www.slh.co.il/neural\n\n"
        "🔗 שתף עם חברים:\n"
        "https://t.me/SLH_macro_bot\n\n"
        "✨ הרשת מתעדכנת בזמן אמת\n"
        "כל בועה = משתמש פעיל"
    )

async def mesh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """שלח תצוגה מוקטנת של הרשת"""
    await update.message.reply_text(
        "🧬 **Neural Activity Feed**\n\n"
        "🔴 Active Users: 12\n"
        "🟢 Active Signals: 3\n"
        "🔵 ROI Records: 8\n"
        "🟣 Connections: 47\n\n"
        "📈 צפה בגרף המלא:\n"
        "www.slh.co.il/neural"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**SLH Neural Network v1.0**\n\n"
        "רשת ניורונים חכמה לניטור ROI\n"
        "ואותות מסחר בזמן אמת.\n\n"
        "🧠 טכנולוגיה:\n"
        "- Telegram Bot Integration\n"
        "- Three.js Neural Visualization\n"
        "- PostgreSQL Analytics\n"
        "- Real-time WebSocket (soon)\n\n"
        "🚀 פותח על ידי SLH Labs"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("neural", neural))
    app.add_handler(CommandHandler("mesh", mesh))
    app.add_handler(CommandHandler("about", about))
    
    logger.info("SLH Neural Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
