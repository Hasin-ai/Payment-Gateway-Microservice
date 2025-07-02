from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip auth for health and docs endpoints
            if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
                await self.app(scope, receive, send)
                return
            
            # For now, just pass through
            # In production, implement proper service-to-service authentication
            
        await self.app(scope, receive, send)
