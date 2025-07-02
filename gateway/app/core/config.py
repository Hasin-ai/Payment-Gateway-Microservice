import os
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    # Gateway Configuration
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Service Discovery
    SERVICE_DISCOVERY_TYPE: str = os.getenv("SERVICE_DISCOVERY_TYPE", "static")  # static, consul, eureka
    
    # Static Service URLs (for development/simple deployment)
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    TRANSACTION_SERVICE_URL: str = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    EXCHANGE_RATE_SERVICE_URL: str = os.getenv("EXCHANGE_RATE_SERVICE_URL", "http://exchange-rate-service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    ADMIN_SERVICE_URL: str = os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8000")
    AUDIT_SERVICE_URL: str = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8000")
    
    # Database & Cache
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:halex@localhost:5432/gateway")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # CORS - Use string field to avoid JSON parsing
    ALLOWED_ORIGINS: Union[str, List[str]] = "*"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        # Handle string input (most common case)
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            # Split by comma and clean up whitespace
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
            return origins if origins else ["*"]
        
        # Handle list input (already processed)
        if isinstance(v, list):
            return v
        
        # Handle None or empty values
        if v is None or v == "":
            return ["*"]
        
        # Fallback to default
        return ["*"]
    
    # Request/Response Configuration
    MAX_REQUEST_SIZE: int = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 60
    
    # Caching
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_REQUESTS: bool = os.getenv("LOG_REQUESTS", "true").lower() == "true"
    LOG_RESPONSES: bool = os.getenv("LOG_RESPONSES", "false").lower() == "true"
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
