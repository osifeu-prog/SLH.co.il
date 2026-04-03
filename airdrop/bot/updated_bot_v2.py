#!/usr/bin/env python3
"""
TON Airdrop Bot - Connected to Management Panel
גרסה מחוברת לפאנל הניהול החדש
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
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "bot_api_key_123")

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
    
    async def register_user(self, user_id: int, username: str) -> dict:
        """רושם משתמש חדש בפאנל"""
        url = f"{self.base_url}/api/users/register"
        data = {
            "telegram_id": str(user_id),
            "username": username,
            "joined_at": datetime.utcnow().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to register user: {response.status}")
                    return {"error": "Registration failed"}
    
    async def check_eligibility(self, user_id: int) -> dict:
        """בודק זכאות למשתמש"""
        url = f"{self.base_url}/api/airdrop/eligibility/{user_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to check eligibility: {response.status}")
                    return {"eligible": False, "reason": "API error"}
    
    async def submit_wallet(self, user_id: int, wallet_address: str) -> dict:
        """שולח ארנק TON לשרת"""
        url = f"{self.base_url}/api/users/wallet"
        data = {
            "telegram_id": str(user_id),
            "wallet_address": wallet_address
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to submit wallet: {response.status}")
                    return {"error": "Failed to save wallet"}

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
🎉 ברוך הבא ל-TON Airdrop Bot!

👤 משתמש: {user.first_name}
🆔 ID: {user.id}

📋 הוראות:
1. שלח את כתובת ארנק ה-TON שלך
2. המתן לאימות
3. קבל את הטוקנים שלך!

💰 הפרס: עד 100 TON למשתמש
        """
    else:
        welcome_text = "❌ שגיאה בהרשמה. נסה שוב מאוחר יותר."
    
    await update.message.reply_text(welcome_text)

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בכתובת ארנק"""
    user = update.effective_user
    wallet_address = update.message.text.strip()
    
    # בדיקה בסיסית של כתובת TON
    if not wallet_address.startswith(("UQ", "EQ", "0Q")):
        await update.message.reply_text("❌ כתובת ארנק לא תקינה. אנא שלח כתובת TON תקינה.")
        return
    
    # שליחת הארנק לשרת
    result = await api_client.submit_wallet(user.id, wallet_address)
    
    if "error" not in result:
        # בדיקת זכאות
        eligibility = await api_client.check_eligibility(user.id)
        
        if eligibility.get("eligible", False):
            response_text = f"""
✅ ארנק התקבל בהצלחה!

📝 פרטים:
• כתובת: {wallet_address[:20]}...
• סטטוס: מאושר
• זכאות: ✅ מאושר

💰 הטוקנים ישלחו בתוך 24 שעות.
            """
        else:
            reason = eligibility.get("reason", "סיבה לא ידועה")
            response_text = f"❌ אינך זכאי ל-airdrop. סיבה: {reason}"
    else:
        response_text = "❌ שגיאה בשמירת הארנק. נסה שוב מאוחר יותר."
    
    await update.message.reply_text(response_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /help"""
    help_text = """
🤖 TON Airdrop Bot - עזרה

פקודות זמינות:
/start - התחל את הבוט
/help - הצג הודעה זו
/status - בדוק סטטוס משתמש

📝 הוראות:
1. שלח את כתובת ארנק ה-TON שלך
2. המתן לאימות
3. קבל את הטוקנים ישירות לארנק

⚠️ הערות:
• כל משתמש יכול לקבל airdrop פעם אחת בלבד
• נדרשת כתובת TON תקינה
• התהליך אוטומטי לחלוטין
    """
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת /status - בדיקת סטטוס"""
    user = update.effective_user
    eligibility = await api_client.check_eligibility(user.id)
    
    if eligibility.get("eligible", False):
        status_text = "✅ אתה זכאי ל-airdrop! שלח את כתובת הארנק שלך."
    else:
        reason = eligibility.get("reason", "טרם נבדק")
        status_text = f"❌ אינך זכאי כרגע. סיבה: {reason}"
    
    await update.message.reply_text(status_text)

# ====================
# MAIN
# ====================
def main():
    """הפונקציה הראשית"""
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN לא הוגדר!")
        return
    
    # יצירת אפליקציית הבוט
    application = Application.builder().token(TOKEN).build()
    
    # הוספת handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_handler))
    
    # הרצת הבוט
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
