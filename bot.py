import os
from telegram.ext import Application, CommandHandler

BOT_TOKEN = "8724910039:AAFkZYO_fV5VFdDpzszWHfhYvJRO25b1fDg"

async def start(update, context):
    await update.message.reply_text("🤖 SLH Macro Bot is alive!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
