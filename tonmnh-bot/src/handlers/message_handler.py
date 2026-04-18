# handlers/message_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, handlers_dict):
    text = update.message.text
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if text == 'Statistics':
        await handlers_dict['admin_stats'](update, context)
    elif text == 'Last users':
        await handlers_dict['admin_last_users'](update, context)
    elif text == 'Pending payments':
        await handlers_dict['admin_pending'](update, context)
    elif text == 'Settings':
        await handlers_dict['admin_settings'](update, context)
    elif text == 'System':
        await update.message.reply_text("Usage: /system <command> (type manually)")
    elif text == 'Processes':
        await handlers_dict['ps_list'](update, context)
    elif text == 'Kill':
        await update.message.reply_text("Usage: /kill <PID> (type manually)")
    elif text == 'Restart':
        await handlers_dict['restart_bot'](update, context)
    elif text == 'Stop':
        await handlers_dict['stop_bot'](update, context)
    elif text == 'VIP Group':
        await handlers_dict['vip_group'](update, context)
    elif text == 'Updates':
        await handlers_dict['updates'](update, context)
    elif text == 'Account':
        await handlers_dict['account'](update, context)
