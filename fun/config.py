import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE = os.getenv("WEBHOOK_BASE")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-123")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
GROUP_MONITOR_ID = int(os.getenv("GROUP_MONITOR_ID", "-1001748319682"))
GROUP_PREMIUM_INVITE_LINK = os.getenv("GROUP_PREMIUM_INVITE_LINK", "https://t.me/+e8GeOmh0CD82ZmI0")

# SLH Starter Pack pricing (April 2026 launch campaign)
PRICE_ILS = 22.221
PRICE_TEXT = "5.35 TON"  # ₪22.221 at April 2026 rates (1 TON ≈ $1.37, 1 USD ≈ 3.03 ILS)
BANK_DETAILS = "המוטב: קאופמן צביקה · בנק לאומי · סניף הרצליה (948) · חשבון 738009"
ALT_TELEGRAM_ROUTE = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"  # TON wallet
COMPANY_BSC_WALLET = "0xd061de73B06d5E91bfA46b35EfB7B08b16903da4"  # BSC/BNB receiving wallet
SLH_BSC_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"  # SLH token on BSC
ASSETS_PROMO_IMAGE_PATH = "assets/promo_image.jpg"
