"""
SLH AI Spark — Pricing Single Source of Truth
==============================================

Edit numbers HERE, not anywhere else. Anything that displays a price,
counts a quota, or calculates margin must import from this module.

Legal framing: this is SaaS — software service revenue. NOT a token sale,
NOT a security. Customers pay for AI access; SLH provides the integration.
Israeli VAT applies (17%, charged separately at invoicing).

Cost basis (Anthropic Claude Sonnet 4.5, current pricing):
- Input:  $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- Avg conversation: ~5K input + 1.5K output ≈ $0.038 ≈ ₪0.137

Fee model (Telegram Stars, withdrawal to fiat):
- Apple/Google IAP fee: 30% (mobile only, web is fee-free)
- Telegram bot revenue share: ~95% of net
- Effective realization rate: ~70% on mobile, ~95% on web
- We price *conservatively* assuming mobile.
"""
from dataclasses import dataclass
from typing import Literal

USD_ILS_RATE = 3.60  # update quarterly; small drift doesn't break the model


# ===== Cost side =====
ANTHROPIC_INPUT_USD_PER_MTOKEN = 3.00
ANTHROPIC_OUTPUT_USD_PER_MTOKEN = 15.00
AVG_CONVERSATION_INPUT_TOKENS = 5_000
AVG_CONVERSATION_OUTPUT_TOKENS = 1_500


def cost_per_message_usd() -> float:
    """Average Anthropic cost for a single conversation turn."""
    return (
        AVG_CONVERSATION_INPUT_TOKENS * ANTHROPIC_INPUT_USD_PER_MTOKEN / 1_000_000
        + AVG_CONVERSATION_OUTPUT_TOKENS * ANTHROPIC_OUTPUT_USD_PER_MTOKEN / 1_000_000
    )


def cost_per_message_ils() -> float:
    return cost_per_message_usd() * USD_ILS_RATE


# ===== Tier definitions =====
Tier = Literal["free", "pro", "vip", "zvk"]


@dataclass(frozen=True)
class TierSpec:
    """Single tier configuration. All numbers in here are normative."""
    name: Tier
    name_he: str
    price_ils: int            # nominal monthly price displayed to user
    price_stars: int          # Telegram Stars charged at /upgrade
    monthly_quota: int        # 0 = unlimited (subject to fair_use_cap)
    fair_use_cap: int         # hard cap on unlimited tiers (anti-abuse)
    ai_provider: str          # 'free' | 'anthropic'
    description_he: str


TIERS: dict[Tier, TierSpec] = {
    "free": TierSpec(
        name="free",
        name_he="חינם",
        price_ils=0,
        price_stars=0,
        monthly_quota=10,
        fair_use_cap=10,
        ai_provider="free",  # Groq/Gemini via free_ai_client
        description_he="10 הודעות/חודש · AI חינם (Groq/Gemini) · ללא tools",
    ),
    "pro": TierSpec(
        name="pro",
        name_he="Pro",
        price_ils=29,
        price_stars=500,
        monthly_quota=70,           # tuned 2026-04-25: 100 → 70 to keep ~50% margin
        fair_use_cap=70,
        ai_provider="anthropic",
        description_he="70 הודעות/חודש · Claude Sonnet 4.5 + tools · עדיפות בתור",
    ),
    "vip": TierSpec(
        name="vip",
        name_he="VIP",
        price_ils=99,
        price_stars=1500,
        monthly_quota=0,            # 0 = unlimited subject to fair_use_cap
        fair_use_cap=350,           # tuned 2026-04-25: 1000 → 350 for positive margin
        ai_provider="anthropic",
        description_he="ללא מכסה (fair-use 350) · Claude + tools · תמיכה ישירה",
    ),
    "zvk": TierSpec(
        name="zvk",
        name_he="ZVK Credits",
        price_ils=0,  # not purchased; earned
        price_stars=0,
        monthly_quota=0,
        fair_use_cap=0,
        ai_provider="anthropic",
        description_he="הודעה = 1 ZVK · רק earned-via-activity (Academia/quests)",
    ),
}


# ===== Margin math (for /revenue admin command) =====
def expected_margin_ils(tier: Tier, telegram_realization: float = 0.70) -> float:
    """
    Expected gross profit per active subscriber per month.

    telegram_realization: fraction of stated price that actually lands in SLH's
    pocket after Apple/Google IAP fee + Telegram revenue share. 0.70 is mobile,
    0.95 is web.
    """
    spec = TIERS[tier]
    if spec.price_ils == 0:
        return 0.0
    expected_revenue = spec.price_ils * telegram_realization
    quota_for_cost = spec.monthly_quota or spec.fair_use_cap
    expected_cost = quota_for_cost * cost_per_message_ils()
    return expected_revenue - expected_cost


def margin_pct(tier: Tier, telegram_realization: float = 0.70) -> float:
    spec = TIERS[tier]
    if spec.price_ils == 0:
        return 0.0
    margin = expected_margin_ils(tier, telegram_realization)
    return margin / (spec.price_ils * telegram_realization) * 100


# ===== Display helpers =====
def tier_summary_he(tier: Tier) -> str:
    spec = TIERS[tier]
    if tier == "free":
        return f"🆓 *{spec.name_he}* — חינם · {spec.description_he}"
    if tier == "zvk":
        return f"🪙 *{spec.name_he}* — utility · {spec.description_he}"
    margin = expected_margin_ils(tier)
    return (
        f"💎 *{spec.name_he}* — ₪{spec.price_ils}/חודש ({spec.price_stars} ⭐)\n"
        f"   {spec.description_he}\n"
        f"   _Margin צפוי: ₪{margin:.0f}/לקוח/חודש_"
    )


def all_tiers_summary_he() -> str:
    lines = ["*SLH AI Spark — חבילות:*\n"]
    for tier in ("free", "pro", "vip", "zvk"):
        lines.append(tier_summary_he(tier))
        lines.append("")
    lines.append(
        "_Forward-looking projection. ביצועי AI תלויים בעומס. לא ייעוץ השקעות._"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick sanity check — `python pricing.py`. ASCII-only for Windows cp1252.
    print(f"Cost / message: ILS {cost_per_message_ils():.3f}")
    for t in ("free", "pro", "vip"):
        print(f"  {t}: margin ILS {expected_margin_ils(t):+.2f} ({margin_pct(t):+.1f}%)")
