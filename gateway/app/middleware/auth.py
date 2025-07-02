from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.bearer = HTTPBearer(auto_error=False)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/services",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/webhooks/sslcommerz/ipn",
            "/api/v1/webhooks/sslcommerz/success",
            "/api/v1/webhooks/sslcommerz/fail",
            "/api/v1/webhooks/sslcommerz/cancel",
            "/api/v1/webhooks/paypal",
            "/api/v1/rates/current",  # Public exchange rates
        }
        
        # Admin-only endpoints
        self.admin_endpoints = {
            "/api/v1/admin",
            "/api/v1/audit",
            "/api/v1/analytics"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Extract and validate JWT token
        try:
            auth_result = await self._authenticate_request(request)
            if auth_result:
                request.state.user = auth_result["user"]
                request.state.token_payload = auth_result["payload"]
                
                # Check admin access for admin endpoints
                if self._is_admin_endpoint(request.url.path):
                    if auth_result["user"].get("role") not in ["admin", "support"]:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required"
                        )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing authentication token"
                )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        # Add user info to request headers for downstream services
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("id")
            if user_id:
                # Create new headers dict and add user info
                mutable_headers = dict(request.headers)
                mutable_headers["X-User-ID"] = str(user_id)
                mutable_headers["X-User-Role"] = request.state.user.get("role", "user")
                
                # Update request headers
                request._headers = mutable_headers
        
        response = await call_next(request)
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        # Exact match
        if path in self.public_endpoints:
            return True
        
        # Pattern matching for dynamic paths
        public_patterns = [
            "/api/v1/auth/",
            "/api/v1/webhooks/",
        ]
        
        return any(path.startswith(pattern) for pattern in public_patterns)
    
    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint requires admin access"""
        admin_patterns = [
            "/api/v1/admin/",
            "/api/v1/audit/",
            "/api/v1/analytics/"
        ]
        
        return any(path.startswith(pattern) for pattern in admin_patterns)
    
    async def _authenticate_request(self, request: Request) -> Optional[dict]:
        """Authenticate request and return user info"""
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Extract user information
            user_info = {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "is_verified": payload.get("is_verified", False)
            }
            
            return {
                "user": user_info,
                "payload": payload
            }
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
