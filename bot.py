import logging
import os
import sys
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)

# ROI records (in-memory)
roi_records = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **SLH Trading Bot**\n\n"
        "Commands:\n"
        "/status - System status\n"
        "/add_roi <percent> [description] - Add ROI record\n"
        "/last_roi - Show last ROI\n"
        "/signals - Trading signals\n"
        "/help - This message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Commands:**\n\n"
        "/status - System status and stats\n"
        "/add_roi 15.5 - Add ROI percentage\n"
        "/add_roi 15.5 'Q1 profit' - Add ROI with description\n"
        "/last_roi - Show most recent ROI\n"
        "/signals - RSI, MACD trading signals"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_roi = sum(r['value'] for r in roi_records) if roi_records else 0
    avg_roi = total_roi / len(roi_records) if roi_records else 0
    
    await update.message.reply_text(
        f"✅ **System Online**\n\n"
        f"📊 ROI Records: {len(roi_records)}\n"
        f"📈 Average ROI: {avg_roi:.1f}%\n"
        f"🤖 Bot: Active\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

async def add_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_roi 15.5 [description]")
        return
    
    try:
        roi = float(context.args[0])
        description = ' '.join(context.args[1:]) if len(context.args) > 1 else "No description"
        
        roi_records.append({
            'value': roi,
            'description': description,
            'timestamp': datetime.now(),
            'user': update.effective_user.first_name
        })
        
        await update.message.reply_text(
            f"✅ **ROI Added!**\n\n"
            f"📊 ROI: {roi}%\n"
            f"📝 {description}\n"
            f"👤 By: {update.effective_user.first_name}"
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Use: /add_roi 15.5")

async def last_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not roi_records:
        await update.message.reply_text("📭 No ROI records yet. Add one with /add_roi 15.5")
        return
    
    last = roi_records[-1]
    await update.message.reply_text(
        f"📊 **Last ROI Record**\n\n"
        f"💰 ROI: {last['value']}%\n"
        f"📝 {last['description']}\n"
        f"👤 By: {last['user']}\n"
        f"⏰ {last['timestamp'].strftime('%Y-%m-%d %H:%M')}"
    )

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simple mock signals - replace with real API later
    await update.message.reply_text(
        "📈 **Trading Signals**\n\n"
        "┌─────────────────────────┐\n"
        "│ RSI (14):    52.3 🟡   │\n"
        "│ MACD:       📈 BULLISH │\n"
        "│ Stochastic: 68.2 🟢    │\n"
        "├─────────────────────────┤\n"
        "│ **Signal:** HOLD        │\n"
        "│ **Confidence:** 65%     │\n"
        "└─────────────────────────┘\n\n"
        "💡 Next update in 5 min"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add_roi", add_roi))
    app.add_handler(CommandHandler("last_roi", last_roi))
    app.add_handler(CommandHandler("signals", signals))
    
    logger.info("🚀 SLH Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
