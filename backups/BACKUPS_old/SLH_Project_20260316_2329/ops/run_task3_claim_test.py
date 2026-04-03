import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import db
from app.services.tasks import get_tasks_overview, claim_task_reward

TEST_USER_ID = 900000001

async def main():
    await db.connect()
    try:
        overview = await get_tasks_overview(TEST_USER_ID)
        print("OVERVIEW=" + json.dumps(overview, ensure_ascii=False, default=str))

        result = await claim_task_reward(TEST_USER_ID, 3)
        print("CLAIM_RESULT=" + json.dumps(result, ensure_ascii=False, default=str))
    finally:
        if db.pool is not None:
            await db.pool.close()

if __name__ == "__main__":
    asyncio.run(main())