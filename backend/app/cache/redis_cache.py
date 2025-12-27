import os
import redis
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self):
        redis_url = os.getenv("REDIS_CACHE_URL")

        if redis_url:
            print("🔌 USING UPSTASH REDIS (TCP)")
            print("REDIS_CACHE_URL =", redis_url)
            self.client = redis.from_url(
                redis_url,
                decode_responses=True
            )
        else:
            print("⚠️ USING LOCAL DOCKER REDIS")
            self.client = redis.Redis(
                host="redis",
                port=6379,
                db=1,
                decode_responses=True
            )


    def get(self, key: str) -> Optional[Any]:
        data = self.client.get(key)
        if data is None:
            return None
        return json.loads(data)

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self.client.set(key, json.dumps(value), ex=ttl_seconds)

    def delete(self, key: str):
        self.client.delete(key)

cache = RedisCache()

