"""Telegram user ID allowlist. Supports multiple admin IDs (comma-separated)."""
import os


def _parse_admin_ids() -> set[int]:
    """
    Read admin IDs from env. New canonical var: ADMIN_TELEGRAM_IDS (plural,
    comma-separated). Legacy fallback: ADMIN_TELEGRAM_ID (singular).
    Default: Osif's two known IDs (224223270 = primary phone account,
    8789977826 = secondary account, confirmed self 2026-04-21).
    """
    raw = os.getenv("ADMIN_TELEGRAM_IDS", "").strip()
    if not raw:
        raw = os.getenv("ADMIN_TELEGRAM_ID", "224223270,8789977826").strip()
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


ADMIN_IDS: set[int] = _parse_admin_ids()


def is_authorized(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


def unauthorized_reply_he(telegram_id: int) -> str:
    allowed = ", ".join(str(i) for i in sorted(ADMIN_IDS))
    return (
        "×³Â³Ö²Â³×²Â²Ö²Â×³Â³Ö²Â³×³â€™×’â‚¬ÂžÖ²Â¢×³Â³Ö²Â³×²Â²Ö²ÂŸ ×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Âš ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×²Â²Ö²Â¨×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â ×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â‚¬ÂšÖ³-×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â‚¬ÂžÖ²Â¢×³Â³Ö²Â³×²Â²Ö²Âœ ×³Â³Ö²Â³×²Â²Ö²Â×³Â³Ö²Â³×²Â³×’â‚¬â€ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â»Ö²Âœ ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â‚¬Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â.\n"
        f"×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â»Ö²Âœ ×³Â³Ö²Â³×²Â²Ö²Âž×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬×’â€žÂ¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Â¨ ×³Â³Ö²Â³×²Â²Ö²Â¢×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö»Âœ×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â¢×³Â³Ö²Â³×²Â²Ö²Â¨: {allowed}\n"
        f"×³Â³Ö²Â³×³â€™×’â€šÂ¬Ö²Â-ID ×³Â³Ö²Â³×²Â²Ö²Â©×³Â³Ö²Â³×²Â²Ö²Âœ×³Â³Ö²Â³×²Â²Ö²Âš: {telegram_id}"
    )

