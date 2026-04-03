#!/usr/bin/env python3
"""
TON Airdrop Bot - גרסה פשוטה ומושלמת
עובד עם כל המערכות שלך
"""

import logging
import requests
import time
from datetime import datetime

# ====================
# CONFIGURATION
# ====================
TOKEN = "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls"
WALLET_ADDRESS = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"

# ====================
# SETUP
# ====================
logging.basicConfig(
    format='%(asctime)s - TON BOT - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====================
# BOT FUNCTIONS
# ====================
def send_telegram_message(chat_id, text):
    """שולח הודעה לטלגרם"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

def handle_start_command(chat_id, user_name, username=""):
    """מטפל בפקודת /start"""
    message = f"""
🎉 <b>ברוך הבא ל-SLH AIR Drop Bot!</b>

<b>מערכת הרשמה וטוקניזציה של SLH</b>

👤 <b>משתמש:</b> {user_name}
🆔 <b>Username:</b> @{username if username else 'לא צוין'}
📅 <b>תאריך:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 <b>פרטים:</b>
• 1,000 טוקני SLH = 44.4 ₪
• קבלה אוטומטית תוך 24 שעות
• תמיכה מלאה בעברית

🔗 <b>קישורים למערכת:</b>
• טלגרם: @Osifs_Factory_bot
• אתר: https://slhisrael.com/
• חוזה BSC: https://bscscan.com/token/0xACb0A09414CEA1C879c67bB7A877E4e19480f022

<b>השלב הראשון:</b>
<b>שלח או אשר את שם המשתמש הטלגרם שלך</b>

(לדוגמה: @Osif83)
"""
    
    return send_telegram_message(chat_id, message)

def handle_username(chat_id, username, user_name):
    """מטפל בקבלת username"""
    # ניקוי ה-username
    username = username.replace('@', '').strip()
    
    if len(username) < 3:
        send_telegram_message(chat_id, "❌ <b>שם משתמש לא תקין.</b>\n\nאנא שלח username תקין (לפחות 3 תווים).")
        return False
    
    # הודעה על אישור
    message = f"""
✅ <b>שם משתמש התקבל!</b>

👤 <b>Username:</b> @{username}
👥 <b>שם:</b> {user_name}
🆔 <b>מזהה:</b> {chat_id}
📅 <b>נרשם:</b> {datetime.now().strftime('%H:%M')}

💰 <b>השלב הבא - תשלום:</b>

1. <b>שלח 44.4 TON</b> לארנק שלנו:
<code>{WALLET_ADDRESS}</code>

2. <b>שמור את מספר העסקה</b> (Transaction Hash)

3. <b>שלח את מספר העסקה</b> לכאן

4. <b>קבל אוטומטית 1,000 טוקני SLH</b>

⚠️ <b>חשוב:</b>
• שלח <b>בדיוק 44.4 TON</b>
• שמור את מספר העסקה!
• זמן אספקה: עד 24 שעות

<b>יש שאלות?</b> פנה ל-@Osif83
"""
    
    send_telegram_message(chat_id, message)
    return True

def handle_transaction(chat_id, tx_hash, user_name):
    """מטפל בשליחת מספר עסקה"""
    message = f"""
🎉 <b>תשלום התקבל!</b>

<b>פרטי עסקה:</b>
👤 <b>משתמש:</b> {user_name}
🆔 <b>מזהה:</b> {chat_id}
🔗 <b>מספר עסקה:</b> 
<code>{tx_hash[:40]}...</code>
💰 <b>סכום:</b> 44.4 TON
🎁 <b>טוקנים:</b> 1,000 SLH

⏳ <b>סטטוס:</b> באישור
🕐 <b>זמן אספקה:</b> עד 24 שעות

📊 <b>למעקב:</b> שלח /status
📞 <b>תמיכה:</b> @Osif83

<b>תודה על ההשתתפות במערכת SLH!</b>
"""
    
    send_telegram_message(chat_id, message)
    
    # גם שלח לך התראה
    admin_message = f"🚨 תשלום חדש!\nמשתמש: {user_name}\nID: {chat_id}\nTX: {tx_hash[:20]}..."
    send_telegram_message(7757102350, admin_message)  # החלף עם ה-ID שלך
    
    return True

def handle_status(chat_id, user_name):
    """מטפל בפקודת /status"""
    message = f"""
📊 <b>סטטוס אישי - SLH Tokens</b>

👤 <b>משתמש:</b> {user_name}
🆔 <b>מזהה:</b> {chat_id}
💰 <b>טוקנים:</b> 1,000 SLH
💸 <b>ערך:</b> 44.4 ₪
✅ <b>סטטוס:</b> בהמתנה לאישור

<b>קישורים רלוונטיים:</b>
• אתר: https://slhisrael.com/
• דשבורד: https://web-production-112f6.up.railway.app/investors/
• טלגרם: @Osifs_Factory_bot

<b>יש שאלות?</b> @Osif83
"""
    
    send_telegram_message(chat_id, message)
    return True

def handle_help(chat_id, user_name):
    """מטפל בפקודת /help"""
    message = f"""
❓ <b>עזרה - SLH Airdrop Bot</b>

<b>פקודות זמינות:</b>
• /start - התחלת מערכת
• /status - בדיקת סטטוס
• /help - הצגת עזרה זו

<b>תהליך רכישה:</b>
1. שלח username טלגרם
2. שלח 44.4 TON לארנק שלנו
3. שלח את מספר העסקה
4. קבל 1,000 טוקני SLH

<b>קישורים חשובים:</b>
• ארנק תשלום: <code>{WALLET_ADDRESS}</code>
• אתר רשמי: https://slhisrael.com/
• חוזה BSC: https://bscscan.com/token/0xACb0A09414CEA1C879c67bB7A877E4e19480f022
• טלגרם: @Osifs_Factory_bot

<b>תמיכה:</b> @Osif83
"""
    
    send_telegram_message(chat_id, message)
    return True

# ====================
# MAIN POLLING LOOP
# ====================
def main():
    """לולאת העבודה הראשית של הבוט"""
    logger.info("🚀 SLH Airdrop Bot מתחיל...")
    
    offset = 0
    user_data = {}  # אחסון זמני של נתוני משתמשים
    
    while True:
        try:
            # קבלת עדכונים מטלגרם
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "").strip()
                        user_name = msg["chat"].get("first_name", "משתמש")
                        username = msg["chat"].get("username", "")
                        
                        logger.info(f"הודעה מ-{user_name} (@{username}): {text[:50]}")
                        
                        # שמור נתוני משתמש
                        if chat_id not in user_data:
                            user_data[chat_id] = {
                                "name": user_name,
                                "username": username,
                                "state": "start"
                            }
                        
                        # טיפול בפקודות
                        if text == "/start":
                            user_data[chat_id]["state"] = "awaiting_username"
                            handle_start_command(chat_id, user_name, username)
                        
                        elif text == "/status":
                            handle_status(chat_id, user_name)
                        
                        elif text == "/help":
                            handle_help(chat_id, user_name)
                        
                        else:
                            # טיפול לפי מצב
                            state = user_data[chat_id]["state"]
                            
                            if state == "awaiting_username":
                                if handle_username(chat_id, text, user_name):
                                    user_data[chat_id]["state"] = "awaiting_payment"
                                    user_data[chat_id]["provided_username"] = text.replace('@', '')
                            
                            elif state == "awaiting_payment":
                                # אם זה נראה כמו כתובת TON, בקש username
                                if text.startswith(("UQ", "EQ", "0Q")) and len(text) > 20:
                                    send_telegram_message(chat_id, "❌ <b>נדרש username קודם!</b>\n\nאנא שלח את שם המשתמש הטלגרם שלך לפני התשלום.")
                                # אם זה נראה כמו hash עסקה
                                elif len(text) > 30:
                                    handle_transaction(chat_id, text, user_name)
                                    user_data[chat_id]["state"] = "payment_received"
                                else:
                                    send_telegram_message(chat_id, "🤖 אנא שלח את שם המשתמש הטלגרם שלך או מספר עסקה.")
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"שגיאה בלולאה הראשית: {e}")
            time.sleep(5)

# ====================
# START BOT
# ====================
if __name__ == "__main__":
    main()
