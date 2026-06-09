import os
import sys

REQUIRED = [
    "BOT_TOKEN",
    "DATABASE_URL",
    "REDIS_URL"
]

missing = [v for v in REQUIRED if not os.getenv(v)]

if missing:
    print("❌ Missing environment variables:")
    for m in missing:
        print(" -", m)
    sys.exit(1)

print("✅ Environment OK")
