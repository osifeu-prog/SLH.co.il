import json
import redis
from config import REDIS_URL

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_conversation(user_id: int) -> list:
    key = f"conv:{user_id}"
    data = redis_client.lrange(key, -10, -1)
    if data:
        return [json.loads(msg) for msg in data]
    return []

def add_to_conversation(user_id: int, role: str, content: str):
    key = f"conv:{user_id}"
    msg = json.dumps({"role": role, "content": content})
    redis_client.rpush(key, msg)
    redis_client.expire(key, 60 * 60)

def clear_conversation(user_id: int):
    key = f"conv:{user_id}"
    redis_client.delete(key)

