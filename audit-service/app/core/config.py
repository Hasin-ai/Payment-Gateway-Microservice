import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:hales@localhost:5432/audit_service")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://admin:admin123@localhost:5672")
    
    # External Service URLs (for audit context)
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    TRANSACTION_SERVICE_URL: str = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "audit-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # JWT Configuration (for inter-service communication)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    # Audit Configuration
    MAX_AUDIT_BATCH_SIZE: int = 1000
    AUDIT_RETENTION_DAYS: int = 365  # 1 year retention
    AUDIT_QUEUE_NAME: str = "audit_events"
    AUDIT_PROCESSOR_INTERVAL: int = 5  # seconds
    
    # Sensitive Data Masking
    MASK_SENSITIVE_DATA: bool = True
    SENSITIVE_FIELDS: List[str] = [
        "password", "password_hash", "token", "secret", 
        "api_key", "private_key", "credit_card", "ssn"
    ]
    
    # Compliance Settings
    COMPLIANCE_MODE: str = os.getenv("COMPLIANCE_MODE", "strict")  # strict, standard, minimal
    LOG_DATA_CHANGES: bool = True
    LOG_FAILED_ATTEMPTS: bool = True
    LOG_ADMIN_ACTIONS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 500
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Alert Configuration
    CRITICAL_ACTION_ALERT: bool = True
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 10  # failed attempts per hour
    
    class Config:
        env_file = ".env"

settings = Settings()
