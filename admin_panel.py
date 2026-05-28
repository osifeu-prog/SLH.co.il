# admin_panel.py - Clean English version
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Hello Osif 👋\n"
        "I am SLH Claude - your AI assistant.\n"
        "💎 Tier: free\n\n"
        "Available commands:\n"
        "/dashboard - System status\n"
        "/crowdfunding - Support the project\n"
        "/points - Your points\n"
        "/daily - Daily missions\n"
        "/backup - Create backup\n"
        "/help - Full command list"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Commands:\n"
        "/dashboard\n"
        "/crowdfunding\n"
        "/points\n"
        "/daily\n"
        "/backup\n"
        "/help"
    )
