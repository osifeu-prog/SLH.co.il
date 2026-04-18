import telebot
import os
import sys
import traceback

sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from merchant_sandbox.handlers import register_merchant_handlers
except ImportError:
    print(f"DEBUG: Import Error! Path: {sys.path}")
    traceback.print_exc()
    sys.exit(1)

TOKEN = "8172123240:AAEmf0TXCvuDXXfG-Kfb5n3S_C8brQ29L6c"
bot = telebot.TeleBot(TOKEN)

print("--- DEBUG MODE ACTIVE ---")

try:
    register_merchant_handlers(bot)
    print("Handlers registered. Starting polling...")
    bot.polling(non_stop=True, interval=0, timeout=20)
except Exception as e:
    print("\n[!!!] CRASH DETECTED:")
    traceback.print_exc()

