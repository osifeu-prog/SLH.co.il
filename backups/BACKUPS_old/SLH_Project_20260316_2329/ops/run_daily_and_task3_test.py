import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import db
from app.services.daily import claim_daily
from app.services.tasks import get_tasks_overview, claim_task_reward

TEST_USER_ID = 900000002
TEST_USERNAME = "finance_test_user_2"

async def main():
    await db.connect()
    try:
        daily_res = await claim_daily(TEST_USER_ID, TEST_USERNAME)
        print("DAILY_RESULT=" + json.dumps(daily_res, ensure_ascii=False, default=str))

        overview = await get_tasks_overview(TEST_USER_ID)
        print("OVERVIEW=" + json.dumps(overview, ensure_ascii=False, default=str))

        task_res = await claim_task_reward(TEST_USER_ID, 3)
        print("TASK3_RESULT=" + json.dumps(task_res, ensure_ascii=False, default=str))
    finally:
        if db.pool is not None:
            await db.pool.close()

if __name__ == "__main__":
    asyncio.run(main())