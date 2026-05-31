import os, psycopg2, requests
from dotenv import load_dotenv
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_id = int(os.getenv("ADMIN_ID", "0"))
def check_health():
    issues = []
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
    except:
        issues.append("Database connection failed")
    try:
        r = requests.get("https://api.telegram.org/bot" + bot_token + "/getMe", timeout=5)
        if r.status_code != 200:
            issues.append("Telegram bot token invalid")
    except:
        issues.append("Telegram API unreachable")
    return issues
if __name__ == "__main__":
    problems = check_health()
    if problems:
        import asyncio
        from aiogram import Bot
        bot = Bot(token=bot_token)
        asyncio.run(bot.send_message(admin_id, "?? Health alert:\n" + "\n".join(problems)))
