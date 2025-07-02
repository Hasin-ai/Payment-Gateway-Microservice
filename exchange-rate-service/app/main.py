from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import rates
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger
from app.tasks.rate_updater import RateUpdater

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Exchange Rate Service...")
    await init_db()
    
    # Start rate updater background task
    rate_updater = RateUpdater()
    update_task = asyncio.create_task(rate_updater.start_periodic_updates())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Exchange Rate Service...")
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Payment Gateway - Exchange Rate Service",
    description="Real-time currency exchange rate service for international payments",
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
app.include_router(rates.router, prefix="/api/v1/rates", tags=["Exchange Rates"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "exchange-rate-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway Exchange Rate Service", 
        "version": "1.0.0",
        "description": "Real-time currency exchange rate service"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
