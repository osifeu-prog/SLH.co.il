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
        "׳³ֲ³ײ²ֲ׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג€ֳ-׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג€ֲ¢׳³ֲ³ײ²ֲ ׳³ֲ³ײ²ֲ׳³ֲ³ײ³ג€” ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ»ֲ ׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ג€׳³ֲ³׳’ג‚¬ֲ.\n"
        f"׳³ֲ³׳’ג‚¬ֲ׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ»ֲ ׳³ֲ³ײ²ֲ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³׳’ג‚¬ג„¢׳³ֲ³׳’ג‚¬ֲ׳³ֲ³ײ²ֲ¨ ׳³ֲ³ײ²ֲ¢׳³ֲ³׳’ג‚¬ֻ׳³ֲ³׳’ג‚¬ֲ¢׳³ֲ³ײ²ֲ¨: {allowed}\n"
        f"׳³ֲ³׳’ג‚¬ֲ-ID ׳³ֲ³ײ²ֲ©׳³ֲ³ײ²ֲ׳³ֲ³ײ²ֲ: {telegram_id}"
    )

