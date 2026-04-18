# handlers/logs_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from utils.log_filter import filter_tokens

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send last 30 lines of bot log to admin (token filtered)"""
    if update.effective_user.id != ADMIN_ID:
        return
    log_file = "/app/logs/bot.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        filtered_lines = [filter_tokens(line) for line in lines]
        log_text = ''.join(filtered_lines[-30:])
        if not log_text.strip():
            log_text = "No recent log entries (after filtering)."
        if len(log_text) > 3500:
            for i in range(0, len(log_text), 3500):
                await update.message.reply_text(f"`\n{log_text[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{log_text}\n`", parse_mode='Markdown')
        print(f"Admin {update.effective_user.id} requested logs.")
    except FileNotFoundError:
        await update.message.reply_text("Log file not found at /app/logs/bot.log")
    except Exception as e:
        await update.message.reply_text(f"Error reading logs: {e}")

async def logs_raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get raw logs (with token) - admin only"""
    if update.effective_user.id != ADMIN_ID:
        return
    log_file = "/app/logs/bot.log"
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        log_text = ''.join(lines[-30:])
        if not log_text.strip():
            log_text = "No recent log entries."
        if len(log_text) > 3500:
            for i in range(0, len(log_text), 3500):
                await update.message.reply_text(f"`\n{log_text[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{log_text}\n`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
