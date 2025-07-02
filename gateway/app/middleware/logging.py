from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import json
import uuid
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        if settings.LOG_REQUESTS:
            await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        
        # Log response
        if settings.LOG_RESPONSES or response.status_code >= 400:
            await self._log_response(request, response, process_time, request_id)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Get user info if available
            user_info = None
            if hasattr(request.state, 'user'):
                user_info = {
                    "id": request.state.user.get("id"),
                    "username": request.state.user.get("username"),
                    "role": request.state.user.get("role")
                }
            
            # Prepare log data
            log_data = {
                "event": "request",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent"),
                "user": user_info,
                "headers": self._filter_sensitive_headers(dict(request.headers))
            }
            
            # Log request body for non-GET requests (but filter sensitive data)
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # Try to parse as JSON and filter sensitive fields
                        try:
                            body_json = json.loads(body)
                            log_data["body"] = self._filter_sensitive_data(body_json)
                        except json.JSONDecodeError:
                            log_data["body"] = "[Binary or non-JSON data]"
                except Exception:
                    log_data["body"] = "[Failed to read body]"
            
            logger.info(f"Request: {json.dumps(log_data, default=str)}")
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        process_time: float, 
        request_id: str
    ):
        """Log response details"""
        try:
            log_data = {
                "event": "response",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "response_headers": dict(response.headers)
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            logger.log(log_level, f"Response: {json.dumps(log_data, default=str)}")
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _filter_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter sensitive information from headers"""
        sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token"
        }
        
        filtered = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value
        
        return filtered
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """Filter sensitive information from request/response data"""
        if isinstance(data, dict):
            sensitive_fields = {
                "password", "token", "secret", "key", "authorization",
                "credit_card", "ssn", "pin", "otp"
            }
            
            filtered = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    filtered[key] = "[REDACTED]"
                else:
                    filtered[key] = self._filter_sensitive_data(value)
            return filtered
        
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        
        else:
            return data
