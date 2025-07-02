import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database - ensure we're using PostgreSQL, not SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:hales@localhost:5432/admin_service")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # External Service URLs
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    TRANSACTION_SERVICE_URL: str = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    EXCHANGE_RATE_SERVICE_URL: str = os.getenv("EXCHANGE_RATE_SERVICE_URL", "http://exchange-rate-service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "admin-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Admin Configuration
    SUPER_ADMIN_EMAIL: str = os.getenv("SUPER_ADMIN_EMAIL", "admin@paymentgateway.com")
    ADMIN_SESSION_TIMEOUT: int = int(os.getenv("ADMIN_SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # Report Configuration
    MAX_REPORT_RECORDS: int = 10000
    REPORT_CACHE_DURATION: int = 300  # 5 minutes
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 500
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
