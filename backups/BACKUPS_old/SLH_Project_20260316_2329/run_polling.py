import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

@dp.message()
async def log_all_messages(message: types.Message):
    logging.info(f'?????? ????? ?-{message.from_user.id}: {message.text}')
    await message.answer('?????? ?? ?????? ???!')

async def main():
    print('\x1b[32m[*] Bot is running and logging all traffic...\x1b[0m')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
