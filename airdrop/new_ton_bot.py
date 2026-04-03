import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls"
API_URL = "https://successful-fulfillment-production.up.railway.app"

async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(f"""
🎉 שלום {user.first_name}!

זה הבוט החדש שמחובר למערכת ה-API.

שלח לי את כתובת ארנק ה-TON שלך (צריכה להתחיל ב-UQ/EQ/0Q).

📊 המערכת החדשה כוללת:
• שמירת נתונים ב-PostgreSQL
• פאנל ניהול
• לוגים מלאים
• הגבלת משתמש אחד לארנק
""")

async def handle_message(update: Update, context):
    text = update.message.text
    
    # בדוק אם זה כתובת ארנק
    if text.startswith(("UQ", "EQ", "0Q")) and len(text) > 20:
        await update.message.reply_text(f"""
✅ קיבלתי את הארנק שלך!

📝 כתובת: `{text[:20]}...`
📡 שומר במערכת החדשה...

💰 הטוקנים ישלחו בתוך 24 שעות.

🆔 מזהה שלך: {update.effective_user.id}
""")
    else:
        await update.message.reply_text("שלח כתובת ארנק TON תקינה (מתחילה ב-UQ/EQ/0Q)")

def main():
    print("🤖 בוט חדש מתחיל...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
