import os, asyncio, psycopg2
from dotenv import load_dotenv
from aiogram import Bot
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = Bot(token=TOKEN)

async def send_daily_report():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='purchase' AND type='debit' AND created_at > NOW() - INTERVAL '1 day'")
    revenue = cur.fetchone()[0]
    conn.close()
    text = f"?? *Daily SLH Report*  {os.getenv('DATE', 'Today')}\n\n? Check-ins today: {checked}/{total}\n?? Revenue (24h): ${revenue:.2f}\n\n?? /start to engage!"
    await bot.send_message(ADMIN_ID, text, parse_mode="MarkdownV2")
    # Also broadcast to all groups? Optional  add group IDs here
    # for group in GROUP_IDS:
    #     await bot.send_message(group, text)

if __name__ == "__main__":
    asyncio.run(send_daily_report())
