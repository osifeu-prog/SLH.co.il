#!/usr/bin/env python3
"""
TON Airdrop Bot - Stable Version
מונע conflicts ומנהל סטטיסטיקות
"""
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
API_URL = os.getenv("API_URL", "https://successful-fulfillment-production.up.railway.app")
ADMIN_KEY = os.getenv("ADMIN_KEY", "test123")
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"

# Track active users to prevent duplicate registrations
active_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ברוכים הבא - רישום משתמש"""
    user = update.effective_user
    
    if user.id in active_users:
        await update.message.reply_text("👋 כבר נרשמת! השתמש ב-/airdrop כדי לבקש airdrop.")
        return
    
    # רישום משתמש חדש
    try:
        user_data = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        
        response = requests.post(f"{API_URL}/api/register", json=user_data, timeout=5)
        
        if response.status_code == 200:
            active_users.add(user.id)
            logger.info(f"✅ User registered: {user.id}")
            
                        welcome = f"""🎉 ברוך הבא {user.first_name}!

🤖 בוט ה-Airdrop של TON מוכן לשירותך!

💰 מחיר Airdrop: 44.4 ₪ (ב-TON)
🎯 כמות טוקנים: 1000 למשתמש

📋 פקודות זמינות:
/airdrop - בקשת airdrop חדשה
/status - מצב משתמש
/help - עזרה והסברים

💼 ארנק לתשלום:
{TON_WALLET}

⚡ המערכת פעילה ומוכנה!"""
            
            await update.message.reply_text(welcome)
            
        else:
            await update.message.reply_text("⚠️ בעיה בשרת. נסה שוב בעוד דקה.")
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await update.message.reply_text("🔧 המערכת מתעדכנת כרגע. נסה שוב תוך 5 דקות.")

async def airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """יצירת airdrop עם QR"""
    user = update.effective_user
    
    if user.id not in active_users:
        await update.message.reply_text("⚠️ אנא הקש /start תחילה לרישום.")
        return
    
    await update.message.reply_text("🔄 *מכין לך airdrop חדש...*", parse_mode="Markdown")
    
    try:
        airdrop_data = {"user_id": user.id}
        response = requests.post(f"{API_URL}/api/airdrop", json=airdrop_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()["airdrop"]
            
            payment_msg = f"""🎁 **AIRDROP מוכן לתשלום!**

🔢 *מספר עסקה:* `{data['id']}`
💰 *סכום:* {data['price']} TON (44.4 ₪)
⏰ *תוקף:* שעה אחת

🏦 *ארנק TON:*
`{data['wallet']}`

📲 *קישור תשלום:*
{data['payment_url']}

📸 *הוראות:*
1. שלח {data['price']} TON לארנק למעלה
2. שמור את מספר העסקה: `{data['id']}`
3. שלח צילום תשלום למנהל

⚡ *התשלום מאומת ידנית תוך 24 שעות*"""
            
            await update.message.reply_text(payment_msg, parse_mode="Markdown")
            
            # שלח QR code
            await update.message.reply_photo(data["qr_code"])
            
            logger.info(f"✅ Airdrop created for {user.id}: {data['id']}")
            
        else:
            await update.message.reply_text("❌ לא ניתן ליצור airdrop כרגע. נסה שוב מאוחר יותר.")
            
    except Exception as e:
        logger.error(f"Airdrop error: {e}")
        await update.message.reply_text("⚠️ שגיאה בשרת. המערכת תשוב בקרוב.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """בדיקת סטטוס משתמש"""
    user = update.effective_user
    
    try:
        response = requests.get(f"{API_URL}/api/user/{user.id}", timeout=5)
        
        if response.status_code == 200:
            user_data = response.json()
            
            if user_data.get("status") == "user_not_found":
                await update.message.reply_text("📝 עדיין לא נרשמת. הקש /start להתחיל.")
                return
            
            status_msg = f"""📊 *סטטוס משתמש*

👤 שם: {user_data.get('first_name', 'משתמש')}
🆔 ID: {user_data.get('id')}
💰 יתרה: {user_data.get('balance', 0)} טוקנים

📈 Airdrops שביצעת: {len(user_data.get('airdrops', []))}
⏳ ממתינים לאימות: {len([a for a in user_data.get('airdrops', []) if a.get('status') == 'pending'])}

💡 לבדיקת airdrops ספציפיים, פנה למנהל עם מספר העסקה."""
            
            await update.message.reply_text(status_msg, parse_mode="Markdown")
            
        else:
            await update.message.reply_text("📡 לא ניתן לטעון נתונים כרגע.")
            
    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text("🔧 שגיאה זמנית בשרת.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הוראות ושירות"""
    help_text = """🆘 *מדריך שימוש מהיר*

1. *הרשמה:* הקש /start
2. *בקשת Airdrop:* הקש /airdrop
3. *בדיקת סטטוס:* הקש /status

💳 *תהליך תשלום:*
• בקשת airdrop → קבלת מספר עסקה
• תשלום TON לארנק → שמירת hash עסקה
• שליחת אישור למנהל → קבלת טוקנים

⏱️ *זמני מענה:*
• אישור תשלום: עד 24 שעות
• קבלת טוקנים: מיידי לאחר אישור

📞 *תמיכה:* @Osif83 (מנהל הפרויקט)

⚡ *המערכת בתקופת הרצה - תודה על הסבלנות!*"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """סטטיסטיקות מערכת (למנהל בלבד)"""
    user = update.effective_user
    
    # בדיקת מנהל (תחליף ל-ID האמיתי שלך)
    if str(user.id) != "7757102350":  # החלף ב-ID האמיתי שלך
        await update.message.reply_text("⚠️ פקודה זו זמינה למנהל בלבד.")
        return
    
    try:
        response = requests.get(f"{API_URL}/admin/stats?admin_key={ADMIN_KEY}", timeout=5)
        
        if response.status_code == 200:
            stats_data = response.json()
            
            stats_msg = f"""📈 *סטטיסטיקות מערכת - מנהל*

👥 משתמשים: {stats_data['statistics']['total_users']}
🎯 Airdrops: {stats_data['statistics']['total_airdrops']}
⏳ ממתינים: {stats_data['statistics']['pending_payments']}
✅ הושלמו: {stats_data['statistics']['completed_payments']}
💰 נפח: {stats_data['statistics']['total_volume_ton']} TON

🕒 עדכון אחרון: {stats_data['timestamp'][11:16]}
            
👤 משתמשים אחרונים: {len(stats_data.get('recent_users', []))}"""
            
            await update.message.reply_text(stats_msg, parse_mode="Markdown")
            
            # שליחת נתונים גולמיים למנהל
            await update.message.reply_text(
                f"📋 נתונים מלאים:\n{json.dumps(stats_data, indent=2, ensure_ascii=False)}"
            )
            
        else:
            await update.message.reply_text("❌ לא ניתן לטעון סטטיסטיקות.")
            
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text("🔧 שגיאה בטעינת סטטיסטיקות.")

def main():
    """הפעלת הבוט - גרסה יציבה"""
    print("🚀 Starting TON Airdrop Bot...")
    print(f"🔗 API: {API_URL}")
    print(f"👑 Admin ID: 7757102350")
    
    # נקה webhooks קודמים
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        print("✅ Cleared previous webhooks")
    except:
        print("⚠️ No webhooks to clear")
    
    # בניית אפליקציה
    app = Application.builder().token(TOKEN).build()
    
    # הוספת פקודות
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("airdrop", airdrop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))  # למנהל בלבד
    
    # הפעלה
    print("🤖 Bot is running and ready!")
    print("📊 Use /stats for admin statistics")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import json
    main()



