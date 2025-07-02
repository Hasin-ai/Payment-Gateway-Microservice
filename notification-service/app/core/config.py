import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/payment_gateway")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # External Service URLs
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    TRANSACTION_SERVICE_URL: str = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    
    # Email Configuration (SMTP)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "your-app-password")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Email Settings
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Payment Gateway")
    EMAIL_FROM_ADDRESS: str = os.getenv("EMAIL_FROM_ADDRESS", "noreply@paymentgateway.com")
    
    # SMS Configuration
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "twilio")  # twilio, nexmo, etc.
    SMS_API_KEY: str = os.getenv("SMS_API_KEY", "your-sms-api-key")
    SMS_API_SECRET: str = os.getenv("SMS_API_SECRET", "your-sms-api-secret")
    SMS_FROM_NUMBER: str = os.getenv("SMS_FROM_NUMBER", "+1234567890")
    
    # Twilio Configuration (if using Twilio)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "your-twilio-sid")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "your-twilio-token")
    
    # Firebase Configuration (for push notifications)
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "notification-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # JWT Configuration (for inter-service communication)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    # Notification Configuration
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 60
    BATCH_SIZE: int = 100
    QUEUE_PROCESSOR_INTERVAL: int = 5  # seconds
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Template Configuration
    TEMPLATE_CACHE_DURATION: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"

settings = Settings()
