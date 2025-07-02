from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, users, profile
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting User Service...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # You might want to exit the application here if database init fails
        # import sys
        # sys.exit(1)
    yield
    # Shutdown
    logger.info("Shutting down User Service...")

app = FastAPI(
    title="Payment Gateway - User Service",
    description="User management and authentication service for payment gateway system",
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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "user-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway User Service", 
        "version": "1.0.0",
        "description": "User management and authentication service"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
