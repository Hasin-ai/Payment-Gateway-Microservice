from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import httpx
from typing import Dict, Any

from app.core.config import settings
from app.core.routing import setup_routes
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware
from app.services.service_discovery import initialize_service_discovery, set_service_discovery
from app.utils.logger import setup_logger
from app.utils.response_handler import ResponseHandler
from app.utils.exceptions import GatewayError

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting API Gateway...")
    
    # Initialize service discovery
    service_discovery = await initialize_service_discovery()
    app.state.service_discovery = service_discovery
    
    # Initialize HTTP client for service communication
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway...")
    await app.state.http_client.aclose()
    await service_discovery.close()

app = FastAPI(
    title="Payment Gateway - API Gateway",
    description="Central API Gateway for Payment Gateway Microservices",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global exception handler
@app.exception_handler(GatewayError)
async def gateway_exception_handler(request: Request, exc: GatewayError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": exc.timestamp.isoformat()
        }
    )

@app.exception_handler(httpx.HTTPError)
async def http_exception_handler(request: Request, exc: httpx.HTTPError):
    logger.error(f"HTTP error occurred: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Backend service temporarily unavailable",
                "details": str(exc)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": "Please contact support if this persists"
            }
        }
    )

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Setup dynamic routing
setup_routes(app)

@app.get("/health")
async def health_check():
    """Gateway health check with service status"""
    try:
        service_discovery = app.state.service_discovery
        service_status = await service_discovery.get_all_service_health()
        
        return {
            "status": "healthy",
            "service": "api-gateway",
            "version": "1.0.0",
            "services": service_status,
            "timestamp": "2025-07-01T05:23:00+06:00"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "api-gateway",
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint with gateway information"""
    return {
        "message": "Payment Gateway API",
        "version": "1.0.0",
        "description": "Central API Gateway for International Payment Services",
        "services": {
            "user-service": "User management and authentication",
            "transaction-service": "Transaction processing and limits",
            "payment-service": "Payment gateway integrations",
            "exchange-rate-service": "Real-time exchange rates",
            "notification-service": "Multi-channel notifications",
            "admin-service": "Administrative operations",
            "audit-service": "Audit logging and compliance"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/services")
async def list_services():
    """List all available services and their status"""
    try:
        service_discovery = app.state.service_discovery
        services = await service_discovery.discover_all_services()
        
        return {
            "success": True,
            "data": {
                "services": services,
                "total_services": len(services),
                "gateway_version": "1.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service information"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.GATEWAY_PORT,
        reload=settings.DEBUG
    )
    
