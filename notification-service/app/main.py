from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import notifications, preferences, templates
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger
from app.tasks.notification_processor import NotificationProcessor

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Notification Service...")
    await init_db()
    
    # Start notification processor background task
    notification_processor = NotificationProcessor()
    processor_task = asyncio.create_task(notification_processor.start_processing())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Service...")
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Payment Gateway - Notification Service",
    description="Notification management service for email, SMS, and push notifications",
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
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["Preferences"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "notification-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway Notification Service", 
        "version": "1.0.0",
        "description": "Notification management service for multi-channel communications"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
