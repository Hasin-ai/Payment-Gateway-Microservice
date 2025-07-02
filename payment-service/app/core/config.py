import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:hales@localhost:5432/payment")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    TRANSACTION_SERVICE_URL: str = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    AUDIT_SERVICE_URL: str = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8000")
    SSLCOMMERZ_STORE_ID: str = os.getenv("SSLCOMMERZ_STORE_ID", "testbox")
    SSLCOMMERZ_STORE_PASSWORD: str = os.getenv("SSLCOMMERZ_STORE_PASSWORD", "qwerty")
    SSLCOMMERZ_SANDBOX: bool = os.getenv("SSLCOMMERZ_SANDBOX", "true").lower() == "true"
    SSLCOMMERZ_SESSION_URL: str = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php" if SSLCOMMERZ_SANDBOX else "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
    SSLCOMMERZ_VALIDATION_URL: str = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php" if SSLCOMMERZ_SANDBOX else "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "your-paypal-client-id")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "your-paypal-client-secret")
    PAYPAL_SANDBOX: bool = os.getenv("PAYPAL_SANDBOX", "true").lower() == "true"
    
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com" if PAYPAL_SANDBOX else "https://api-m.paypal.com"
    SSLCOMMERZ_IPN_URL: str = os.getenv("SSLCOMMERZ_IPN_URL", "https://yourdomain.com/api/v1/webhooks/sslcommerz/ipn")
    PAYPAL_WEBHOOK_URL: str = os.getenv("PAYPAL_WEBHOOK_URL", "https://yourdomain.com/api/v1/webhooks/paypal")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "payment-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    RATE_LIMIT_REQUESTS: int = 300
    RATE_LIMIT_WINDOW: int = 60
    PAYMENT_TIMEOUT_MINUTES: int = 30
    PAYOUT_RETRY_ATTEMPTS: int = 3
    PAYOUT_RETRY_DELAY_SECONDS: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
