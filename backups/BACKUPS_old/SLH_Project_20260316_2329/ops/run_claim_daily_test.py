import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import db
from app.services.daily import claim_daily

TEST_USER_ID = 900000001
TEST_USERNAME = "finance_test_user"

async def main():
    await db.connect()
    try:
        result = await claim_daily(TEST_USER_ID, TEST_USERNAME)
        print(json.dumps(result, ensure_ascii=False, default=str))
    finally:
        if db.pool is not None:
            await db.pool.close()

if __name__ == "__main__":
    asyncio.run(main())