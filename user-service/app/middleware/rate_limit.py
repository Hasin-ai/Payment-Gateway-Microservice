from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(deque)
        self.window = 60  # 60 seconds
        self.max_requests = 100  # per window
    
    async def dispatch(self, request: Request, call_next):
        # Simple in-memory rate limiting
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean old requests
        while self.requests[client_ip] and self.requests[client_ip][0] < now - self.window:
            self.requests[client_ip].popleft()
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response
