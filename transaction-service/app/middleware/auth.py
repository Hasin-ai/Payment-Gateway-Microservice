from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and documentation endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response
        
        # For now, we'll let the dependency injection handle auth
        # This middleware can be used for additional auth logic if needed
        response = await call_next(request)
        return response
