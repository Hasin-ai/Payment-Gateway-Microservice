import os
from pydantic_settings import BaseSettings
from typing import Optional, Any
from pydantic import model_validator
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://alex:hales@localhost:5432/user_service_db")
    
    @model_validator(mode='after')
    def validate_database_url(self) -> 'Settings':
        """Validate and update database URL."""
        url = self.DATABASE_URL
        
        try:
            # For local development, force host to localhost if it's 'postgres'
            if "@postgres" in url:
                url = url.replace("@postgres", "@localhost")
                logger.info("Updated database host from 'postgres' to 'localhost' for local development")

            # Ensure postgresql:// prefix (not postgres://)
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
                logger.info("Updated database URL scheme from 'postgres://' to 'postgresql://'")
            
            # Validate URL format
            if not url.startswith("postgresql://"):
                raise ValueError("DATABASE_URL must start with 'postgresql://'")
            
            # Basic validation - ensure it contains required components
            if "@" not in url or "/" not in url.split("@")[1]:
                raise ValueError("DATABASE_URL format is invalid. Expected format: postgresql://user:password@host:port/database")
            
            self.DATABASE_URL = url
            logger.info(f"Database URL validated successfully: {url.split('@')[0]}@***")
            
        except Exception as e:
            logger.error(f"Database URL validation failed: {e}")
            raise ValueError(f"Invalid DATABASE_URL: {e}")
        
        return self

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "user-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Password Configuration
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    PASSWORD_REQUIRE_NUMBER: bool = os.getenv("PASSWORD_REQUIRE_NUMBER", "true").lower() == "true"
    PASSWORD_REQUIRE_UPPER: bool = os.getenv("PASSWORD_REQUIRE_UPPER", "true").lower() == "true"
    
    # Session Configuration
    SESSION_EXPIRE_HOURS: int = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))
    MAX_SESSIONS_PER_USER: int = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Email Configuration (for verification)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", EMAIL_USERNAME)
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    
    # External Service URLs
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
    AUDIT_SERVICE_URL: str = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8000")
    
    # Database Connection Pool Settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    DB_CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
    DB_COMMAND_TIMEOUT: int = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
    
    # Database retry settings
    DB_RETRY_ATTEMPTS: int = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
    DB_RETRY_DELAY: int = int(os.getenv("DB_RETRY_DELAY", "1"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        """Additional validation for all settings."""
        # Validate pool sizes
        if self.DB_POOL_SIZE < 1:
            raise ValueError("DB_POOL_SIZE must be at least 1")
        if self.DB_MAX_OVERFLOW < 0:
            raise ValueError("DB_MAX_OVERFLOW must be non-negative")
        
        # Validate timeouts
        if self.DB_POOL_TIMEOUT < 1:
            raise ValueError("DB_POOL_TIMEOUT must be at least 1 second")
        if self.DB_CONNECT_TIMEOUT < 1:
            raise ValueError("DB_CONNECT_TIMEOUT must be at least 1 second")
        
        # Validate JWT settings
        if self.JWT_EXPIRE_MINUTES < 1:
            raise ValueError("JWT_EXPIRE_MINUTES must be at least 1")
        if self.JWT_REFRESH_EXPIRE_DAYS < 1:
            raise ValueError("JWT_REFRESH_EXPIRE_DAYS must be at least 1")
        
        # Validate password requirements
        if self.PASSWORD_MIN_LENGTH < 1:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 1")
        
        # Log configuration in debug mode
        if self.DEBUG:
            logger.debug("Settings validation completed successfully")
        
        return self
    
    @property
    def database_url_masked(self) -> str:
        """Return database URL with password masked for logging."""
        if "@" in self.DATABASE_URL:
            parts = self.DATABASE_URL.split("@")
            user_pass = parts[0].split("://")[1]
            if ":" in user_pass:
                user = user_pass.split(":")[0]
                return f"postgresql://{user}:***@{parts[1]}"
        return self.DATABASE_URL

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

# Create global settings instance
settings = Settings()

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT
)