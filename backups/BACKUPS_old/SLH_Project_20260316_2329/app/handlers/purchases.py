import re
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.i18n import get_user_language, t, status_label
from app.services.bootstrap import ensure_user_exists
from app.services.delivery import render_payment_instructions, render_payment_received_for_review
from app.services.purchases import (
    cancel_purchase_order,
    create_purchase_order,
    get_manual_payment_config,
    list_active_products,
    list_user_purchase_orders,
    submit_purchase_payment,
)

router = Router()

PAGE_SIZE = 5


def _first_line_text(message: Message) -> str:
    text = message.text or ""
    lines = text.splitlines()
    if not lines:
        return ""
    return lines[0].strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_page(page: int, total_pages: int) -> int:
    if total_pages <= 0:
        return 0
    return max(0, min(page, total_pages - 1))


def _paginate_rows(rows: list[dict], page: int) -> tuple[list[dict], int, int]:
    total = len(rows)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = _normalize_page(page, total_pages)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    return rows[start:end], page, total_pages


def _find_product(rows: list[dict], product_code: str) -> dict | None:
    wanted = (product_code or "").strip().upper()
    for row in rows:
        if str(row.get("code") or "").strip().upper() == wanted:
            return row
    return None


def _featured_codes(rows: list[dict]) -> list[str]:
    return [str(r["code"]) for r in rows if bool(r.get("is_featured"))]


def _product_card_text(row: dict, lang: str) -> str:
    code = str(row["code"])
    title = str(row["title"])
    amount = float(row.get("price_amount") or 0)
    currency = str(row.get("price_currency") or "TON")
    ptype = str(row.get("product_type") or "digital")
    group_title = str(row.get("group_title") or t(lang, "store.group.other"))
    desc = (row.get("description") or "").strip()
    success_message = (row.get("success_message_template") or "").strip()

    lines = [
        t(lang, "detail.title"),
        "",
        f"{title} ({code})",
        t(lang, "store.product_group", group=group_title),
        t(lang, "store.product_type", ptype=ptype),
        t(lang, "store.product_price", amount=amount, currency=currency),
    ]

    inventory_mode = str(row.get("inventory_mode") or "unlimited")
    inventory_count = row.get("inventory_count")
    if inventory_mode == "limited":
        lines.append(t(lang, "store.stock.limited", count=_safe_int(inventory_count, 0)))
    else:
        lines.append(t(lang, "store.stock.unlimited"))

    limit_per_user = row.get("purchase_limit_per_user")
    if limit_per_user is not None:
        lines.append(t(lang, "store.limit.user", count=_safe_int(limit_per_user, 0)))

    if bool(row.get("is_featured")):
        lines.append(t(lang, "store.badge.featured"))

    if desc:
        lines.append(t(lang, "store.product_desc", text=desc))

    if success_message:
        lines.append(t(lang, "detail.success_template", text=success_message))

    return "\n".join(lines)


def _render_products_text(rows: list[dict], lang: str, page: int) -> str:
    if not rows:
        return f"{t(lang, 'store.title')}\n\n{t(lang, 'store.empty')}"

    page_rows, page, total_pages = _paginate_rows(rows, page)
    featured = _featured_codes(rows)

    lines = [t(lang, "store.title"), ""]

    if featured:
        lines.append(f"{t(lang, 'store.featured_title')}: " + ", ".join(featured))
        lines.append("")

    lines.append(t(lang, "store.page_label", current=page + 1, total=total_pages))
    lines.append(t(lang, "store.catalog_hint"))
    lines.append("")
    lines.append(t(lang, "store.list_title"))

    for row in page_rows:
        lines.append(
            t(
                lang,
                "store.product_line",
                title=str(row["title"]),
                code=str(row["code"]),
                amount=float(row.get("price_amount") or 0),
                currency=str(row.get("price_currency") or "TON"),
            )
        )

    lines.extend([
        "",
        t(lang, "store.select_product"),
        "",
        t(lang, "store.commands"),
        t(lang, "store.cmd.buy"),
        t(lang, "store.cmd.my_orders"),
        t(lang, "store.cmd.submit_payment"),
        t(lang, "store.cmd.cancel_order"),
    ])

    return "\n".join(lines)


def _catalog_keyboard(rows: list[dict], lang: str, page: int) -> InlineKeyboardMarkup:
    page_rows, page, total_pages = _paginate_rows(rows, page)
    keyboard: list[list[InlineKeyboardButton]] = []

    for row in page_rows:
        code = str(row["code"])
        keyboard.append([
            InlineKeyboardButton(
                text=t(lang, "button.open_product", code=code),
                callback_data=f"store:detail:{code}:{page}",
            )
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text=t(lang, "button.prev"),
                callback_data=f"store:page:{page - 1}",
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            text=t(lang, "store.page_label", current=page + 1, total=total_pages),
            callback_data="store:noop",
        )
    )

    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text=t(lang, "button.next"),
                callback_data=f"store:page:{page + 1}",
            )
        )

    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton(
            text=t(lang, "button.refresh"),
            callback_data=f"store:page:{page}",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _detail_keyboard(row: dict, lang: str, page: int) -> InlineKeyboardMarkup:
    code = str(row["code"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "button.confirm_purchase"),
                    callback_data=f"store:buy:{code}:{page}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "button.back_to_store"),
                    callback_data=f"store:page:{page}",
                )
            ],
        ]
    )


def _image_url_or_none(row: dict) -> str | None:
    raw = str(row.get("image_url") or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return None


async def _send_store_catalog(message: Message, lang: str, page: int = 0) -> None:
    res = await list_active_products(200)
    if not res["ok"]:
        await message.answer(res["error"])
        return

    rows = res["rows"]
    text = _render_products_text(rows, lang, page)
    reply_markup = _catalog_keyboard(rows, lang, page)
    await message.answer(text, reply_markup=reply_markup)


async def _send_product_detail(message: Message, row: dict, lang: str, page: int) -> None:
    text = _product_card_text(row, lang)
    reply_markup = _detail_keyboard(row, lang, page)
    image_url = _image_url_or_none(row)

    if image_url:
        await message.answer_photo(photo=image_url, caption=text, reply_markup=reply_markup)
        return

    await message.answer(text, reply_markup=reply_markup)


def _render_order_created(order: dict, lang: str, payment_cfg: dict | None = None) -> str:
    cfg = payment_cfg or {}
    payment_text = render_payment_instructions(
        order=order,
        lang=lang,
        body=str(cfg.get("body") or ""),
        contact=str(cfg.get("contact") or ""),
    )

    return (
        f"{t(lang, 'order.created.title')}\n\n"
        f"{t(lang, 'order.id', id=int(order['id']))}\n"
        f"{t(lang, 'order.product', title=order['product_title'], code=order['product_code'])}\n"
        f"{t(lang, 'order.quantity', quantity=int(order['quantity']))}\n"
        f"{t(lang, 'order.total', amount=float(order['total_amount']), currency=order['currency'])}\n"
        f"{t(lang, 'order.payment_method', method=order['payment_method'])}\n"
        f"{t(lang, 'order.status', status=status_label(lang, order['status']))}\n\n"
        f"{payment_text}"
    )


def _render_orders(rows: list[dict], lang: str) -> str:
    if not rows:
        return f"{t(lang, 'orders.title')}\n\n{t(lang, 'orders.empty')}"

    lines = [t(lang, "orders.title"), ""]
    for row in rows:
        ext_ref = row.get("external_payment_ref") or "-"
        lines.append(
            t(
                lang,
                "orders.row",
                id=int(row["id"]),
                title=row["product_title"],
                code=row["product_code"],
                quantity=int(row["quantity"]),
                amount=float(row["total_amount"]),
                currency=row["currency"],
                status=status_label(lang, row["status"]),
                ref=ext_ref,
            )
        )

    lines.extend([
        "",
        t(lang, "orders.cancel_format"),
        t(lang, "store.cmd.cancel_order"),
    ])

    return "\n".join(lines)


@router.message(F.text == "Store")
@router.message(F.text == "Buy")
@router.message(Command("buy"))
async def buy_help(message: Message, command: CommandObject | None = None):
    lang = get_user_language(message)
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    await ensure_user_exists(user_id, username)

    raw = ""
    if command and command.args:
        lines = command.args.splitlines()
        raw = lines[0].strip() if lines else ""

    if raw:
        res = await create_purchase_order(user_id, raw, 1)
        if not res["ok"]:
            await message.answer(res["error"])
            return

        await message.answer(_render_order_created(res["order"], lang, res.get("payment_config")))
        return

    await _send_store_catalog(message, lang, 0)


@router.message(F.text.regexp(r"^[Bb]uy\s+[A-Za-z0-9_\-]+$"))
async def buy_text(message: Message):
    lang = get_user_language(message)
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    await ensure_user_exists(user_id, username)

    text = _first_line_text(message)
    m = re.match(r"^[Bb]uy\s+([A-Za-z0-9_\-]+)$", text)
    if not m:
        await _send_store_catalog(message, lang, 0)
        return

    product_code = m.group(1)
    res = await create_purchase_order(user_id, product_code, 1)
    if not res["ok"]:
        await message.answer(res["error"])
        return

    await message.answer(_render_order_created(res["order"], lang, res.get("payment_config")))


@router.callback_query(F.data == "store:noop")
async def store_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("store:page:"))
async def store_page(callback: CallbackQuery):
    lang = get_user_language(callback)
    user_id = callback.from_user.id if callback.from_user else 0
    username = callback.from_user.username if callback.from_user else None
    await ensure_user_exists(user_id, username)

    raw = str(callback.data or "")
    parts = raw.split(":")
    page = _safe_int(parts[2] if len(parts) > 2 else 0, 0)

    await callback.answer()
    if callback.message is None:
        return
    await _send_store_catalog(callback.message, lang, page)


@router.callback_query(F.data.startswith("store:detail:"))
async def store_detail(callback: CallbackQuery):
    lang = get_user_language(callback)
    user_id = callback.from_user.id if callback.from_user else 0
    username = callback.from_user.username if callback.from_user else None
    await ensure_user_exists(user_id, username)

    raw = str(callback.data or "")
    parts = raw.split(":")
    code = parts[2] if len(parts) > 2 else ""
    page = _safe_int(parts[3] if len(parts) > 3 else 0, 0)

    await callback.answer()

    res = await list_active_products(200)
    if not res["ok"]:
        if callback.message is not None:
            await callback.message.answer(res["error"])
        return

    row = _find_product(res["rows"], code)
    if row is None:
        if callback.message is not None:
            await callback.message.answer(t(lang, "detail.not_found"))
        return

    if callback.message is None:
        return
    await _send_product_detail(callback.message, row, lang, page)


@router.callback_query(F.data.startswith("store:buy:"))
async def store_buy(callback: CallbackQuery):
    lang = get_user_language(callback)
    user_id = callback.from_user.id if callback.from_user else 0
    username = callback.from_user.username if callback.from_user else None
    await ensure_user_exists(user_id, username)

    raw = str(callback.data or "")
    parts = raw.split(":")
    code = parts[2] if len(parts) > 2 else ""

    await callback.answer()

    res = await create_purchase_order(user_id, code, 1)
    if callback.message is None:
        return

    if not res["ok"]:
        await callback.message.answer(res["error"])
        return

    await callback.message.answer(_render_order_created(res["order"], lang, res.get("payment_config")))


@router.message(F.text == "My Orders")
@router.message(Command("my_orders"))
async def my_orders(message: Message):
    lang = get_user_language(message)
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    await ensure_user_exists(user_id, username)

    rows = await list_user_purchase_orders(user_id, 10)
    await message.answer(_render_orders(rows, lang))


@router.message(Command("submit_payment"))
async def submit_payment_cmd(message: Message):
    lang = get_user_language(message)
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    await ensure_user_exists(user_id, username)

    parts = _first_line_text(message).split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer(t(lang, "submit_payment.usage"))
        return

    order_id = int(parts[1])
    payment_ref = parts[2]

    result = await submit_purchase_payment(order_id, user_id, payment_ref)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    await message.answer(render_payment_received_for_review(result["row"], lang))


@router.message(Command("cancel_order"))
async def cancel_order_cmd(message: Message):
    lang = get_user_language(message)
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    await ensure_user_exists(user_id, username)

    parts = _first_line_text(message).split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(t(lang, "cancel_order.usage"))
        return

    order_id = int(parts[1])

    result = await cancel_purchase_order(order_id, user_id)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"{t(lang, 'cancel_order.ok.title')}\n\n"
        f"{t(lang, 'order.id', id=int(row['id']))}\n"
        f"{t(lang, 'order.product', title=row['product_title'], code=row['product_code'])}\n"
        f"{t(lang, 'order.status', status=status_label(lang, row['status']))}\n"
        f"{t(lang, 'cancel_order.note', note=row.get('admin_note') or '-')}"
    )