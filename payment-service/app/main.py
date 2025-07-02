from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import sslcommerz, paypal, webhooks
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Payment Service...")
    try:
        await init_db()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Service starting without database initialization")
    yield
    logger.info("Shutting down Payment Service...")

app = FastAPI(
    title="Payment Gateway - Payment Service",
    description="Payment processing service for SSLCommerz and PayPal integrations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(sslcommerz.router, prefix="/api/v1/sslcommerz", tags=["SSLCommerz"])
app.include_router(paypal.router, prefix="/api/v1/paypal", tags=["PayPal"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "payment-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Payment Gateway Payment Service", 
        "version": "1.0.0",
        "description": "Payment processing service for international transfers"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
