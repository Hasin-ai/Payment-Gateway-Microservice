import redis
import json
import logging
from typing import Optional, Any
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    async def get_rate(self, currency_code: str) -> Optional[dict]:
        """Get cached exchange rate"""
        if not self.enabled:
            return None
        
        try:
            key = f"rate:{currency_code}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            
        except Exception as e:
            logger.warning(f"Failed to get cached rate for {currency_code}: {e}")
        
        return None
    
    async def set_rate(self, currency_code: str, rate_value: float, source: str):
        """Cache exchange rate"""
        if not self.enabled:
            return
        
        try:
            key = f"rate:{currency_code}"
            data = {
                "currency_code": currency_code,
                "rate_to_bdt": rate_value,
                "source": source,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Cache for rate cache duration
            self.redis_client.setex(
                key,
                settings.RATE_CACHE_DURATION,
                json.dumps(data)
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache rate for {currency_code}: {e}")
    
    async def invalidate_rate(self, currency_code: str):
        """Invalidate cached rate"""
        if not self.enabled:
            return
        
        try:
            key = f"rate:{currency_code}"
            self.redis_client.delete(key)
            
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for {currency_code}: {e}")
    
    async def get_all_cached_rates(self) -> dict:
        """Get all cached rates"""
        if not self.enabled:
            return {}
        
        try:
            keys = self.redis_client.keys("rate:*")
            rates = {}
            
            for key in keys:
                currency_code = key.split(":")[1]
                cached_data = self.redis_client.get(key)
                if cached_data:
                    rates[currency_code] = json.loads(cached_data)
            
            return rates
            
        except Exception as e:
            logger.warning(f"Failed to get all cached rates: {e}")
            return {}
