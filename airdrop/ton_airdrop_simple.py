#!/usr/bin/env python3
"""
TON Airdrop Bot - גרסה פשוטה ויציבה
"""

import os
import logging
import requests
from datetime import datetime

# ====================
# CONFIGURATION
# ====================
TOKEN = "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls"
API_URL = "https://successful-fulfillment-production.up.railway.app"

# ====================
# SETUP
# ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====================
# TELEGRAM API FUNCTIONS
# ====================
def send_message(chat_id, text):
    """שולח הודעה דרך Telegram API"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def handle_start(chat_id, user_name):
    """מטפל בפקודת /start"""
    message = f"""
🎉 <b>ברוך הבא ל-TON Airdrop Bot!</b>

👤 <b>משתמש:</b> {user_name}
📅 <b>תאריך:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 <b>פרטי Airdrop:</b>
• סכום: 1-10 TON למשתמש
• סה"כ תקציב: 1000 TON
• זמן אספקה: עד 24 שעות

📋 <b>איך לקבל Airdrop?</b>
1. שלח את כתובת ארנק ה-TON שלך
2. המתן לאימות אוטומטי
3. קבל את הטוקנים ישירות לארנק!

⚠️ <b>תנאים:</b>
• משתמש אחד בלבד לכתובת ארנק
• כתובת TON תקינה בלבד
• זמין עד גמר התקציב

<b>התחל עכשיו:</b> שלח את כתובת הארנק שלך!
"""
    return send_message(chat_id, message)

def handle_wallet(chat_id, wallet_address):
    """מטפל בכתובת ארנק"""
    # בדיקה בסיסית
    if not wallet_address.startswith(("UQ", "EQ", "0Q")):
        return send_message(chat_id, "❌ כתובת ארנק לא תקינה. אנא שלח כתובת TON שתחל ב-UQ/EQ/0Q")
    
    # שליחה ל-API החדש
    try:
        api_data = {
            "telegram_id": str(chat_id),
            "wallet_address": wallet_address,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        api_response = requests.post(
            f"{API_URL}/api/users/submit_wallet",
            json=api_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if api_response.status_code == 200:
            message = f"""
✅ <b>ארנק התקבל בהצלחה!</b>

📝 <b>פרטים:</b>
• <b>כתובת:</b> <code>{wallet_address[:20]}...</code>
• <b>סטטוס:</b> מאושר
• <b>זמן:</b> {datetime.now().strftime('%H:%M:%S')}

💰 <b>הטוקנים ישלחו בתוך 24 שעות.</b>

🆔 <b>מזהה:</b> {chat_id}
"""
        else:
            message = f"""
❌ <b>שגיאה בשמירת הארנק</b>

<code>{api_response.text}</code>

נסה שוב בעוד כמה דקות.
"""
        
        return send_message(chat_id, message)
        
    except Exception as e:
        logger.error(f"API Error: {e}")
        return send_message(chat_id, "⚠️ שגיאה במערכת. נסה שוב מאוחר יותר.")

def handle_unknown(chat_id):
    """מטפל בהודעות לא מובנות"""
    return send_message(chat_id, "🤖 שלח לי את כתובת ארנק ה-TON שלך או /start")

# ====================
# POLLING LOOP
# ====================
def poll_updates():
    """לולאת קבלת עדכונים מהטלגרם"""
    logger.info("🤖 TON Airdrop Bot מתחיל...")
    
    offset = 0
    
    while True:
        try:
            # קבלת עדכונים
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            
            response = requests.get(url, params=params, timeout=35)
            updates = response.json()
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "").strip()
                        
                        # טיפול בפקודות
                        if text == "/start":
                            user_name = message["chat"].get("first_name", "משתמש")
                            handle_start(chat_id, user_name)
                        
                        elif text.startswith("/"):
                            # פקודה לא מוכרת
                            handle_unknown(chat_id)
                        
                        elif text:
                            # הודעת טקסט רגילה - מניחים שזה ארנק
                            handle_wallet(chat_id, text)
                        
                        else:
                            handle_unknown(chat_id)
            
        except Exception as e:
            logger.error(f"Polling error: {e}")
            import time
            time.sleep(5)

# ====================
# MAIN
# ====================
if __name__ == "__main__":
    poll_updates()
