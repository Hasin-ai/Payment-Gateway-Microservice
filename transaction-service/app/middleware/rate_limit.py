from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self._add_request(client_ip, current_time)
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Remove old requests outside the time window"""
        if client_ip in self.requests:
            cutoff_time = current_time - settings.RATE_LIMIT_WINDOW
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > cutoff_time
            ]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client has exceeded rate limit"""
        if client_ip not in self.requests:
            return False
        
        return len(self.requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS
    
    def _add_request(self, client_ip: str, current_time: float):
        """Add current request to tracking"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
