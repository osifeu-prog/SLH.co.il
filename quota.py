"""
SLH AI Spark ×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×³â€™×’â€šÂ¬Ö²Â Quota middleware.

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
    use_anthropic: bool             # True ×³Â³×’â‚¬â„¢×³â€™×’â€šÂ¬Ö²Â ×³â€™×’â€šÂ¬×’â€žÂ¢ claude_client, False ×³Â³×’â‚¬â„¢×³â€™×’â€šÂ¬Ö²Â ×³â€™×’â€šÂ¬×’â€žÂ¢ free_ai_client
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
            f"×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬Ö²Âœ×²Â²Ö²ÂŠ *×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö³Â·×³Â³Ö²Â³×²Â²Ö²Â¡×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â© ×³Â³Ö²Â³×²Â²Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â* ×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×³â€™×’â€šÂ¬Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â³×’â‚¬â€×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ-{used}/{cap} ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€.\n\n"
            f"×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢ ×³Â³Ö²Â³×²Â²Ö²Âœ-Pro: 100 ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€/×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â© + Claude Sonnet 4.5 + tools.\n"
            f"×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬×’â€žÂ¢×²Â²Ö²ÂŽ *Pro ×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×³â€™×’â€šÂ¬Ö²Â ×³Â³×’â‚¬â„¢×³â€™×’â€šÂ¬Ö²Âš×²Â³×’â‚¬â€29/×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â©* (500 ×³Â³×’â‚¬â„¢×²Â²Ö²Â­×²Â²Ö²Â)\n\n"
            f"×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-: `/upgrade pro`"
        )
    if tier == "vip":
        return (
            f"×³Â³×’â‚¬â„¢×²Â²Ö²Âš×²Â²Ö²Â ×³Â³Ö²ÂŸ×²Â²Ö²Â¸×²Â²Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×²Â²Ö²Âœ-fair-use cap ×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Âœ {cap} ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â© (VIP unlimited).\n"
            f"×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â‚¬Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â ×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â²Ö²Â§×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â ×³Â³Ö²Â³×²Â²Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×³â€™×’â‚¬ÂžÖ²Â¢×³Â³Ö²Â³×²Â²Ö²Â¨ ×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×³â€™×’â€šÂ¬Ö²Â ×³Â³Ö²Â³×²Â²Ö²Â¦×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â²Ö²Â¨ ×³Â³Ö²Â³×²Â²Ö²Â§×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Â¨ ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×²Â²Ö²Â @osifeu_prog ×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â."
        )
    return (
        f"×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬Ö²Âœ×²Â²Ö²ÂŠ ×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö³Â·×³Â³Ö²Â³×²Â²Ö²Â¡×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â-{spec.name_he} ×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Âš ×³Â³Ö²Â³×²Â²Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â ({used}/{cap}).\n"
        f"×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â³×’â‚¬â€×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â© ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ-1 ×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â© ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ×³Â³Ö²Â³×²Â²Ö²Â, ×³Â³Ö²Â³×²Â²Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢ ×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢ ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×²Â²Ö²Â `/upgrade vip`."
    )


async def quota_status_he(user_id: int) -> str:
    """For /credits command ×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×³â€™×’â€šÂ¬Ö²Â show remaining quota."""
    sub = await subscriptions.get_or_create(user_id)
    spec = pricing.TIERS.get(sub.tier, pricing.TIERS["free"])
    cap = spec.monthly_quota if spec.monthly_quota > 0 else spec.fair_use_cap
    used = sub.messages_used_this_period
    remaining = max(0, cap - used)
    pct = (used / cap * 100) if cap else 0
    bar_len = 20
    filled = int(used / cap * bar_len) if cap else 0
    bar = "×³Â³×’â‚¬â„¢×³â€™×’â€šÂ¬×’â‚¬Âœ×²Â»×’â‚¬Â " * filled + "×³Â³×’â‚¬â„¢×³â€™×’â€šÂ¬×’â‚¬Âœ×³â€™×’â€šÂ¬Ö»Âœ" * (bar_len - filled)
    return (
        f"×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬Ö²Âœ×²Â²Ö²ÂŠ *Tier: {spec.name_he}*\n\n"
        f"`{bar}`\n"
        f"×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â³×’â‚¬â€×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ-{used}/{cap} ({pct:.0f}%)\n"
        f"×³Â³Ö²Â³×²Â²Ö²Â ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢: *{remaining}* ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â³×’â‚¬â€\n\n"
        f"×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×²Â³×’â‚¬â€×³Â³Ö²ÂŸ×²Â²Ö²Â¿×²Â²Ö²Â½-×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â©: `{sub.current_period_end[:10]}`"
    )

