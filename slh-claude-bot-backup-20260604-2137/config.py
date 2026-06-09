import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

    @staticmethod
    def validate():
        required = [
            "BOT_TOKEN",
            "DATABASE_URL",
        ]

        missing = [r for r in required if not os.getenv(r)]

        if missing:
            raise RuntimeError(f"Missing env vars: {missing}")

Config.validate()
