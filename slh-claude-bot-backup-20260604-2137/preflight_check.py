import os
import sys

checks = {
    "BOT_TOKEN": os.getenv("BOT_TOKEN"),
    "DATABASE_URL": os.getenv("DATABASE_URL"),
    "REDIS_URL": os.getenv("REDIS_URL"),
}

print("🔍 Running preflight check...")

failed = False

for k, v in checks.items():
    if not v:
        print(f"❌ Missing: {k}")
        failed = True
    else:
        print(f"✅ {k} OK")

if failed:
    print("🚨 Deployment blocked")
    sys.exit(1)

print("✅ All systems go")
