"""
SLH AI Spark — Quota middleware.

Sits between the Telegram message handler and the AI client. Decides:
1. Does this user have quota left this month?
2. Which AI provider should answer? (free vs anthropic, based on tier)
3. After the response: log usage + increment counter.

Usage in bot.py on_text:

    decision = await quota.check(user_id)
    if not decision.allowed:
        await msg.answer(decision.refusal_he)
        return
    # ... call AI client (decision.use_anthropic tells you which) ...
    await quota.record(user_id, chat_id, decision.tier, provider, model,
                       tokens_in, tokens_out, cost_usd_cents)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pricing
import subscriptions


@dataclass
class QuotaDecision:
    allowed: bool
    tier: str                       # 'free' | 'pro' | 'vip' | 'zvk'
    use_anthropic: bool             # True → claude_client, False → free_ai_client
    refusal_he: Optional[str]       # message to send the user if not allowed
    quota_remaining: int            # informational; for /credits command
    quota_total: int


async def check(user_id: int) -> QuotaDecision:
    """Pre-flight check before invoking the AI."""
    sub = await subscriptions.get_or_create(user_id)
    spec = pricing.TIERS.get(sub.tier, pricing.TIERS["free"])

    # Hard cap: monthly_quota=0 means "unlimited up to fair_use_cap"
    cap = spec.monthly_quota if spec.monthly_quota > 0 else spec.fair_use_cap
    used = sub.messages_used_this_period
    remaining = max(0, cap - used)

    if remaining <= 0:
        return QuotaDecision(
            allowed=False,
            tier=sub.tier,
            use_anthropic=False,
            refusal_he=_quota_exhausted_message(sub.tier, used, cap),
            quota_remaining=0,
            quota_total=cap,
        )

    return QuotaDecision(
        allowed=True,
        tier=sub.tier,
        use_anthropic=(spec.ai_provider == "anthropic"),
        refusal_he=None,
        quota_remaining=remaining,
        quota_total=cap,
    )


async def record(user_id: int, chat_id: int, tier: str, provider: str,
                 model: Optional[str], tokens_in: int, tokens_out: int,
                 cost_usd_cents: int) -> None:
    """Post-flight: log the usage row + bump the counter."""
    await subscriptions.record_usage(
        user_id=user_id,
        chat_id=chat_id,
        tier=tier,
        provider=provider,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd_cents=cost_usd_cents,
    )
    await subscriptions.increment_usage_counter(user_id)


def _quota_exhausted_message(tier: str, used: int, cap: int) -> str:
    """Hebrew message + upgrade prompt when quota runs out."""
    spec = pricing.TIERS.get(tier, pricing.TIERS["free"])
    if tier == "free":
        return (
            f"📊 *מכסת חודש נגמרה* — השתמשת ב-{used}/{cap} הודעות.\n\n"
            f"שדרוג ל-Pro: 100 הודעות/חודש + Claude Sonnet 4.5 + tools.\n"
            f"💎 *Pro — ₪29/חודש* (500 ⭐)\n\n"
            f"שלח: `/upgrade pro`"
        )
    if tier == "vip":
        return (
            f"⚠️ הגעת ל-fair-use cap של {cap} הודעות החודש (VIP unlimited).\n"
            f"זה מקרה נדיר — צור קשר עם @osifeu_prog להעלאה."
        )
    return (
        f"📊 מכסת ה-{spec.name_he} שלך נגמרה ({used}/{cap}).\n"
        f"מתחדש ב-1 לחודש הבא, או שדרג עם `/upgrade vip`."
    )


async def quota_status_he(user_id: int) -> str:
    """For /credits command — show remaining quota."""
    sub = await subscriptions.get_or_create(user_id)
    spec = pricing.TIERS.get(sub.tier, pricing.TIERS["free"])
    cap = spec.monthly_quota if spec.monthly_quota > 0 else spec.fair_use_cap
    used = sub.messages_used_this_period
    remaining = max(0, cap - used)
    pct = (used / cap * 100) if cap else 0
    bar_len = 20
    filled = int(used / cap * bar_len) if cap else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return (
        f"📊 *Tier: {spec.name_he}*\n\n"
        f"`{bar}`\n"
        f"השתמשת ב-{used}/{cap} ({pct:.0f}%)\n"
        f"נותרו: *{remaining}* הודעות\n\n"
        f"מתחדש: `{sub.current_period_end[:10]}`"
    )
