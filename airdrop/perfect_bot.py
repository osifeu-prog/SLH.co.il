#!/usr/bin/env python3
"""
SLH Airdrop Bot - גרסה פשוטה, יציבה ומושלמת
"""

import logging
import requests
import time
import sys
import io
from datetime import datetime

# ====================
# CONFIGURATION - יש לעדכן!
# ====================
TOKEN = "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls"
API_URL = "https://successful-fulfillment-production.up.railway.app"  # לשנות ל-URL של Railway אחרי העלאה
ADMIN_ID = "7757102350"
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"

# ====================
# SETUP
# ====================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    format='%(asctime)s - SLH BOT - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================
# HELPER FUNCTIONS
# ====================
def send_message(chat_id, text, parse_mode="HTML"):
    """שולח הודעה לטלגרם"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def call_api(endpoint, method="GET", data=None):
    """קורא ל-API"""
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"API connection error: {e}")
        return None

def create_menu_keyboard():
    """יוצר מקלדת תפריט"""
    return {
        "keyboard": [
            ["🚀 התחל תהליך"],
            ["📊 סטטוס אישי", "🎁 בונוסים"],
            ["🔗 קישור הפניה", "🏆 טבלת מובילים"],
            ["ℹ️ מידע", "⚙️ הגדרות"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ====================
# MESSAGE TEMPLATES
# ====================
def get_welcome_message(name):
    return f"""
🚀 <b>ברוך הבא ל-SLH Airdrop System!</b>

👤 <b>משתמש:</b> {name}

🎁 <b>מבצע השקה בלעדי:</b>
• 1,000 טוקני SLH = 44.4 ₪ בלבד!
• קבלה אוטומטית תוך 24 שעות
• תמיכה טכנית 24/7

📈 <b>מדוע להשקיע עכשיו?</b>
הטוקנים יאפשרו גישה לפלטפורמת בחירת מומחים מבוזרת
וייסחרו בבורסות המובילות בעתיד.

<b>לחץ על '🚀 התחל תהליך' למטה!</b>
"""

def get_payment_instructions(chat_id):
    return f"""
✅ <b>הוראות תשלום</b>

🏦 <b>ארנק TON שלנו:</b>
<code>{TON_WALLET}</code>

📋 <b>שלבי התשלום:</b>
1. שלח בדיוק <b>44.4 TON</b> לכתובת למעלה
2. בתיאור התשלום כתוב: <code>Airdrop-{chat_id}</code>
3. שמור את מספר העסקה (Transaction Hash)
4. שלח את מספר העסקה לכאן

⚠️ <b>חשוב:</b>
• שלח בדיוק 44.4 TON
• הקפד על התיאור עם המזהה שלך
• זמן אספקה: עד 24 שעות

<b>שאלות?</b> @Osif83
"""

# ====================
# BOT LOGIC
# ====================
class AirdropBot:
    def __init__(self):
        self.user_states = {}
    
    def handle_start(self, chat_id, name, username=""):
        """מטפל בפקודת /start"""
        # רישום משתמש
        user_data = {
            "telegram_id": str(chat_id),
            "username": username,
            "first_name": name
        }
        
        # נסה לרשום את המשתמש ב-API
        api_result = call_api("/api/register", "POST", user_data)
        
        # שלח הודעת ברוכים הבאים
        send_message(chat_id, get_welcome_message(name))
        
        time.sleep(1)
        
        # שלח תפריט
        menu = create_menu_keyboard()
        send_message(chat_id, "👇 <b>בחר אפשרות מהתפריט:</b>", reply_markup=menu)
        
        # עדכן מצב משתמש
        self.user_states[chat_id] = "main_menu"
        
        # שלח התראה למנהל
        if api_result and api_result.get("status") == "success":
            admin_msg = f"👤 משתמש חדש: {name} (@{username})"
            send_message(ADMIN_ID, admin_msg)
        
        logger.info(f"User {name} (@{username}) started the bot")
    
    def handle_menu(self, chat_id, text, name):
        """מטפל בבחירת תפריט"""
        if text == "🚀 התחל תהליך":
            self.user_states[chat_id] = "awaiting_username"
            send_message(chat_id, "👤 <b>שלב ראשון:</b>\n\nשלח לי את שם המשתמש הטלגרם שלך (לדוגמה: @username)")
        
        elif text == "📊 סטטוס אישי":
            self.show_status(chat_id, name)
        
        elif text == "🎁 בונוסים":
            send_message(chat_id, "🎁 <b>מערכת הבונוסים:</b>\n\n• 50 טוקנים על כל חבר שמצטרף\n• 30 טוקנים על שיתוף בפייסבוק\n• 10% תוספת ל-100 הראשונים!")
        
        elif text == "🔗 קישור הפניה":
            link = f"https://t.me/SLH_AIR_bot?start=ref{chat_id}"
            send_message(chat_id, f"🔗 <b>קישור הפניה שלך:</b>\n\n{link}\n\nהזמן חברים וקבל בונוסים!")
        
        elif text == "🏆 טבלת מובילים":
            send_message(chat_id, "🏆 <b>טבלת מובילים:</b>\n\n1. @User1 - 15 הפניות\n2. @User2 - 12 הפניות\n3. @User3 - 8 הפניות\n\n🔥 רוצה להיות מוביל? הזמן עוד חברים!")
        
        elif text == "ℹ️ מידע":
            send_message(chat_id, "ℹ️ <b>מידע על SLH:</b>\n\nפרויקט בלוקצ'יין ישראלי לפלטפורמת בחירת מומחים מבוזרת. הטוקנים יאפשרו גישה לשירותים מתקדמים וזכות הצבעה על פיתוח המערכת.")
        
        elif text == "⚙️ הגדרות":
            send_message(chat_id, "⚙️ <b>הגדרות:</b>\n\nשפה: עברית\nמטבע: ILS (₪)\nאזור זמן: ישראל\nהתראות: פעילות")
    
    def handle_username(self, chat_id, username, name):
        """מטפל בקבלת username"""
        username = username.replace('@', '').strip()
        
        if len(username) < 3:
            send_message(chat_id, "❌ <b>שם משתמש לא תקין.</b>\n\nאנא שלח username תקין (לפחות 3 תווים).")
            return False
        
        send_message(chat_id, get_payment_instructions(chat_id))
        self.user_states[chat_id] = "awaiting_payment"
        return True
    
    def handle_transaction(self, chat_id, tx_hash, name):
        """מטפל בקבלת transaction hash"""
        if len(tx_hash) < 30:
            send_message(chat_id, "❌ <b>מספר עסקה לא תקין.</b>\n\nאנא שלח את מספר העסקה המלא (לפחות 30 תווים).")
            return False
        
        # שמור את העסקה ב-API
        tx_data = {
            "telegram_id": str(chat_id),
            "transaction_hash": tx_hash,
            "amount": 44.4
        }
        
        result = call_api("/api/submit", "POST", tx_data)
        
        if result and result.get("status") == "success":
            # הודעה למשתמש
            success_msg = f"""
✅ <b>תשלום התקבל!</b>

👤 <b>משתמש:</b> {name}
🔢 <b>עסקה:</b> {tx_hash[:20]}...
💰 <b>סכום:</b> 44.4 TON
🎁 <b>טוקנים:</b> 1,000 SLH
⏳ <b>סטטוס:</b> ממתין לאישור מנהל
📅 <b>זמן אספקה:</b> עד 24 שעות

📊 <b>למעקב:</b> שלח /status בכל עת
"""
            send_message(chat_id, success_msg)
            
            # התראה למנהל
            admin_msg = f"""
🔔 <b>תשלום חדש!</b>

👤 משתמש: {name}
🆔 מזהה: {chat_id}
💳 עסקה: {tx_hash[:20]}...
💰 סכום: 44.4 TON
🕐 זמן: {datetime.now().strftime('%H:%M:%S')}

🌐 <b>פאנל ניהול:</b>
/admin/dashboard?admin_key=airdrop_admin_2026
"""
            send_message(ADMIN_ID, admin_msg)
            
            self.user_states[chat_id] = "completed"
            return True
        else:
            send_message(chat_id, "❌ <b>שגיאה בשמירת העסקה.</b>\n\nאנא נסה שוב או פנה לתמיכה: @Osif83")
            return False
    
    def show_status(self, chat_id, name):
        """מציג סטטוס משתמש"""
        result = call_api(f"/api/user/{chat_id}")
        
        if result and "user" in result:
            user = result["user"]
            tokens = user.get("tokens", 0)
            value = tokens * 44.4 / 1000
            
            status_msg = f"""
📊 <b>סטטוס אישי</b>

👤 <b>משתמש:</b> {name}
🆔 <b>מזהה:</b> {chat_id}
🪙 <b>טוקנים:</b> {tokens:,} SLH
💰 <b>שווי משוער:</b> {value:,.1f} ₪
📅 <b>נרשם:</b> {user.get('registered_at', 'לא ידוע')}

📈 <b>עסקאות אחרונות:</b>
"""
            
            if result.get("transactions"):
                for tx in result["transactions"][:3]:  # 3 עסקאות אחרונות
                    status_msg += f"• {tx['status']}: {tx['amount']} TON\n"
            else:
                status_msg += "אין עסקאות עדיין"
            
            send_message(chat_id, status_msg)
        else:
            send_message(chat_id, "ℹ️ <b>עדיין לא רכשת טוקנים.</b>\n\nלחץ על '🚀 התחל תהליך' כדי להתחיל!")

# ====================
# MAIN BOT LOOP
# ====================
def main():
    """לולאת הבוט הראשית"""
    bot = AirdropBot()
    offset = 0
    
    logger.info("=" * 50)
    logger.info("🤖 SLH Airdrop Bot - גרסה יציבה")
    logger.info(f"📞 בוט: @SLH_AIR_bot")
    logger.info(f"🌐 API: {API_URL}")
    logger.info("=" * 50)
    
    while True:
        try:
            # קבל עדכונים מטלגרם
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
                        name = msg["chat"].get("first_name", "משתמש")
                        username = msg["chat"].get("username", "")
                        
                        logger.info(f"📨 {name}: {text}")
                        
                        # טיפול בפקודות מיוחדות
                        if text == "/start":
                            bot.handle_start(chat_id, name, username)
                        
                        elif text == "/status":
                            bot.show_status(chat_id, name)
                        
                        elif text == "/help":
                            send_message(chat_id, "ℹ️ <b>עזרה:</b>\n\n/start - התחל\n/status - סטטוס\n/wallet - ארנק\n/help - עזרה זו")
                        
                        elif text == "/wallet":
                            send_message(chat_id, f"🏦 <b>ארנק TON:</b>\n\n<code>{TON_WALLET}</code>\n\nשלח 44.4 TON לכתובת זו.")
                        
                        else:
                            # בדוק מצב נוכחי
                            state = bot.user_states.get(chat_id, "main_menu")
                            
                            if state == "awaiting_username":
                                bot.handle_username(chat_id, text, name)
                            
                            elif state == "awaiting_payment":
                                if len(text) > 30:  # סביר שזה hash עסקה
                                    bot.handle_transaction(chat_id, text, name)
                                else:
                                    # בדוק אם זה בחירת תפריט
                                    menu_options = ["🚀", "📊", "🎁", "🔗", "🏆", "ℹ️", "⚙️"]
                                    if any(opt in text for opt in menu_options):
                                        bot.handle_menu(chat_id, text, name)
                                    else:
                                        send_message(chat_id, "❓ <b>לא הבנתי.</b>\n\nאנא שלח את מספר העסקה המלא או בחר מהתפריט.")
                            
                            else:
                                # אם זה בחירת תפריט
                                menu_options = ["🚀", "📊", "🎁", "🔗", "🏆", "ℹ️", "⚙️"]
                                if any(opt in text for opt in menu_options):
                                    bot.handle_menu(chat_id, text, name)
                                elif text.startswith("/"):
                                    send_message(chat_id, "❓ <b>פקודה לא מוכרת.</b>\n\nלחץ /start להתחיל מחדש.")
                                else:
                                    # החזר לתפריט
                                    menu = create_menu_keyboard()
                                    send_message(chat_id, "👇 <b>בחר אפשרות מהתפריט:</b>", reply_markup=menu)
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"🔥 שגיאה בלולאה ראשית: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

