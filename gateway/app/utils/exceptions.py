from datetime import datetime
from typing import Any, Dict, Optional

class GatewayError(Exception):
    """Base exception for gateway errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "GATEWAY_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

class ServiceUnavailableError(GatewayError):
    """Raised when a backend service is unavailable"""
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service {service_name} is temporarily unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details or {"service": service_name}
        )

class AuthenticationError(GatewayError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED"
        )

class AuthorizationError(GatewayError):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="ACCESS_DENIED"
        )

class RateLimitExceededError(GatewayError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )

class ValidationError(GatewayError):
    """Raised when request validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )
