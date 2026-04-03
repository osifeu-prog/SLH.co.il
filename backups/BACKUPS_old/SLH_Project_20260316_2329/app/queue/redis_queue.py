import os
import json
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6380/0")
REDIS_STREAM = os.getenv("REDIS_STREAM", "slh:updates")

def get_redis() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)

async def enqueue_update(payload: dict) -> str:
    r = get_redis()
    try:
        update_id = payload.get("update_id")
        if update_id is not None:
            dedup_key = f"slh:update:{update_id}"
            inserted = await r.set(dedup_key, "1", ex=86400, nx=True)
            if not inserted:
                return "duplicate"

        msg_id = await r.xadd(
            REDIS_STREAM,
            {"update": json.dumps(payload, ensure_ascii=False)},
            maxlen=100000,
            approximate=True,
        )
        return msg_id
    finally:
        await r.aclose()