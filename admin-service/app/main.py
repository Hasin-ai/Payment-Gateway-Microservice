from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio
import sys

from app.core.config import settings
from app.core.database import init_db, verify_db_connection
from app.api.v1 import dashboard, settings as settings_router, users, reports
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Admin Service...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Verify database connection
    db_connected = verify_db_connection()
    if not db_connected:
        logger.warning("Database connection verification failed - some features may not work correctly")
    else:
        logger.info("Database connection verified")
    
    try:
        # Initialize database
        if db_connected:
            logger.info("Initializing database...")
            await init_db()
            logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Application starting with limited functionality due to database issues")
    
    yield
    # Shutdown
    logger.info("Shutting down Admin Service...")

app = FastAPI(
    title="Payment Gateway - Admin Service",
    description="Administrative management service for payment gateway system",
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
app.include_router(dashboard.router, prefix="/api/v1/admin/dashboard", tags=["Dashboard"])
app.include_router(settings_router.router, prefix="/api/v1/admin/settings", tags=["Settings"])
app.include_router(users.router, prefix="/api/v1/admin/users", tags=["User Management"])
app.include_router(reports.router, prefix="/api/v1/admin/reports", tags=["Reports"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "admin-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway Admin Service", 
        "version": "1.0.0",
        "description": "Administrative management service"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
