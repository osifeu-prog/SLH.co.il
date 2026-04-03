import redis
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
    
    def set_user_state(self, telegram_id, state):
        """שמור את מצב המשתמש"""
        key = f"user:{telegram_id}:state"
        self.redis.setex(key, 3600, state)  # תפוגה: שעה
    
    def get_user_state(self, telegram_id):
        """קבל את מצב המשתמש"""
        key = f"user:{telegram_id}:state"
        return self.redis.get(key)
    
    def delete_user_state(self, telegram_id):
        """מחק את מצב המשתמש"""
        key = f"user:{telegram_id}:state"
        self.redis.delete(key)
    
    def cache_api_response(self, key, data, ttl=300):
        """שמור מטמון לתגובת API"""
        self.redis.setex(key, ttl, json.dumps(data))
    
    def get_cached_response(self, key):
        """קבל תגובת API ממטמון"""
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def increment_counter(self, key):
        """הגדר מונה"""
        return self.redis.incr(key)

redis_client = RedisClient()
