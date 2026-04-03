from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.admin_guard import is_admin
from app.services.purchases_admin import list_purchase_orders_admin, list_products_admin

router = Router()


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Orders", callback_data="adminv2:orders")],
            [InlineKeyboardButton(text="Open Orders", callback_data="adminv2:orders_open")],
            [InlineKeyboardButton(text="Paid Orders", callback_data="adminv2:orders_paid")],
            [InlineKeyboardButton(text="Products", callback_data="adminv2:products")],
            [InlineKeyboardButton(text="Stats", callback_data="adminv2:stats")],
            [InlineKeyboardButton(text="Logs", callback_data="adminv2:logs")],
        ]
    )


def _render_orders(rows: list[dict], title: str) -> str:
    if not rows:
        return f"{title}\n\nNo orders."

    lines = [title, ""]
    for row in rows[:20]:
        ref = row.get("external_payment_ref") or "-"
        lines.append(
            f"#{int(row['id'])} | user={int(row['user_id'])} | "
            f"{row['product_code']} | {float(row['total_amount']):.8f} {row['currency']} | "
            f"{row['status']} | ref={ref}"
        )
    return "\n".join(lines)


def _render_products(rows: list[dict]) -> str:
    if not rows:
        return "Products\n\nNo products."

    lines = ["Products", ""]
    for row in rows[:20]:
        lines.append(
            f"{row['code']} | {row['title']} | "
            f"{row['price_amount']} {row['price_currency']} | "
            f"visible={bool(row['is_visible'])} | active={bool(row['is_active'])}"
        )
    return "\n".join(lines)


@router.message(Command("admin2"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        await message.answer("Forbidden")
        return

    await message.answer("SLH Admin Console V2", reply_markup=admin_menu())


@router.callback_query(F.data == "adminv2:orders")
async def admin_orders(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_purchase_orders_admin(50)
    await callback.answer()
    if callback.message:
        await callback.message.answer(_render_orders(rows, "All Orders"))


@router.callback_query(F.data == "adminv2:orders_open")
async def admin_orders_open(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_purchase_orders_admin(100)
    rows = [r for r in rows if str(r.get("status")) in ("pending_payment", "payment_submitted", "paid")]
    await callback.answer()
    if callback.message:
        await callback.message.answer(_render_orders(rows, "Open Orders"))


@router.callback_query(F.data == "adminv2:orders_paid")
async def admin_orders_paid(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_purchase_orders_admin(100)
    rows = [r for r in rows if str(r.get("status")) == "paid"]
    await callback.answer()
    if callback.message:
        await callback.message.answer(_render_orders(rows, "Paid Orders"))


@router.callback_query(F.data == "adminv2:products")
async def admin_products(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_products_admin(100)
    await callback.answer()
    if callback.message:
        await callback.message.answer(_render_products(rows))


@router.callback_query(F.data == "adminv2:stats")
async def admin_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_purchase_orders_admin(200)
    total = len(rows)
    open_orders = len([r for r in rows if str(r.get("status")) in ("pending_payment", "payment_submitted", "paid")])
    fulfilled = len([r for r in rows if str(r.get("status")) == "fulfilled"])

    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Stats\n\n"
            f"Orders total: {total}\n"
            f"Orders open: {open_orders}\n"
            f"Orders fulfilled: {fulfilled}"
        )


@router.callback_query(F.data == "adminv2:logs")
async def admin_logs(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(user_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    await callback.answer()
    if callback.message:
        await callback.message.answer("Use /admin to access tail logs in the current console.")