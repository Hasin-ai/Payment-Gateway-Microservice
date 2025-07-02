import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/payment_gateway")
    
    def get_database_url(self) -> str:
        """Get database URL with fallback for local development"""
        db_url = self.DATABASE_URL
        
        # If running locally (not in Docker) and using 'postgres' hostname, 
        # replace with localhost
        if "postgres:5432" in db_url and not os.getenv("DOCKER_ENV"):
            db_url = db_url.replace("postgres:5432", "localhost:5432")
            
        return db_url
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Exchange Rate API Configuration
    EXCHANGE_RATE_API_KEY: str = os.getenv("EXCHANGE_RATE_API_KEY", "your-api-key")
    EXCHANGE_RATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    BACKUP_API_URL: str = "https://api.fxratesapi.com/latest"
    
    # Rate Update Configuration
    RATE_UPDATE_INTERVAL: int = int(os.getenv("RATE_UPDATE_INTERVAL", "900"))  # 15 minutes
    RATE_CACHE_DURATION: int = int(os.getenv("RATE_CACHE_DURATION", "600"))   # 10 minutes
    
    # Supported Currencies
    SUPPORTED_CURRENCIES: List[str] = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SGD"]
    BASE_CURRENCY: str = "BDT"
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "exchange-rate-service")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Service Fees
    DEFAULT_SERVICE_FEE_PERCENTAGE: float = 2.0
    
    class Config:
        env_file = ".env"

settings = Settings()
