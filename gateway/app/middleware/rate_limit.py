from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis_client: redis.Redis = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for rate limiting"""
        if settings.RATE_LIMIT_ENABLED:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    health_check_interval=30
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                self.redis_client = None
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or not self.redis_client:
            return await call_next(request)
        
        # Skip rate limiting for health checks and static content
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        try:
            # Check rate limit
            await self._check_rate_limit(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        try:
            limit_info = await self._get_rate_limit_info(request)
            if limit_info:
                response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
                response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(limit_info["reset_time"])
                response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW)
        except Exception as e:
            logger.error(f"Failed to add rate limit headers: {e}")
        
        return response
    
    async def _check_rate_limit(self, request: Request):
        """Check if request exceeds rate limit"""
        # Generate rate limit key
        rate_limit_key = self._get_rate_limit_key(request)
        
        # Get current count from Redis
        pipe = self.redis_client.pipeline()
        pipe.get(rate_limit_key)
        pipe.ttl(rate_limit_key)
        results = await pipe.execute()
        
        current_count = int(results[0] or 0)
        ttl = results[1]
        
        # Check if limit exceeded
        if current_count >= settings.RATE_LIMIT_REQUESTS:
            # Calculate reset time
            reset_time = int(datetime.utcnow().timestamp()) + max(ttl, 0)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": settings.RATE_LIMIT_REQUESTS,
                    "window": settings.RATE_LIMIT_WINDOW,
                    "reset_time": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(max(ttl, 1))
                }
            )
        
        # Increment counter
        pipe = self.redis_client.pipeline()
        pipe.incr(rate_limit_key)
        if ttl == -1:  # Key doesn't have expiration
            pipe.expire(rate_limit_key, settings.RATE_LIMIT_WINDOW)
        await pipe.execute()
    
    async def _get_rate_limit_info(self, request: Request) -> Dict[str, int]:
        """Get current rate limit information"""
        rate_limit_key = self._get_rate_limit_key(request)
        
        pipe = self.redis_client.pipeline()
        pipe.get(rate_limit_key)
        pipe.ttl(rate_limit_key)
        results = await pipe.execute()
        
        current_count = int(results[0] or 0)
        ttl = results[1]
        
        return {
            "limit": settings.RATE_LIMIT_REQUESTS,
            "current": current_count,
            "remaining": max(settings.RATE_LIMIT_REQUESTS - current_count, 0),
            "reset_time": int(datetime.utcnow().timestamp()) + max(ttl, 0)
        }
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key for request"""
        # Use different strategies for rate limiting
        
        # Strategy 1: User-based rate limiting (if authenticated)
        user_id = getattr(request.state, 'user', {}).get('id') if hasattr(request.state, 'user') else None
        if user_id:
            window_start = int(datetime.utcnow().timestamp()) // settings.RATE_LIMIT_WINDOW
            return f"rate_limit:user:{user_id}:{window_start}"
        
        # Strategy 2: IP-based rate limiting (for unauthenticated requests)
        client_ip = self._get_client_ip(request)
        window_start = int(datetime.utcnow().timestamp()) // settings.RATE_LIMIT_WINDOW
        return f"rate_limit:ip:{client_ip}:{window_start}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (from load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
