import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ADMIN_ID = int(os.getenv("ADMIN_ID", "224223270").split()[0])
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
