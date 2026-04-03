import asyncio
from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    await bot.delete_webhook(drop_pending_updates=True)
    print('\x1b[32m[+] Webhook deleted successfully! You can now run the bot.\x1b[0m')
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
