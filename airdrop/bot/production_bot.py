#!/usr/bin/env python3
"""
TON Airdrop Bot - Production Version
מחובר ל-API ב-Railway
"""

import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ====================
# CONFIGURATION
# ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
API_URL = os.getenv("API_URL", "https://successful-fulfillment-production.up.railway.app")
API_KEY = os.getenv("API_KEY", "bot_api_key_123_secret_456")

# ====================
# LOGGING
# ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====================
# API CLIENT
# ====================
class APIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
        logger.info(f"API Client initialized with URL: {base_url}")
    
    async def register_user(self, user_id: int, username: str) -> dict:
        """רושם משתמש חדש בפאנל"""
        url = f"{self.base_url}/api/users/register"
        data = {
            "telegram_id": str(user_id),
            "username": username or f"user_{user_id}",
            "joined_at": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"User {user_id} registered successfully")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to register user {user_id}: {response.status} - {error_text}")
                        return {"error": f"Registration failed: {response.status}"}
        except Exception as e:
            logger.error(f"Exception registering user {user_id}: {e}")
            return {"error": f"Exception: {str(e)}"}
    
    async def check_eligibility(self, user_id: int) -> dict:
        """בודק זכאות למשתמש"""
        url = f"{self.base_url}/api/airdrop/check/{user_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Eligibility check for {user_id}: {result}")
                        return result
                    else:
                        logger.warning(f"Eligibility check failed for {user_id}: {response.status}")
                        return {"eligible": False, "reason": "System busy, try again"}
        except Exception as e:
            logger.error(f"Exception checking eligibility: {e}")
            return {"eligible": False, "reason": "System error"}
    
    async def submit_wallet(self, user_id: int, wallet_address: str) -> dict:
        """שולח ארנק TON לשרת"""
        url = f"{self.base_url}/api/users/submit_wallet"
        data = {
            "telegram_id": str(user_id),
            "wallet_address": wallet_address,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Wallet submitted for user {user_id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Wallet submission failed: {response.status} - {error_text}")
                        return {"error": "Failed to save wallet"}
        except Exception as e:
            logger.error(f"Exception submitting wallet: {e}")
            return {"error": f"Exception: {str(e)}"}

# ====================
# BOT HANDLERS
# ====================
api_client = APIClient(API_URL, API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /start"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # רישום המשתמש
    result = await api_client.register_user(user.id, user.username or user.first_name)
    
    if "error" not in result:
        welcome_text = f"""
🎉 **ברוך הבא ל-TON Airdrop Bot!**

👤 **משתמש:** {user.first_name}
🆔 **ID:** {user.id}
✅ **רישום:** הצלח!

📋 **הוראות:**
1. שלח את כתובת ארנק ה-TON שלך
2. המתן לאימות
3. קבל את הטוקנים שלך!

💰 **פרס:** עד 10 TON למשתמש
⏰ **זמן אספקה:** עד 24 שעות

🚀 **להתחיל:** שלח את כתובת הארנק שלך עכשיו!
        """
    else:
        welcome_text = f"""
❌ **שגיאה בהרשמה**

סיבה: {result.get('error', 'Unknown error')}

נסה שוב בעוד כמה דקות.
        """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בכתובת ארנק"""
    user = update.effective_user
    wallet_address = update.message.text.strip()
    
    # בדיקה בסיסית של כתובת TON
    if not (wallet_address.startswith(("UQ", "EQ", "0Q")) and len(wallet_address) > 20):
        await update.message.reply_text("""
❌ **כתובת ארנק לא תקינה**

אנא שלח כתובת TON תקינה שתחל ב:
- UQ...
- EQ... 
- 0Q...

⚠️ **דוגמה:** UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        """)
        return
    
    # הודעה על עיבוד
    processing_msg = await update.message.reply_text("🔍 **מעבד את בקשתך...**")
    
    # שליחת הארנק לשרת
    result = await api_client.submit_wallet(user.id, wallet_address)
    
    if "error" not in result:
        # בדיקת זכאות
        eligibility = await api_client.check_eligibility(user.id)
        
        if eligibility.get("eligible", False):
            response_text = f"""
✅ **ארנק התקבל בהצלחה!**

📝 **פרטים:**
• **כתובת:** `{wallet_address[:20]}...`
• **סטטוס:** מאושר
• **זכאות:** ✅ מאושר

💰 **הטוקנים ישלחו בתוך 24 שעות.**

📊 **מעקב:** השתמש ב-/status כדי לעקוב
            """
        else:
            reason = eligibility.get("reason", "סיבה לא ידועה")
            response_text = f"""
❌ **אינך זכאי ל-airdrop**

**סיבה:** {reason}

📞 **תמיכה:** פנה למנהל המערכת
            """
    else:
        response_text = f"""
❌ **שגיאה בשמירת הארנק**

**סיבה:** {result.get('error', 'Unknown error')}

נסה שוב בעוד כמה דקות.
        """
    
    # עדכון ההודעה הקודמת
    await processing_msg.edit_text(response_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /help"""
    help_text = """
🤖 **TON Airdrop Bot - עזרה**

**פקודות זמינות:**
/start - התחל את הבוט
/help - הצג הודעה זו  
/status - בדוק סטטוס משתמש

**📝 הוראות:**
1. שלח את כתובת ארנק ה-TON שלך
2. המתן לאימות
3. קבל את הטוקנים ישירות לארנק

**⚠️ הערות:**
• כל משתמש יכול לקבל airdrop פעם אחת בלבד
• נדרשת כתובת TON תקינה
• התהליך אוטומטי לחלוטין

**📞 תמיכה:**
@SupportUsername
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /status - בדיקת סטטוס"""
    user = update.effective_user
    eligibility = await api_client.check_eligibility(user.id)
    
    if eligibility.get("eligible", False):
        status_text = """
✅ **אתה זכאי ל-airdrop!**

**השלב הבא:** שלח את כתובת הארנק שלך.

💰 **פרס:** עד 10 TON
⏰ **זמן:** עד 24 שעות
        """
    else:
        reason = eligibility.get("reason", "טרם נבדק")
        status_text = f"""
❌ **אינך זכאי כרגע**

**סיבה:** {reason}

**📞 תמיכה:** @SupportUsername
        """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /stats - סטטיסטיקות"""
    stats_text = """
📊 **סטטיסטיקות מערכת:**

• **משתמשים רשומים:** 0
• **ארנקים שקיבלו:** 0  
• **סה"כ TON שחולק:** 0
• **יתרה:** 1000 TON

**🚀 Beta Test פעיל!**
    """
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# ====================
# MAIN
# ====================
def main():
    """הפונקציה הראשית"""
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN לא הוגדר!")
        return
    
    logger.info(f"Starting bot with API URL: {API_URL}")
    
    # יצירת אפליקציית הבוט
    application = Application.builder().token(TOKEN).build()
    
    # הוספת handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_handler))
    
    # הרצת הבוט
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
