from datetime import datetime, timedelta
from typing import Any, Optional
import json
from flask import current_app
import redis

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=current_app.config.get('REDIS_HOST', 'localhost'),
            port=current_app.config.get('REDIS_PORT', 6379),
            db=current_app.config.get('REDIS_DB', 0),
            decode_responses=True
        )
        self.default_timeout = 3600  # 1 hour

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            current_app.logger.error(f"Cache get error: {str(e)}")
            return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            timeout = timeout or self.default_timeout
            return self.redis_client.setex(
                key,
                timeout,
                json.dumps(value)
            )
        except Exception as e:
            current_app.logger.error(f"Cache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {str(e)}")
            return False

    def clear_group_cache(self, group_id: int) -> bool:
        """Clear all cache entries for a specific group."""
        try:
            pattern = f"group:{group_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except Exception as e:
            current_app.logger.error(f"Cache clear error: {str(e)}")
            return False

    def get_or_set(self, key: str, func, timeout: Optional[int] = None) -> Any:
        """Get from cache or set if not exists."""
        try:
            data = self.get(key)
            if data is not None:
                return data
            
            # Generate new data
            data = func()
            if data is not None:
                self.set(key, data, timeout)
            return data
        except Exception as e:
            current_app.logger.error(f"Cache get_or_set error: {str(e)}")
            return None