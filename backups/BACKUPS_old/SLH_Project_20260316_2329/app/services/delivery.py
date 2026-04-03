from aiogram import Bot

from app.i18n import t, status_label

DEFAULT_GROUP_INVITE_LINK = "https://t.me/+KLKB9-JdO85kNWJk"


def _safe_text(value) -> str:
    return str(value or "").strip()


def render_payment_instructions(order: dict, lang: str, body: str = "", contact: str = "") -> str:
    lines = [
        t(lang, "payment.instructions.title"),
        "",
        t(lang, "order.id", id=int(order["id"])),
        t(lang, "order.product", title=order["product_title"], code=order["product_code"]),
        t(lang, "order.quantity", quantity=int(order["quantity"])),
        t(lang, "payment.instructions.line_amount", amount=float(order["total_amount"]), currency=order["currency"]),
        t(lang, "order.status", status=status_label(lang, order.get("status"))),
    ]

    clean_body = _safe_text(body)
    clean_contact = _safe_text(contact)

    if clean_body:
        lines.extend(["", t(lang, "payment.instructions.line_body", body=clean_body)])

    if clean_contact:
        lines.append(t(lang, "payment.instructions.line_contact", contact=clean_contact))

    lines.extend([
        "",
        t(lang, "payment.instructions.line_ref"),
        t(lang, "payment.instructions.line_after", id=int(order["id"])),
    ])
    return "\n".join(lines)


def render_payment_received_for_review(order: dict, lang: str) -> str:
    return (
        f"{t(lang, 'submit_payment.ok.title')}\n\n"
        f"{t(lang, 'order.id', id=int(order['id']))}\n"
        f"{t(lang, 'order.product', title=order['product_title'], code=order['product_code'])}\n"
        f"{t(lang, 'order.status', status=status_label(lang, order.get('status')))}\n"
        f"{t(lang, 'submit_payment.ref', ref=order.get('external_payment_ref') or '-')}\n\n"
        f"{t(lang, 'submit_payment.review_note')}"
    )


def render_receipt(order: dict, lang: str, footer: str = "") -> str:
    paid_at = order.get("paid_at") or "-"
    fulfilled_at = order.get("fulfilled_at") or "-"
    ref = order.get("external_payment_ref") or "-"
    note = order.get("admin_note") or "-"
    clean_footer = _safe_text(footer)

    lines = [
        t(lang, "receipt.title"),
        "",
        t(lang, "order.id", id=int(order["id"])),
        t(lang, "order.product", title=order["product_title"], code=order["product_code"]),
        t(lang, "order.quantity", quantity=int(order["quantity"])),
        t(lang, "order.total", amount=float(order["total_amount"]), currency=order["currency"]),
        t(lang, "receipt.line_status", status=status_label(lang, order.get("status"))),
        t(lang, "receipt.line_paid_at", paid_at=paid_at),
        t(lang, "receipt.line_fulfilled_at", fulfilled_at=fulfilled_at),
        t(lang, "receipt.line_ref", ref=ref),
        t(lang, "receipt.line_note", note=note),
    ]

    if clean_footer:
        lines.extend(["", clean_footer])
    else:
        lines.extend(["", t(lang, "receipt.line_footer")])

    return "\n".join(lines)


async def deliver_group_access(bot: Bot, user_id: int, order_id: int, lang: str = "he", invite_link: str | None = None) -> str:
    final_link = _safe_text(invite_link) or DEFAULT_GROUP_INVITE_LINK
    text = (
        f"{t(lang, 'delivery.friends.title')}\n\n"
        f"{t(lang, 'delivery.friends.body')}\n\n"
        f"{t(lang, 'delivery.friends.join')}\n"
        f"{final_link}\n\n"
        f"{t(lang, 'order.id', id=order_id)}"
    )
    await bot.send_message(user_id, text)
    return final_link


async def send_fulfillment_bundle(
    bot: Bot,
    order: dict,
    lang: str = "he",
    invite_link: str | None = None,
    receipt_footer: str = "",
) -> None:
    await bot.send_message(
        int(order["user_id"]),
        f"{t(lang, 'delivery.success.title')}\n\n"
        f"{t(lang, 'order.id', id=int(order['id']))}\n"
        f"{t(lang, 'order.product', title=order['product_title'], code=order['product_code'])}\n"
        f"{t(lang, 'order.status', status=status_label(lang, order.get('status')))}"
    )

    if str(order.get("product_code") or "").strip().upper() == "FRIENDS_SUPPORT_ACCESS":
        await deliver_group_access(
            bot=bot,
            user_id=int(order["user_id"]),
            order_id=int(order["id"]),
            lang=lang,
            invite_link=invite_link,
        )

    await bot.send_message(
        int(order["user_id"]),
        render_receipt(order, lang, footer=receipt_footer),
    )