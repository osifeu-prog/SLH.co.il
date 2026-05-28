"""
SLH AI Spark ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Telegram Stars payment flow.

Handlers:
- /upgrade [tier]  ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ show prices or send invoice for the chosen tier
- /credits         ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ show remaining quota
- /pricing         ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ show full price table
- pre_checkout_query handler ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ approve all (or refuse with reason)
- successful_payment handler ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ activate subscription + log

Wired into bot.py via `payment_flow.register(dp, auth)`.
"""
from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

import pricing
import quota
import subscriptions

log = logging.getLogger("slh-payment")

# Telegram Stars use a special "currency" code XTR
STARS_CURRENCY = "XTR"


def _payload_for_tier(tier: str, user_id: int) -> str:
    """Encoded into the invoice; we pull tier+user_id back from successful_payment."""
    return f"slh-ai:{tier}:{user_id}"


def _parse_payload(payload: str) -> tuple[Optional[str], Optional[int]]:
    try:
        prefix, tier, uid = payload.split(":", 2)
        if prefix != "slh-ai":
            return None, None
        return tier, int(uid)
    except Exception:
        return None, None


def register(dp: Dispatcher, auth_module) -> None:
    """Hook all payment-related handlers onto the dispatcher."""

    @dp.message(Command("pricing"))
    async def cmd_pricing(msg: Message) -> None:
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        await msg.answer(
            pricing.all_tiers_summary_he() + "\n\n׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ג„¢: `/upgrade pro` ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢ `/upgrade vip`"
        )

    @dp.message(Command("credits"))
    async def cmd_credits(msg: Message) -> None:
        # Anyone can check their own credits ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ no auth gate (helpful for support)
        text = await quota.quota_status_he(msg.from_user.id)
        await msg.answer(text)

    @dp.message(Command("upgrade"))
    async def cmd_upgrade(msg: Message, bot: Bot) -> None:
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split(maxsplit=1)
        tier_arg = parts[1].strip().lower() if len(parts) > 1 else ""

        if tier_arg not in ("pro", "vip"):
            # No tier specified ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ show menu with buttons
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"׳³ֲ ײ²ֲ׳’ג‚¬ג„¢ײ²ֲ Pro ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ ׳³ג€™׳’ג‚¬ֲײ³ג€”{pricing.TIERS['pro'].price_ils}/׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ©",
                    callback_data="upgrade:pro",
                )],
                [InlineKeyboardButton(
                    text=f"׳³ֲ ײ²ֲ׳’ג‚¬ֻ׳’ג‚¬ֻ VIP ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ ׳³ג€™׳’ג‚¬ֲײ³ג€”{pricing.TIERS['vip'].price_ils}/׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ©",
                    callback_data="upgrade:vip",
                )],
                [InlineKeyboardButton(text="׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€” ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€”", callback_data="show_pricing")],
            ])
            await msg.answer(
                "*׳³ֲ³׳’ג‚¬ֻ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³ײ²ֲ¨ ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ג„¢:*\n\n"
                + pricing.tier_summary_he("pro") + "\n\n"
                + pricing.tier_summary_he("vip"),
                reply_markup=kb,
            )
            return

        await _send_invoice(bot, msg.chat.id, msg.from_user.id, tier_arg)

    @dp.callback_query(F.data.startswith("upgrade:"))
    async def cb_upgrade(cb, bot: Bot):
        if not auth_module.is_authorized(cb.from_user.id):
            await cb.answer("׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ", show_alert=True)
            return
        tier = cb.data.split(":", 1)[1]
        if tier not in ("pro", "vip"):
            await cb.answer("׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ§׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€”", show_alert=True)
            return
        await cb.answer()
        await _send_invoice(bot, cb.message.chat.id, cb.from_user.id, tier)

    @dp.callback_query(F.data == "show_pricing")
    async def cb_show_pricing(cb):
        await cb.answer()
        await cb.message.answer(pricing.all_tiers_summary_he())

    @dp.pre_checkout_query()
    async def pre_checkout(query: PreCheckoutQuery, bot: Bot):
        """Telegram asks: 'OK to charge?' We say yes (or no with reason)."""
        tier, uid = _parse_payload(query.invoice_payload)
        if tier is None or uid != query.from_user.id:
            await bot.answer_pre_checkout_query(
                query.id, ok=False,
                error_message="׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ§׳³ֲ³׳’ג€ֳ-׳³ֲ³׳’ג‚¬ֲ. ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֻ ׳³ֲ³ײ²ֲ-/upgrade.",
            )
            return
        if tier not in pricing.TIERS or pricing.TIERS[tier].price_stars == 0:
            await bot.answer_pre_checkout_query(
                query.id, ok=False,
                error_message="׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ§׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€”.",
            )
            return
        await bot.answer_pre_checkout_query(query.id, ok=True)

    @dp.message(F.successful_payment)
    async def on_payment(msg: Message):
        """Telegram confirms: payment captured. Activate the tier."""
        sp = msg.successful_payment
        tier, uid = _parse_payload(sp.invoice_payload)
        if tier is None or uid != msg.from_user.id:
            log.error(f"payment payload mismatch: {sp.invoice_payload}")
            return

        # ILS conversion (stars ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ ils): use the tier's nominal ILS price as "received"
        # Real settlement happens on Telegram's side; we're tracking nominal here.
        ils_cents = pricing.TIERS[tier].price_ils * 100

        await subscriptions.record_payment(
            user_id=msg.from_user.id,
            provider="telegram_stars",
            charge_id=sp.telegram_payment_charge_id,
            amount_stars=sp.total_amount,
            amount_ils_cents=ils_cents,
            tier_purchased=tier,
            status="completed",
            raw_payload={
                "currency": sp.currency,
                "total_amount": sp.total_amount,
                "invoice_payload": sp.invoice_payload,
                "telegram_payment_charge_id": sp.telegram_payment_charge_id,
                "provider_payment_charge_id": sp.provider_payment_charge_id,
            },
        )

        await subscriptions.upgrade(
            user_id=msg.from_user.id,
            tier=tier,
            provider="telegram_stars",
            payment_id=sp.telegram_payment_charge_id,
        )

        spec = pricing.TIERS[tier]
        await msg.answer(
            f"׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ *׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ¨!*\n\n"
            f"׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ג„¢׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ-*{spec.name_he}* ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ ׳³ג€™׳’ג‚¬ֲײ³ג€”{spec.price_ils}/׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ©.\n"
            f"׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֳ·׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג‚¬ֲ: {spec.monthly_quota or 'unlimited (fair-use ' + str(spec.fair_use_cap) + ')'} ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€”\n"
            f"AI: Claude Sonnet 4.5 + tools\n\n"
            f"׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½- /credits ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¦׳³ֲ³׳’ג‚¬ֻ, ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢ ׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ»ֲ ׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½- ׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ."
        )

    log.info("payment_flow handlers registered")


async def _send_invoice(bot: Bot, chat_id: int, user_id: int, tier: str) -> None:
    spec = pricing.TIERS[tier]
    if spec.price_stars == 0:
        await bot.send_message(chat_id, f"׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€” {spec.name_he} ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ ׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֳ·׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ.")
        return
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"SLH AI Spark ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ {spec.name_he}",
        description=spec.description_he,
        payload=_payload_for_tier(tier, user_id),
        currency=STARS_CURRENCY,
        prices=[LabeledPrice(label=f"{spec.name_he} ׳³ֲײ²ֲ¿ײ²ֲ½-30 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ", amount=spec.price_stars)],
        # provider_token left empty ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Telegram Stars don't need a provider
    )

