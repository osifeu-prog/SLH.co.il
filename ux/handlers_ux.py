# SLH Bot — handlers_ux.py
# UX-enhanced handlers with typing indicator, inline keyboards, error handling
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
from telegram.constants import ChatAction, ParseMode
import ux.responses as R
import ux.keyboards as K

logger = logging.getLogger(__name__)

async def _typing(update: Update, context: ContextTypes.DEFAULT_TYPE, delay: float = 0.4):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(delay)

def _mk(rows):
    buttons = [[InlineKeyboardButton(**btn) for btn in row] for row in rows]
    return InlineKeyboardMarkup(buttons)

async def _reply(update: Update, text: str, keyboard=None):
    kwargs = {"text": text, "parse_mode": ParseMode.MARKDOWN_V2, "disable_web_page_preview": True}
    if keyboard:
        kwargs["reply_markup"] = _mk(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text(**kwargs)
    else:
        await update.message.reply_text(**kwargs)

async def cmd_start_ux(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _typing(update, context)
    # stub  in real app, get user from DB
    await _reply(update, R.msg_welcome(update.effective_user.username or "friend"), K.kb_main_menu())

async def cmd_help_ux(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _typing(update, context)
    await _reply(update, R.msg_help(), K.kb_help())

# Add more handlers as needed (checkin, points, etc.)

def register_ux_handlers(app: Application):
    from telegram.ext import CommandHandler, CallbackQueryHandler
    app.add_handler(CommandHandler("start", cmd_start_ux))
    app.add_handler(CommandHandler("help", cmd_help_ux))
    # Placeholder for other commands  you can add them later
    logger.info("✅ UX handlers registered")
