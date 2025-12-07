import redis
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 1):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

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
