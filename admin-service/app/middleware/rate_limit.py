from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: timestamps for ip, timestamps in self.clients.items()
            if any(ts > current_time - self.period for ts in timestamps)
        }
        
        # Check rate limit
        if client_ip in self.clients:
            self.clients[client_ip] = [
                ts for ts in self.clients[client_ip] 
                if ts > current_time - self.period
            ]
            
            if len(self.clients[client_ip]) >= self.calls:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
        else:
            self.clients[client_ip] = []
        
        self.clients[client_ip].append(current_time)
        response = await call_next(request)
        return response