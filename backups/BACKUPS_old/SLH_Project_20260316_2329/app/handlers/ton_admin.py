from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.admin_guard import is_admin
from app.services.withdrawals_query import mark_withdraw_sent, mark_withdraw_failed
from app.services.withdrawals_exec import get_withdrawal_for_execution
from app.services.ton_gateway import send_ton_withdrawal
from app.services.delivery import send_fulfillment_bundle
from app.services.purchases import get_manual_payment_config
from app.services.purchases_admin import (
    list_product_groups,
    list_products_admin,
    list_purchase_orders_admin,
    get_purchase_order_admin,
    mark_purchase_order_paid_admin,
    reject_purchase_order_payment_admin,
    fulfill_purchase_order_admin,
    hide_product,
    show_product,
    set_product_group,
    update_product_price_admin,
    list_system_settings_admin,
    set_system_setting_text_admin,
)

router = Router()


def _render_groups(rows: list[dict]) -> str:
    if not rows:
        return "No product groups."

    lines = ["Product groups", ""]
    for row in rows:
        lines.append(
            f"{row['code']} | {row['title']} | sort={int(row['sort_order'])} | active={bool(row['is_active'])}"
        )
    return "\n".join(lines)


def _render_products(rows: list[dict]) -> str:
    if not rows:
        return "No products."

    lines = ["Products", ""]
    for row in rows:
        lines.append(
            f"{row['code']} | {row['title']} | "
            f"group={row.get('group_code') or '-'} | "
            f"price={row['price_amount']} {row['price_currency']} | "
            f"visible={bool(row['is_visible'])} | "
            f"active={bool(row['is_active'])} | "
            f"featured={bool(row.get('is_featured'))} | "
            f"inventory={row.get('inventory_mode') or '-'}"
        )
    return "\n".join(lines)


def _render_purchase_queue(rows: list[dict]) -> str:
    if not rows:
        return "Purchase Queue\n\nNo open purchase orders."

    lines = [
        "Purchase Queue",
        "",
        "Priority: payment_submitted -> pending_payment -> paid",
        "",
    ]
    for row in rows:
        ref = row.get("external_payment_ref") or "-"
        note = row.get("admin_note") or "-"
        lines.append(
            f"#{int(row['id'])} | user={int(row['user_id'])} | "
            f"{row['product_code']} | {float(row['total_amount']):.8f} {row['currency']} | "
            f"{row['status']} | ref={ref} | note={note}"
        )

    lines.extend([
        "",
        "Review flow:",
        "/purchase_order <order_id>",
        "/purchase_approve <order_id> [payment_ref] [admin_note]",
        "/purchase_reject <order_id> [reason]",
        "/purchase_message <order_id> <message>",
        "/purchase_offer <order_id> <message>",
        "/purchase_fulfill <order_id> [admin_note]",
    ])
    return "\n".join(lines)


def _first_line_text(message: types.Message) -> str:
    text = message.text or ""
    lines = text.splitlines()
    if not lines:
        return ""
    return lines[0].strip()


def _inventory_keyboard(rows: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows[:20]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{row['code']} | {row['price_amount']} {row['price_currency']}",
                callback_data=f"adm:inv:product:{row['code']}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="System Settings", callback_data="adm:inv:settings")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _settings_keyboard(rows: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows[:20]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{row['key']} = {row['value_text']}",
                callback_data=f"adm:inv:setting:{row['key']}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _render_purchase_order_admin(row: dict) -> str:
    ref = row.get("external_payment_ref") or "-"
    note = row.get("admin_note") or "-"
    paid_at = row.get("paid_at") or "-"
    fulfilled_at = row.get("fulfilled_at") or "-"

    return (
        "Purchase Order\n\n"
        f"Order ID: {int(row['id'])}\n"
        f"User ID: {int(row['user_id'])}\n"
        f"Product: {row['product_title']} ({row['product_code']})\n"
        f"Quantity: {int(row['quantity'])}\n"
        f"Unit Price: {float(row['unit_price_amount']):.8f} {row['currency']}\n"
        f"Total: {float(row['total_amount']):.8f} {row['currency']}\n"
        f"Payment Method: {row['payment_method']}\n"
        f"Status: {row['status']}\n"
        f"Reference: {ref}\n"
        f"Admin Note: {note}\n"
        f"Paid At: {paid_at}\n"
        f"Fulfilled At: {fulfilled_at}"
    )


@router.message(Command("list_groups"))
async def list_groups_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    rows = await list_product_groups(50)
    await message.answer(_render_groups(rows))


@router.message(Command("list_products"))
async def list_products_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    rows = await list_products_admin(100)
    await message.answer(_render_products(rows))


@router.message(Command("hide_product"))
async def hide_product_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /hide_product <product_code>")
        return

    result = await hide_product(parts[1], admin_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(f"Product hidden: {row['code']} | {row['title']} | visible={row['is_visible']}")


@router.message(Command("show_product"))
async def show_product_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /show_product <product_code>")
        return

    result = await show_product(parts[1], admin_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(f"Product shown: {row['code']} | {row['title']} | visible={row['is_visible']}")


@router.message(Command("set_product_group"))
async def set_product_group_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("Usage: /set_product_group <product_code> <group_code>")
        return

    result = await set_product_group(parts[1], parts[2], admin_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Product group updated: {row['code']} | {row['title']} | "
        f"group={row['group_code']} ({row['group_title']})"
    )


@router.message(Command("ton_send_approved"))
async def ton_send_approved_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /ton_send_approved <withdrawal_id>")
        return

    withdrawal_id = int(parts[1])
    row = await get_withdrawal_for_execution(withdrawal_id)

    if not row:
        await message.answer("Withdrawal not found.")
        return

    if str(row["status"]) != "approved":
        await message.answer(f"Withdrawal status is {row['status']}, not approved.")
        return

    result = await send_ton_withdrawal(
        withdrawal_id=int(row["id"]),
        wallet=str(row["wallet"]),
        amount=float(row["amount"]),
    )

    if not result["ok"]:
        fail = await mark_withdraw_failed(withdrawal_id, admin_id, result["error"])
        if not fail["ok"]:
            await message.answer(result["error"])
            return
        await message.answer(f"TON send failed for #{withdrawal_id}\nerror={result['error']}")
        return

    sent = await mark_withdraw_sent(withdrawal_id, admin_id, str(result["tx_hash"]))
    if not sent["ok"]:
        await message.answer(sent["error"])
        return

    await message.answer(
        f"TON processed withdrawal #{withdrawal_id}\n"
        f"mode={result['mode']}\n"
        f"tx_hash={result['tx_hash']}"
    )


@router.message(Command("purchase_queue"))
async def purchase_queue_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    rows = await list_purchase_orders_admin(50)
    await message.answer(_render_purchase_queue(rows))


@router.message(Command("purchase_order"))
async def purchase_order_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_order <order_id>")
        return

    order_id = int(parts[1])
    row = await get_purchase_order_admin(order_id)
    if not row:
        await message.answer(f"Purchase order #{order_id} not found.")
        return

    await message.answer(_render_purchase_order_admin(row))


@router.message(Command("purchase_mark_paid"))
@router.message(Command("purchase_approve"))
async def purchase_mark_paid_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_approve <order_id> [payment_ref] [admin_note]")
        return

    order_id = int(parts[1])
    payment_ref = parts[2] if len(parts) >= 3 else ""
    admin_note = " ".join(parts[3:]).strip() if len(parts) >= 4 else ""

    result = await mark_purchase_order_paid_admin(order_id, admin_id, payment_ref, admin_note)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        "Purchase payment approved.\n\n"
        f"Order ID: {int(row['id'])}\n"
        f"Product: {row['product_title']} ({row['product_code']})\n"
        f"Status: {row['status']}\n"
        f"Reference: {row.get('external_payment_ref') or '-'}\n"
        f"Points Granted: {float(row.get('points_granted') or 0):.8f}\n"
        f"Admin Note: {row.get('admin_note') or '-'}"
    )


@router.message(Command("purchase_reject"))
async def purchase_reject_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_reject <order_id> [reason]")
        return

    order_id = int(parts[1])
    reason = parts[2] if len(parts) >= 3 else ""

    result = await reject_purchase_order_payment_admin(order_id, admin_id, reason)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    try:
        await message.bot.send_message(
            int(row["user_id"]),
            "Your payment submission was rejected.\n\n"
            f"Order ID: {int(row['id'])}\n"
            f"Product: {row['product_title']} ({row['product_code']})\n"
            f"Status: {row['status']}\n"
            f"Note: {row.get('admin_note') or '-'}"
        )
    except Exception:
        pass

    await message.answer(
        "Purchase payment rejected.\n\n"
        f"Order ID: {int(row['id'])}\n"
        f"Status: {row['status']}\n"
        f"Admin Note: {row.get('admin_note') or '-'}"
    )


@router.message(Command("purchase_message"))
async def purchase_message_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_message <order_id> <message>")
        return

    order_id = int(parts[1])
    user_text = parts[2].strip()

    row = await get_purchase_order_admin(order_id)
    if not row:
        await message.answer(f"Purchase order #{order_id} not found.")
        return

    try:
        await message.bot.send_message(
            int(row["user_id"]),
            "Message from support:\n\n"
            f"{user_text}\n\n"
            f"Order ID: {int(row['id'])}"
        )
    except Exception:
        await message.answer("Could not deliver message to user.")
        return

    await message.answer(f"Message sent to user {int(row['user_id'])} for order #{int(row['id'])}.")


@router.message(Command("purchase_offer"))
async def purchase_offer_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_offer <order_id> <message>")
        return

    order_id = int(parts[1])
    offer_text = parts[2].strip()

    row = await get_purchase_order_admin(order_id)
    if not row:
        await message.answer(f"Purchase order #{order_id} not found.")
        return

    try:
        await message.bot.send_message(
            int(row["user_id"]),
            "Offer from support:\n\n"
            f"{offer_text}\n\n"
            f"Order ID: {int(row['id'])}"
        )
    except Exception:
        await message.answer("Could not deliver offer to user.")
        return

    await message.answer(f"Offer sent to user {int(row['user_id'])} for order #{int(row['id'])}.")


@router.message(Command("purchase_fulfill"))
async def purchase_fulfill_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /purchase_fulfill <order_id> [admin_note]")
        return

    order_id = int(parts[1])
    admin_note = parts[2] if len(parts) >= 3 else ""

    result = await fulfill_purchase_order_admin(order_id, admin_id, admin_note)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    payment_cfg = await get_manual_payment_config()

    await send_fulfillment_bundle(
        bot=message.bot,
        order=row,
        lang="he",
        invite_link=payment_cfg.get("friends_support_invite_link") or "",
        receipt_footer=payment_cfg.get("receipt_footer") or "",
    )

    await message.answer(
        "Purchase order fulfilled and delivered to user.\n\n"
        f"Order ID: {int(row['id'])}\n"
        f"Product: {row['product_title']} ({row['product_code']})\n"
        f"Status: {row['status']}\n"
        f"Admin Note: {row.get('admin_note') or '-'}"
    )@router.message(Command("admin_inventory"))
async def admin_inventory_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    rows = await list_products_admin(100)
    if not rows:
        await message.answer("No inventory items.")
        return

    await message.answer(
        "Admin Inventory\n\nChoose a product to inspect or update.",
        reply_markup=_inventory_keyboard(rows),
    )


@router.callback_query(lambda c: c.data == "adm:inv:settings")
async def admin_inventory_settings(callback: types.CallbackQuery):
    admin_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(admin_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    rows = await list_system_settings_admin(50)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "System Settings\n\nChoose a setting key to inspect or update.",
            reply_markup=_settings_keyboard(rows),
        )


@router.callback_query(lambda c: c.data and c.data.startswith("adm:inv:product:"))
async def admin_inventory_product(callback: types.CallbackQuery):
    admin_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(admin_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    code = str(callback.data).split(":", 3)[3]
    rows = await list_products_admin(200)
    row = next((r for r in rows if str(r["code"]) == code), None)

    await callback.answer()
    if row is None:
        if callback.message:
            await callback.message.answer("Product not found.")
        return

    if callback.message:
        await callback.message.answer(
            "Product\n\n"
            f"Code: {row['code']}\n"
            f"Title: {row['title']}\n"
            f"Price: {row['price_amount']} {row['price_currency']}\n"
            f"Visible: {row['is_visible']}\n"
            f"Active: {row['is_active']}\n"
            f"Featured: {row.get('is_featured')}\n\n"
            f"Update price with:\n/set_price {row['code']} <amount>"
        )


@router.callback_query(lambda c: c.data and c.data.startswith("adm:inv:setting:"))
async def admin_inventory_setting(callback: types.CallbackQuery):
    admin_id = callback.from_user.id if callback.from_user else 0
    if not is_admin(admin_id):
        await callback.answer("Forbidden", show_alert=True)
        return

    key = str(callback.data).split(":", 3)[3]
    rows = await list_system_settings_admin(200)
    row = next((r for r in rows if str(r["key"]) == key), None)

    await callback.answer()
    if row is None:
        if callback.message:
            await callback.message.answer("Setting not found.")
        return

    if callback.message:
        await callback.message.answer(
            "System Setting\n\n"
            f"Key: {row['key']}\n"
            f"Value: {row['value_text']}\n\n"
            f"Update with:\n/set_setting_text {row['key']} <value_text>"
        )


@router.message(Command("set_price"))
async def set_price_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("Usage: /set_price <product_code> <amount>")
        return

    product_code = parts[1].strip()

    try:
        amount = float(parts[2].strip())
    except Exception:
        await message.answer("Amount must be numeric.")
        return

    result = await update_product_price_admin(product_code, amount, admin_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Price updated.\n\n"
        f"Code: {row['code']}\n"
        f"Title: {row['title']}\n"
        f"Price: {row['price_amount']} {row['price_currency']}"
    )


@router.message(Command("set_setting_text"))
async def set_setting_text_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("Usage: /set_setting_text <key> <value_text>")
        return

    key = parts[1].strip()
    value_text = parts[2].strip()

    result = await set_system_setting_text_admin(key, value_text, admin_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Setting updated.\n\n"
        f"Key: {row['key']}\n"
        f"Value: {row['value_text']}"
    )