from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import transactions, limits, history
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Transaction Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Transaction Service...")

app = FastAPI(
    title="Payment Gateway - Transaction Service",
    description="Transaction processing and payment limits management service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(limits.router, prefix="/api/v1/limits", tags=["Payment Limits"])
app.include_router(history.router, prefix="/api/v1/history", tags=["Transaction History"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "transaction-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway Transaction Service", 
        "version": "1.0.0",
        "description": "Transaction processing and payment limits management"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
