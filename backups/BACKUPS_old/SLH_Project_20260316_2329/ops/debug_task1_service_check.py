import asyncio
from app.db.database import db
from app.services.task_verifications import request_task_verification
from app.services.tasks import get_tasks_overview

USER_ID = 7757102350

async def main():
    await db.connect()
    try:
        tasks = await get_tasks_overview(USER_ID)
        print("TASKS_OVERVIEW=", tasks)
        res = await request_task_verification(USER_ID, 1)
        print("REQUEST_TASK_VERIFICATION=", res)
    finally:
        await db.close()

asyncio.run(main())