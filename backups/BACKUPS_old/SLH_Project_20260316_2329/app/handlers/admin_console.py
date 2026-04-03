from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.admin_guard import is_admin

router = Router()


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Orders", callback_data="admin:orders")],
            [InlineKeyboardButton(text="Payments Queue", callback_data="admin:payments")],
            [InlineKeyboardButton(text="Products", callback_data="admin:products")],
            [InlineKeyboardButton(text="System", callback_data="admin:system")],
            [InlineKeyboardButton(text="Logs", callback_data="admin:logs")],
        ]
    )


@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        await message.answer("Forbidden")
        return

    await message.answer(
        "SLH Admin Console",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: types.CallbackQuery):
    await callback.message.answer("/purchase_queue")


@router.callback_query(F.data == "admin:payments")
async def admin_payments(callback: types.CallbackQuery):
    await callback.message.answer("/purchase_queue")


@router.callback_query(F.data == "admin:products")
async def admin_products(callback: types.CallbackQuery):
    await callback.message.answer("/list_products")


@router.callback_query(F.data == "admin:system")
async def admin_system(callback: types.CallbackQuery):
    await callback.message.answer("/admin_inventory")


@router.callback_query(F.data == "admin:logs")
async def admin_logs(callback: types.CallbackQuery):
    await callback.message.answer("Logs feature coming soon")