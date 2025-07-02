from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict
from typing import Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, list] = defaultdict(list)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "message": "Rate limit exceeded",
                    "retry_after": self.window_seconds
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
