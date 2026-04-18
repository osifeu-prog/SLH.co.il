# utils/notifications.py
import logging
import subprocess
import os
from config import ADMIN_ID, LOG_FILE

# פונקציה לשליחת הודעה לטלגרם (דרך curl או request)
async def notify_admin(bot, message: str):
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"🔔 *SLH Bot Update*\n{message}", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")

def notify_admin_sync(message: str):
    # גרסה סינכרונית (לשימוש ב-watchdog)
    try:
        import requests
        from config import TOKEN
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {'chat_id': ADMIN_ID, 'text': f"🔔 *SLH Bot Update*\n{message}", 'parse_mode': 'Markdown'}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to notify admin: {e}")
