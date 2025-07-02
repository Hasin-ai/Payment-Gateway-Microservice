import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:hales@postgres:5432/transaction")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # External Service URLs
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    EXCHANGE_RATE_SERVICE_URL: str = os.getenv("EXCHANGE_RATE_SERVICE_URL", "http://exchange-rate-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "transaction-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Transaction Configuration
    DEFAULT_SERVICE_FEE_PERCENTAGE: float = 2.0
    MIN_TRANSACTION_AMOUNT_USD: float = 10.0
    MAX_TRANSACTION_AMOUNT_USD: float = 10000.0
    
    # Supported Currencies
    SUPPORTED_CURRENCIES: List[str] = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SGD"]
    
    # Default Payment Limits (USD)
    DEFAULT_DAILY_LIMIT: float = 5000.0
    DEFAULT_MONTHLY_LIMIT: float = 25000.0
    DEFAULT_YEARLY_LIMIT: float = 100000.0
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 200
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
