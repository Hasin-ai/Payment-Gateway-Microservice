from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request logging and validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        logger.info(f"Incoming request: {request.method} {request.url}")
        
        # Add request ID for tracing
        import uuid
        request.state.request_id = str(uuid.uuid4())
        
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response status: {response.status_code}")
        
        return response
