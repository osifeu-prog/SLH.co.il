"""Telegram user ID allowlist. Only Osif may talk to the bot."""
import os

ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "224223270"))


def is_authorized(telegram_id: int) -> bool:
    return telegram_id == ADMIN_ID


def unauthorized_reply_he(telegram_id: int) -> str:
    return (
        "אין לך הרשאה להפעיל את הבוט הזה.\n"
        f"הבוט הוגדר לעבוד רק עם משתמש {ADMIN_ID}.\n"
        f"ה-ID שלך: {telegram_id}"
    )
