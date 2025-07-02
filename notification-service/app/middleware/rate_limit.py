from fastapi import Request, HTTPException, status
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app
        self.requests = defaultdict(deque)
        self.window_size = 60  # 1 minute
        self.max_requests = 1000
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip rate limiting for health checks
            if request.url.path == "/health":
                await self.app(scope, receive, send)
                return
            
            # Get client IP
            client_ip = request.client.host
            now = time.time()
            
            # Clean old requests
            while (self.requests[client_ip] and 
                   now - self.requests[client_ip][0] > self.window_size):
                self.requests[client_ip].popleft()
            
            # Check rate limit
            if len(self.requests[client_ip]) >= self.max_requests:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Rate limit exceeded"}
                )
                await response(scope, receive, send)
                return
            
            # Add current request
            self.requests[client_ip].append(now)
        
        await self.app(scope, receive, send)
