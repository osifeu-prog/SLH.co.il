import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import db
from app.services.bootstrap import ensure_user_exists, attach_referrer, grant_referral_reward_for_user
from app.services.daily import claim_daily
from app.services.task_verifications import request_task_verification, review_task_verification

PARENT_ID = 900000010
CHILD_ID = 900000011

async def main():
    await db.connect()
    try:
        res = {}

        res["ensure_parent"] = await ensure_user_exists(PARENT_ID, "ref_parent_u10")
        res["ensure_child"] = await ensure_user_exists(CHILD_ID, "ref_child_u11")

        res["attach_referrer"] = await attach_referrer(CHILD_ID, PARENT_ID)
        res["child_daily"] = await claim_daily(CHILD_ID, "ref_child_u11")
        res["grant_referral_reward"] = await grant_referral_reward_for_user(CHILD_ID)

        res["verify_request"] = await request_task_verification(CHILD_ID, 1)
        res["verify_approve"] = await review_task_verification(
            admin_user_id=PARENT_ID,
            user_id=CHILD_ID,
            task_id=1,
            approve=True,
            review_note="controlled_test",
        )

        print(json.dumps(res, ensure_ascii=False, default=str, indent=2))
    finally:
        if db.pool is not None:
            await db.pool.close()

if __name__ == "__main__":
    asyncio.run(main())