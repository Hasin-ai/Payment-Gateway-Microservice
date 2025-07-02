from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Check for authentication header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Authorization header required"}
            )
        
        # Validate token (simplified - implement proper JWT validation)
        try:
            token = auth_header.replace("Bearer ", "")
            # TODO: Implement proper JWT validation
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Authentication failed"}
            )
