"""
SLH AI Spark ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Admin commands. Only admins (auth.is_authorized) may run these.

- /revenue                 ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ MRR + last 30d revenue + cost + net
- /quota_user <user_id>    ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ see/set quota for a user
- /set_tier <user_id> <tier> ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ manual tier upgrade (e.g., for grandfathered users)
- /anthropic_spend         ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ estimated Anthropic spend last 7/30 days
- /top_users               ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ top 10 users by AI message count this month
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import aiosqlite
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

import pricing
import subscriptions

log = logging.getLogger("slh-admin")


def register(dp: Dispatcher, auth_module) -> None:

    @dp.message(Command("revenue"))
    async def cmd_revenue(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        stats = await subscriptions.usage_stats(window_days=30)
        mrr = await subscriptions.mrr_ils()

        revenue_ils = stats["revenue_ils_cents"] / 100
        anthropic = stats["usage_by_provider"].get("anthropic", {})
        anthropic_cost_usd = anthropic.get("cost_usd_cents", 0) / 100
        anthropic_cost_ils = anthropic_cost_usd * pricing.USD_ILS_RATE
        net_ils = revenue_ils - anthropic_cost_ils

        tiers_str = "\n".join(
            f"  ׳³ג€™׳’ג€ֲ¬ײ²ֲ¢ {tier}: {count}"
            for tier, count in sorted(stats["tier_counts"].items())
        ) or "  (׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ)"

        await msg.answer(
            f"׳³ֲ ײ²ֲ׳’ג‚¬ג„¢ײ²ֲ° *Revenue Report ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ 30 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ*\n\n"
            f"*MRR:* `׳³ג€™׳’ג‚¬ֲײ³ג€”{mrr:,.2f}`\n"
            f"*Revenue 30d:* `׳³ג€™׳’ג‚¬ֲײ³ג€”{revenue_ils:,.2f}`\n"
            f"*Anthropic cost 30d:* `׳³ג€™׳’ג‚¬ֲײ³ג€”{anthropic_cost_ils:,.2f}` (${anthropic_cost_usd:,.2f})\n"
            f"*Net profit 30d:* `׳³ג€™׳’ג‚¬ֲײ³ג€”{net_ils:,.2f}`\n\n"
            f"*׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ:*\n{tiers_str}\n\n"
            f"*Messages 30d:*\n"
            + "\n".join(f"  ׳³ג€™׳’ג€ֲ¬ײ²ֲ¢ {p}: {d['messages']}" for p, d in stats["usage_by_provider"].items())
        )

    @dp.message(Command("anthropic_status"))
    async def cmd_anthropic_status(msg: Message):
        """Probe Anthropic key state: auth + balance ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ without printing the key."""
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        import os, httpx
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key.startswith("sk-"):
            await msg.answer(
                "׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ´ *ANTHROPIC_API_KEY*\n׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ»ֲ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€”׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג‚¬ֻ-sk-.\n"
                "׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ¡׳³ֲ³ײ²ֲ£ ׳³ֲ³׳’ג‚¬ֻ-`slh-claude-bot/.env` ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ¢׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג‚¬ֲ `docker compose up -d --force-recreate claude-bot`.")
            return
        # Step 1: auth check via /v1/models (free, doesn't consume credit)
        try:
            r = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                timeout=10,
            )
            auth_ok = (r.status_code == 200)
        except Exception as e:
            auth_ok = False
            r_text = f"err: {type(e).__name__}"
        # Step 2: tiny balance probe ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ 1-token call. If it 400s with "credit balance",
        # we know there's $0; if it 200s, balance exists.
        try:
            from anthropic import Anthropic
            c = Anthropic(api_key=key)
            c.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
                max_tokens=1,
                messages=[{"role": "user", "content": "."}],
            )
            balance_ok = True
            balance_note = "׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ© balance ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Pro tier ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³׳’ג‚¬ֻ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ¨"
        except Exception as e:
            err = str(e).lower()
            balance_ok = False
            if "credit balance" in err or "credit_balance" in err or "billing" in err:
                balance_note = "$0 balance ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Pro tier ׳³ֲ³׳’ג€ֲ¢׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ג€׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ¨ ׳³ֲ³ײ²ֲ-Groq fallback ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ»ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³ײ»ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ³ג€”"
            else:
                balance_note = f"err: {type(e).__name__}: {str(e)[:80]}"
        await msg.answer(
            f"׳³ֲ ײ²ֲ׳’ג‚¬ֲ׳’ג‚¬ֻ *Anthropic Status*\n"
            f"  auth: {'׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦' if auth_ok else '׳³ג€™ײ²ֲײ²ֲ'}\n"
            f"  balance: {'׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦' if balance_ok else '׳³ג€™ײ²ֲײ²ֲ ׳³ֲײ²ֲ¸ײ²ֲ'}\n"
            f"  ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ {balance_note}"
        )

    @dp.message(Command("anthropic_spend"))
    async def cmd_spend(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        for window in (1, 7, 30):
            stats = await subscriptions.usage_stats(window_days=window)
            anthropic = stats["usage_by_provider"].get("anthropic", {})
            cost_usd = (anthropic.get("cost_usd_cents", 0)) / 100
            tin = anthropic.get("tokens_in", 0)
            tout = anthropic.get("tokens_out", 0)
            await msg.answer(
                f"׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ *Anthropic Spend ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ {window}d*\n"
                f"  ׳³ֲ ײ²ֲ׳’ג‚¬ג„¢ײ²ֲµ ${cost_usd:,.2f} (~׳³ג€™׳’ג‚¬ֲײ³ג€”{cost_usd * pricing.USD_ILS_RATE:,.2f})\n"
                f"  ׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ¥ {tin:,} input tokens\n"
                f"  ׳³ֲ ײ²ֲ׳’ג‚¬ֲ׳’ג€ֳ- {tout:,} output tokens"
            )

    @dp.message(Command("quota_user"))
    async def cmd_quota_user(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split()
        if len(parts) < 2:
            await msg.answer("׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ©: `/quota_user <user_id>`")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await msg.answer("user_id ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֻ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ¨.")
            return
        sub = await subscriptions.get_or_create(target_uid)
        spec = pricing.TIERS.get(sub.tier, pricing.TIERS["free"])
        cap = spec.monthly_quota or spec.fair_use_cap
        await msg.answer(
            f"׳³ֲ ײ²ֲ׳’ג‚¬ֻ׳’ג€ֳ- *User {target_uid}*\n"
            f"  Tier: `{sub.tier}` ׳²ֲ²ײ²ֲ· {spec.name_he}\n"
            f"  Used: {sub.messages_used_this_period}/{cap}\n"
            f"  Period: `{sub.current_period_start[:10]}` ׳³ג€™׳’ג‚¬ֲ ׳’ג‚¬ג„¢ `{sub.current_period_end[:10]}`\n"
            f"  Provider: `{sub.payment_provider or 'none'}`"
        )

    @dp.message(Command("grandfather"))
    async def cmd_grandfather(msg: Message):
        """
        Bulk-grant Pro to a user with custom duration. Same effect as /set_tier
        but semantic ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ for early-access promos to community members.

        Usage: /grandfather <user_id> [days=30] [tier=pro]
        """
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split()
        if len(parts) < 2:
            await msg.answer(
                "׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ©: `/grandfather <user_id> [days=30] [tier=pro]`\n\n"
                "׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ג„¢׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€”:\n"
                "  `/grandfather 224223270` ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Pro 30 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ\n"
                "  `/grandfather 224223270 90` ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ Pro 90 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ\n"
                "  `/grandfather 224223270 30 vip` ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ VIP 30 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ"
            )
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await msg.answer("user_id ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֻ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ¨.")
            return
        try:
            days = int(parts[2]) if len(parts) > 2 else 30
        except ValueError:
            days = 30
        tier = parts[3].lower() if len(parts) > 3 else "pro"
        if tier not in pricing.TIERS:
            await msg.answer(f"Tier ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ§׳³ֲ³ײ²ֲ£: {tier}. ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג€ֲ¢: {', '.join(pricing.TIERS.keys())}")
            return
        if days < 1 or days > 365:
            await msg.answer("days ׳³ֲ³׳’ג‚¬ֻ׳³ֲ³ײ»ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲײ²ֲ¿ײ²ֲ½- 1-365.")
            return

        sub = await subscriptions.upgrade(
            user_id=target_uid,
            tier=tier,
            provider="grandfather",
            payment_id=f"granted_by_{msg.from_user.id}_for_{days}d",
            period_days=days,
        )
        spec = pricing.TIERS[tier]
        await msg.answer(
            f"׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ *Grandfathered*\n\n"
            f"User: `{target_uid}`\n"
            f"Tier: *{spec.name_he}* ({tier})\n"
            f"׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֳ·׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג‚¬ֲ: {spec.monthly_quota or 'unlimited'} ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€”\n"
            f"׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ§׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג€ֳ-׳³ֲ³׳’ג‚¬ֲ: {days} ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ\n"
            f"׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¡׳³ֲ³ײ³ג€”׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ: `{sub.current_period_end[:10]}`\n\n"
            f"_׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½- ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢: ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ© ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֳ·׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֲ¢ Pro ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ {sub.current_period_end[:10]}. "
            f"׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½- /credits ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ§._"
        )

    @dp.message(Command("set_tier"))
    async def cmd_set_tier(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split()
        if len(parts) < 3:
            await msg.answer("׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ©: `/set_tier <user_id> <free|pro|vip|zvk>`")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await msg.answer("user_id ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֻ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€” ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ¡׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ¨.")
            return
        tier = parts[2].lower()
        if tier not in pricing.TIERS:
            await msg.answer(f"Tier ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ§׳³ֲ³ײ²ֲ£. ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€”: {', '.join(pricing.TIERS.keys())}")
            return
        await subscriptions.upgrade(
            user_id=target_uid,
            tier=tier,
            provider="manual",
            payment_id=f"admin_grant_by_{msg.from_user.id}",
        )
        await msg.answer(f"׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ User {target_uid} ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֳ·׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ-{tier}")

    @dp.message(Command("top_users"))
    async def cmd_top(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        async with aiosqlite.connect(subscriptions.DB_PATH) as db:
            cur = await db.execute(
                "SELECT user_id, COUNT(*), SUM(cost_usd_cents) "
                "FROM ai_usage WHERE created_at >= ? "
                "GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 10",
                (cutoff,),
            )
            rows = await cur.fetchall()
        if not rows:
            await msg.answer("׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ© ׳³ֲ³׳’ג‚¬ֻ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ© ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ׳³ֲײ²ֲ¿ײ²ֲ½-׳³ֲ³ײ²ֲ¨׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ.")
            return
        lines = ["׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ *Top 10 ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ©׳³ֲ³ײ³ג€”׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ©׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ 30 ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ*\n"]
        for i, (uid, msgs, cost_cents) in enumerate(rows, 1):
            cost_ils = (cost_cents or 0) / 100 * pricing.USD_ILS_RATE
            lines.append(f"{i}. `{uid}` ׳³ג€™׳’ג€ֲ¬׳’ג‚¬ֲ {msgs} ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ³ג€” (׳³ג€™׳’ג‚¬ֲײ³ג€”{cost_ils:.2f})")
        await msg.answer("\n".join(lines))

    log.info("admin_panel handlers registered")

