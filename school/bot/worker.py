#!/usr/bin/env python3
"""
Worker process לבוט - מריץ את הבוט בפולינג (לגיבוי)
"""

import os
import sys
import logging
from bot.main import setup_bot

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """הרצת worker בפולינג"""
    logger.info("🚀 מפעיל worker בפולינג...")
    
    # אתחול הבוט
    bot_app = setup_bot()
    if bot_app:
        try:
            bot_app.run_polling(allowed_updates=None, drop_pending_updates=True)
        except Exception as e:
            logger.error(f"❌ שגיאה ב-worker: {e}")
            sys.exit(1)
    else:
        logger.error("❌ לא ניתן לאתחל את הבוט")
        sys.exit(1)

if __name__ == '__main__':
    main()

