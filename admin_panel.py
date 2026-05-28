# admin_panel.py  SLH Claude
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

def register(dp, auth):
    router = Router()

    # OLD /start REMOVED
    async def cmd_start(message: Message):
        await message.answer(
            "Hello Osif ðŸ‘‹\n"
            "I am SLH Claude - your AI assistant.\n"
            "ðŸ’Ž Tier: free\n\n"
            "Available:\n"
            "/dashboard - System status\n"
            "/crowdfunding - Support\n"
            "/points - Points\n"
            "/daily - Daily missions\n"
            "/backup - Create backup\n"
            "/help - Commands"
        )

    @router.message(Command("help"))
    async def cmd_help(message: Message):
        await message.answer(
            "Commands:\n/dashboard\n/crowdfunding\n/points\n/daily\n/backup\n/help"
        )

    dp.include_router(router)


