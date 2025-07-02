from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response
        
        # For now, allow all requests
        # In production, implement proper JWT validation
        response = await call_next(request)
        return response
