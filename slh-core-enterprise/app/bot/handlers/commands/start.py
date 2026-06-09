from aiogram import types
from app.services.user_service import UserService

async def start_handler(msg: types.Message):
    await UserService.create_or_update(
        msg.from_user.id,
        msg.from_user.username or "user"
    )

    await msg.answer("CORE SYSTEM ONLINE")