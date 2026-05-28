"""
?????? ????? Crypto-Class
"""

import os

class Config:
    """?????? ???????"""
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
    TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///crypto_class.db")
    USE_POLLING = os.environ.get("USE_POLLING", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """????? ?????? ???????"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN ?? ?????")
        
        if not cls.WEBHOOK_URL:
            errors.append("WEBHOOK_URL ?? ????? (????? ?-production)")
        
        if errors:
            raise ValueError("?????? ???????: " + ", ".join(errors))
        
        return True


