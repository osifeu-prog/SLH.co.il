#!/usr/bin/env python3
"""
TON Airdrop Bot - מבקש username טלגרם
"""

import os
import logging
import requests
import re
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
# USER STATE MANAGEMENT
# ====================
# אחסן את המצבים של המשתמשים בזיכרון (בפועל נשמור ב-Redis/DB)
user_states = {}

def get_user_state(chat_id):
    """מחזיר את המצב הנוכחי של המשתמש"""
    return user_states.get(chat_id, "start")

def set_user_state(chat_id, state):
    """קובע את המצב של המשתמש"""
    user_states[chat_id] = state

# ====================
# TELEGRAM API FUNCTIONS
# ====================
def send_message(chat_id, text, reply_markup=None):
    """שולח הודעה דרך Telegram API"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

# ====================
# HANDLERS
# ====================
def handle_start(chat_id, user_name, username=None):
    """מטפל בפקודת /start"""
    logger.info(f"User {chat_id} ({user_name}) started bot")
    
    # אם יש כבר username, מעבר ישיר לשלב הבא
    if username:
        return handle_wallet_prompt(chat_id, user_name, username)
    
    # אחרת, בקש username
    message = f"""
🎉 <b>ברוך הבא ל-TON Airdrop Bot!</b>

👤 <b>שם:</b> {user_name}
🆔 <b>מזהה:</b> {chat_id}
📅 <b>תאריך:</b> {datetime.now().strftime('%d/%m/%Y')}

💰 <b>פרטי Airdrop:</b>
• 1,000 טוקנים = 44.4 ₪
• זמן אספקה: עד 24 שעות
• תמיכה בעברית

📋 <b>איך זה עובד?</b>
1. שלח את <b>שם המשתמש הטלגרם שלך</b> (ה@username שלך)
2. קבל אישור והנחיות תשלום
3. שלח 44.4 TON לארנק שלנו
4. קבל 1,000 טוקנים אוטומטית

<b>השלב הראשון:</b>
<b>שלח או אשר את שם המשתמש הטלגרם שלך:</b>

(אם אין לך username, לחץ על הגדרות → שם משתמש)
"""
    
    set_user_state(chat_id, "waiting_for_username")
    return send_message(chat_id, message)

def handle_username(chat_id, username):
    """מטפל בקבלת username"""
    logger.info(f"User {chat_id} provided username: {username}")
    
    # ניקוי ה-username
    username = username.strip().replace('@', '')
    
    # בדיקת תקינות בסיסית
    if not username or len(username) < 3:
        return send_message(chat_id, "❌ <b>שם משתמש לא תקין.</b>\n\nאנא שלח username תקין (לפחות 3 תווים).\n\n📝 <b>דוגמה:</b> Osif83")
    
    if not re.match(r'^[a-zA-Z0-9_]{3,}$', username):
        return send_message(chat_id, "❌ <b>שם משתמש לא תקין.</b>\n\nאנא שלח username באנגלית בלבד (אותיות, מספרים וקו תחתון).")
    
    # שמירה במערכת
    try:
        api_data = {
            "telegram_id": str(chat_id),
            "username": username,
            "registered_at": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{API_URL}/api/users/register",
            json=api_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            set_user_state(chat_id, "username_received")
            return handle_wallet_prompt(chat_id, "", username)
        else:
            return send_message(chat_id, "❌ <b>שגיאה בהרשמה.</b>\n\nנסה שוב בעוד כמה דקות.")
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return send_message(chat_id, "⚠️ <b>שגיאה במערכת.</b>\n\nנסה שוב מאוחר יותר.")

def handle_wallet_prompt(chat_id, user_name, username):
    """שולח הנחיות תשלום לאחר קבלת username"""
    message = f"""
✅ <b>שם משתמש התקבל!</b>

👤 <b>Username:</b> @{username}
🆔 <b>מזהה:</b> {chat_id}
📅 <b>נרשם:</b> {datetime.now().strftime('%H:%M')}

💰 <b>השלב הבא - תשלום:</b>

1. <b>שלח 44.4 TON</b> לארנק הבא:
<code>UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp</code>

2. <b>שמור את מספר העסקה</b> (Transaction Hash)

3. <b>שלח את מספר העסקה</b> לכאן לבוט

4. <b>קבל אוטומטית 1,000 טוקנים</b>

⚠️ <b>חשוב:</b>
• שלח <b>בדיוק 44.4 TON</b>
• שמור את מספר העסקה!
• זמן אספקה: עד 24 שעות

<b>יש שאלות?</b> פנה ל-@Osif83
"""
    
    set_user_state(chat_id, "waiting_for_payment")
    return send_message(chat_id, message)

def handle_payment(chat_id, transaction_hash):
    """מטפל בשליחת מספר עסקה"""
    logger.info(f"User {chat_id} sent transaction: {transaction_hash[:20]}...")
    
    # שמירת מספר העסקה
    try:
        api_data = {
            "telegram_id": str(chat_id),
            "transaction_hash": transaction_hash,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{API_URL}/api/users/submit_transaction",
            json=api_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            message = f"""
🎉 <b>תשלום התקבל!</b>

🔗 <b>מספר עסקה:</b> 
<code>{transaction_hash[:30]}...</code>

⏳ <b>סטטוס:</b> באישור
💰 <b>סכום:</b> 44.4 TON
🎁 <b>טוקנים:</b> 1,000

<b>הטוקנים ישלחו אליך בתוך 24 שעות.</b>

📊 <b>מעקב:</b> שלח /status לבדיקת סטטוס
📞 <b>תמיכה:</b> @Osif83
"""
        else:
            message = f"""
❌ <b>שגיאה בשמירת העסקה.</b>

נסה שוב או פנה לתמיכה: @Osif83
"""
        
        return send_message(chat_id, message)
        
    except Exception as e:
        logger.error(f"Payment save error: {e}")
        return send_message(chat_id, "⚠️ <b>שגיאה במערכת.</b>\n\nנסה שוב או פנה לתמיכה: @Osif83")

def handle_status(chat_id):
    """מטפל בפקודת /status"""
    try:
        response = requests.get(
            f"{API_URL}/api/users/{chat_id}/status",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            message = f"""
📊 <b>סטטוס אישי</b>

👤 <b>מזהה:</b> {chat_id}
🆔 <b>Username:</b> @{data.get('username', 'לא ידוע')}
💰 <b>טוקנים:</b> {data.get('tokens', 0):,}
💸 <b>השקעה:</b> {data.get('total_invested', 0)} TON
✅ <b>אירדרופים:</b> {data.get('airdrops_completed', 0)}
"""
        else:
            message = f"""
📊 <b>סטטוס אישי</b>

👤 <b>מזהה:</b> {chat_id}
💰 <b>טוקנים:</b> 0
💸 <b>השקעה:</b> 0 TON
✅ <b>אירדרופים:</b> 0

<i>עדיין לא נרשמת! שלח /start כדי להתחיל.</i>
"""
        
        return send_message(chat_id, message)
        
    except:
        return send_message(chat_id, "📊 <b>לא ניתן לטעון סטטוס כרגע.</b>\n\nנסה שוב בעוד כמה דקות.")

# ====================
# POLLING LOOP
# ====================
def poll_updates():
    """לולאת קבלת עדכונים מהטלגרם"""
    logger.info("🤖 TON Airdrop Bot (Username) מתחיל...")
    
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
                        user_name = message["chat"].get("first_name", "משתמש")
                        username = message["chat"].get("username", "")
                        
                        # טיפול בפקודות
                        if text == "/start":
                            handle_start(chat_id, user_name, username)
                        
                        elif text == "/status":
                            handle_status(chat_id)
                        
                        elif text == "/help":
                            handle_start(chat_id, user_name, username)
                        
                        else:
                            # בדוק לפי המצב הנוכחי
                            state = get_user_state(chat_id)
                            
                            if state == "waiting_for_username":
                                handle_username(chat_id, text)
                            
                            elif state == "waiting_for_payment":
                                # מניחים שזה מספר עסקה אם זה ארוך מספיק
                                if len(text) > 20:
                                    handle_payment(chat_id, text)
                                else:
                                    send_message(chat_id, "❌ <b>מספר עסקה לא תקין.</b>\n\nאנא שלח את מספר העסקה המלא שקיבלת.")
                            
                            else:
                                # מצב לא ידוע - בקש username
                                set_user_state(chat_id, "waiting_for_username")
                                send_message(chat_id, f"🤖 <b>שלום {user_name}!</b>\n\nשלח את שם המשתמש הטלגרם שלך כדי להתחיל.")
            
        except Exception as e:
            logger.error(f"Polling error: {e}")
            import time
            time.sleep(5)

# ====================
# MAIN
# ====================
if __name__ == "__main__":
    poll_updates()
