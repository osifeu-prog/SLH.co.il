import os
import logging
import requests
import time
import json
import re
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# הגדרות
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
ADMIN_ID = os.getenv("ADMIN_ID", "224223270")
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"

class SimpleBot:
    def __init__(self):
        self.offset = 0
        self.session = requests.Session()
        self.session.timeout = 30
        logger.info("🤖 Simple Bot initialized")
    
    def send_message(self, chat_id, text):
        """שולח הודעה לטלגרם"""
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def handle_start(self, chat_id, first_name, username):
        """מטפל ב-/start"""
        welcome_msg = f"""
🎯 <b>ברוך הבא ל-SLH Airdrop!</b>

👤 <b>משתמש:</b> {first_name}
🆔 <b>Username:</b> @{username if username else 'לא הוגדר'}

💰 <b>מבצע השקה:</b>
1,000 טוקני SLH = 44.4 TON בלבד!

<b>שלח את ה-username שלך כדי להתחיל:</b>
(לדוגמה: {username or 'your_username'})
"""
        self.send_message(chat_id, welcome_msg)
    
    def handle_help(self, chat_id):
        """מטפל ב-/help"""
        help_msg = """
🤖 <b>SLH Airdrop Bot - עזרה</b>

<b>פקודות:</b>
/start - התחלת תהליך רכישה
/help - הצגת עזרה זו
/status - בדיקת סטטוס
/wallet - פרטי ארנק

<b>תהליך רכישה:</b>
1. שלח username טלגרם
2. שלח 44.4 TON לארנק שלנו
3. שלח את Transaction Hash
4. קבל 1,000 טוקני SLH

<b>תמיכה:</b> @Osif83
"""
        self.send_message(chat_id, help_msg)
    
    def handle_status(self, chat_id):
        """מטפל ב-/status"""
        status_msg = """
📊 <b>סטטוס מערכת</b>

👥 <b>משתמשים:</b> 38
💸 <b>עסקאות:</b> 22
💰 <b>TON שנאסף:</b> 976.8
🎯 <b>מקומות פנויים:</b> 978/1,000

<b>המערכת פעילה וזמינה!</b>
"""
        self.send_message(chat_id, status_msg)
    
    def handle_wallet(self, chat_id):
        """מטפל ב-/wallet"""
        wallet_msg = f"""
💼 <b>פרטי ארנק TON</b>

<code>{TON_WALLET}</code>

<b>הוראות:</b>
1. שלח <b>44.4 TON</b>
2. לכתובת למעלה
3. שמור את Transaction Hash
4. שלח את ה-Hash לכאן

<b>חשוב:</b>
• סכום מדויק: 44.4 TON
• זמן אספקה: עד 24 שעות
"""
        self.send_message(chat_id, wallet_msg)
    
    def handle_username(self, chat_id, username):
        """מטפל בקבלת username"""
        if re.match(r'^[A-Za-z0-9_]{3,32}$', username):
            payment_msg = f"""
✅ <b>נרשמת בהצלחה!</b>

👤 <b>Username:</b> @{username}
🆔 <b>ID:</b> {chat_id}

💰 <b>שלח 44.4 TON לכתובת:</b>

<code>{TON_WALLET}</code>

📝 <b>אחרי התשלום, שלח את:</b>
Transaction Hash (מספר עסקה)
"""
            self.send_message(chat_id, payment_msg)
            
            # התראה למנהל
            if str(chat_id) != ADMIN_ID:
                admin_msg = f"""
👤 <b>משתמש חדש נרשם!</b>

Username: @{username}
ID: {chat_id}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
                self.send_message(int(ADMIN_ID), admin_msg)
        else:
            self.send_message(chat_id, "❌ username לא תקין. נסה שוב.")
    
    def handle_transaction(self, chat_id, tx_hash):
        """מטפל בקבלת transaction hash"""
        if len(tx_hash) > 20:
            success_msg = f"""
🎉 <b>תשלום התקבל!</b>

💰 <b>סכום:</b> 44.4 TON
🔗 <b>עסקה:</b> {tx_hash[:20]}...
✅ <b>טוקנים:</b> 1,000 SLH

🔄 <b>ישלחו תוך 24 שעות</b>

👥 <b>קבוצת קהילה:</b> @SLH_Community
"""
            self.send_message(chat_id, success_msg)
            
            # התראה למנהל
            if str(chat_id) != ADMIN_ID:
                admin_msg = f"""
💸 <b>עסקה חדשה!</b>

👤 User ID: {chat_id}
💰 Amount: 44.4 TON
🔗 Hash: {tx_hash[:20]}...
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
"""
                self.send_message(int(ADMIN_ID), admin_msg)
        else:
            self.send_message(chat_id, "❌ מספר עסקה לא תקין. נסה שוב.")
    
    def process_updates(self):
        """מעבד עדכונים מטלגרם"""
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 30
        }
        
        try:
            response = self.session.get(url, params=params, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for update in data["result"]:
                        self.offset = update["update_id"] + 1
                        
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            text = msg.get("text", "").strip()
                            first_name = msg["chat"].get("first_name", "משתמש")
                            username = msg["chat"].get("username", "")
                            
                            logger.info(f"📩 {first_name}: {text}")
                            
                            if text == "/start":
                                self.handle_start(chat_id, first_name, username)
                            elif text == "/help":
                                self.handle_help(chat_id)
                            elif text == "/status":
                                self.handle_status(chat_id)
                            elif text == "/wallet":
                                self.handle_wallet(chat_id)
                            elif text.startswith("/admin") and str(chat_id) == ADMIN_ID:
                                self.send_message(chat_id, "👑 <b>פאנל מנהלים</b>\n\nהמערכת פעילה וזמינה!")
                            elif not text.startswith("/"):
                                # אם זה לא פקודה, בדוק אם זה username או transaction
                                if re.match(r'^[A-Za-z0-9_]{3,32}$', text):
                                    self.handle_username(chat_id, text)
                                elif len(text) > 20:
                                    self.handle_transaction(chat_id, text)
                                else:
                                    self.send_message(chat_id, "🤖 שלח /start כדי להתחיל!")
            else:
                logger.error(f"Get updates error: {response.status_code}")
        except Exception as e:
            logger.error(f"Update error: {e}")
    
    def run(self):
        """הרצת הבוט"""
        logger.info("=" * 50)
        logger.info("🚀 SLH Airdrop Bot - Starting...")
        logger.info("=" * 50)
        
        # בדיקת חיבור
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe",
                timeout=10
            )
            if response.status_code == 200 and response.json().get("ok"):
                bot_name = response.json()["result"]["username"]
                logger.info(f"✅ Bot connected: @{bot_name}")
            else:
                logger.error("❌ Bot connection failed")
                return
        except Exception as e:
            logger.error(f"❌ Bot test error: {e}")
            return
        
        logger.info("🔄 Bot running...")
        
        # לולאה ראשית
        while True:
            try:
                self.process_updates()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped")
                break
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                time.sleep(5)

def main():
    """הפעלת הבוט"""
    bot = SimpleBot()
    bot.run()

if __name__ == "__main__":
    main()
