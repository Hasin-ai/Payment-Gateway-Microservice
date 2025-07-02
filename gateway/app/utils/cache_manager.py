import json
import logging
import redis.asyncio as redis
from typing import Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching"""
        if settings.CACHE_ENABLED:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    health_check_interval=30
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis for caching: {e}")
                self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(key)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key)
            cache_value = json.dumps(value, default=str)
            ttl = ttl or settings.CACHE_TTL
            
            await self.redis_client.setex(cache_key, ttl, cache_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key)
            result = await self.redis_client.delete(cache_key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            cache_pattern = f"gateway_cache:{pattern}"
            keys = await self.redis_client.keys(cache_pattern)
            
            if keys:
                return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
        
        return 0
    
    def _generate_cache_key(self, key: str) -> str:
        """Generate cache key with namespace"""
        return f"gateway_cache:{key}"
    
    def _should_cache_response(self, method: str, status_code: int) -> bool:
        """Determine if response should be cached"""
        # Only cache successful GET requests
        return method == "GET" and 200 <= status_code < 300
