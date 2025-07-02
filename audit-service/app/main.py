from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import audit, analytics
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.tasks.audit_processor import AuditProcessor
from app.utils.logger import setup_logger
import asyncio

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Audit Service...")
    await init_db()
    
    # Start audit processor background task
    audit_processor = AuditProcessor()
    processor_task = asyncio.create_task(audit_processor.start_processing())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Audit Service...")
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Payment Gateway - Audit Service",
    description="Audit logging and compliance service for payment gateway system",
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
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Audit Analytics"])

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy", 
        "service": "audit-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Payment Gateway Audit Service", 
        "version": "1.0.0",
        "description": "Comprehensive audit logging and compliance service"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )
