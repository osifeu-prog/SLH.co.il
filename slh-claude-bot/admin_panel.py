"""
SLH AI Spark — Admin commands. Only admins (auth.is_authorized) may run these.

- /revenue                 → MRR + last 30d revenue + cost + net
- /quota_user <user_id>    → see/set quota for a user
- /set_tier <user_id> <tier> → manual tier upgrade (e.g., for grandfathered users)
- /anthropic_spend         → estimated Anthropic spend last 7/30 days
- /top_users               → top 10 users by AI message count this month
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
            f"  • {tier}: {count}"
            for tier, count in sorted(stats["tier_counts"].items())
        ) or "  (אין מנויים)"

        await msg.answer(
            f"💰 *Revenue Report — 30 ימים אחרונים*\n\n"
            f"*MRR:* `₪{mrr:,.2f}`\n"
            f"*Revenue 30d:* `₪{revenue_ils:,.2f}`\n"
            f"*Anthropic cost 30d:* `₪{anthropic_cost_ils:,.2f}` (${anthropic_cost_usd:,.2f})\n"
            f"*Net profit 30d:* `₪{net_ils:,.2f}`\n\n"
            f"*מנויים פעילים:*\n{tiers_str}\n\n"
            f"*Messages 30d:*\n"
            + "\n".join(f"  • {p}: {d['messages']}" for p, d in stats["usage_by_provider"].items())
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
                f"📊 *Anthropic Spend — {window}d*\n"
                f"  💵 ${cost_usd:,.2f} (~₪{cost_usd * pricing.USD_ILS_RATE:,.2f})\n"
                f"  📥 {tin:,} input tokens\n"
                f"  📤 {tout:,} output tokens"
            )

    @dp.message(Command("quota_user"))
    async def cmd_quota_user(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split()
        if len(parts) < 2:
            await msg.answer("שימוש: `/quota_user <user_id>`")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await msg.answer("user_id חייב להיות מספר.")
            return
        sub = await subscriptions.get_or_create(target_uid)
        spec = pricing.TIERS.get(sub.tier, pricing.TIERS["free"])
        cap = spec.monthly_quota or spec.fair_use_cap
        await msg.answer(
            f"👤 *User {target_uid}*\n"
            f"  Tier: `{sub.tier}` · {spec.name_he}\n"
            f"  Used: {sub.messages_used_this_period}/{cap}\n"
            f"  Period: `{sub.current_period_start[:10]}` → `{sub.current_period_end[:10]}`\n"
            f"  Provider: `{sub.payment_provider or 'none'}`"
        )

    @dp.message(Command("set_tier"))
    async def cmd_set_tier(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split()
        if len(parts) < 3:
            await msg.answer("שימוש: `/set_tier <user_id> <free|pro|vip|zvk>`")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await msg.answer("user_id חייב להיות מספר.")
            return
        tier = parts[2].lower()
        if tier not in pricing.TIERS:
            await msg.answer(f"Tier לא תקף. אפשרויות: {', '.join(pricing.TIERS.keys())}")
            return
        await subscriptions.upgrade(
            user_id=target_uid,
            tier=tier,
            provider="manual",
            payment_id=f"admin_grant_by_{msg.from_user.id}",
        )
        await msg.answer(f"✅ User {target_uid} עודכן ל-{tier}")

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
            await msg.answer("אין שימוש בחודש האחרון.")
            return
        lines = ["📊 *Top 10 משתמשים — 30 ימים*\n"]
        for i, (uid, msgs, cost_cents) in enumerate(rows, 1):
            cost_ils = (cost_cents or 0) / 100 * pricing.USD_ILS_RATE
            lines.append(f"{i}. `{uid}` — {msgs} הודעות (₪{cost_ils:.2f})")
        await msg.answer("\n".join(lines))

    log.info("admin_panel handlers registered")
