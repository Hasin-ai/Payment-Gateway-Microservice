from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi(app) -> Dict[str, Any]:
    """Generate custom OpenAPI schema for the gateway"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Payment Gateway API",
        version="1.0.0",
        description="""
        ## Payment Gateway API
        
        Complete API for international payment processing from Bangladesh.
        
        ### Features
        - User authentication and management
        - International transaction processing
        - Real-time exchange rates
        - Payment gateway integrations (SSLCommerz, PayPal)
        - Multi-channel notifications
        - Administrative controls
        - Comprehensive audit logging
        
        ### Authentication
        Most endpoints require authentication using JWT tokens.
        
        ```
        Authorization: Bearer <token>
        ```
        
        ### Rate Limiting
        API requests are rate limited to prevent abuse:
        - 1000 requests per minute per authenticated user
        - 100 requests per minute per IP for unauthenticated requests
        
        ### Response Format
        All responses follow a consistent format:
        
        ```
        {
          "success": true,
          "message": "Operation completed successfully",
          "data": { ... },
          "timestamp": "2025-07-01T12:00:00Z"
        }
        ```
        
        ### Error Handling
        Errors are returned with appropriate HTTP status codes and detailed error information:
        
        ```
        {
          "success": false,
          "error": {
            "code": "ERROR_CODE",
            "message": "Human readable error message",
            "details": { ... }
          },
          "timestamp": "2025-07-01T12:00:00Z"
        }
        ```
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.paymentgateway.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.paymentgateway.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add tags
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Users",
            "description": "User management operations"
        },
        {
            "name": "Transactions",
            "description": "International payment transactions"
        },
        {
            "name": "Payments",
            "description": "Payment gateway integrations"
        },
        {
            "name": "Exchange Rates",
            "description": "Real-time currency exchange rates"
        },
        {
            "name": "Notifications",
            "description": "Multi-channel notification system"
        },
        {
            "name": "Administration",
            "description": "Administrative and system management"
        },
        {
            "name": "Audit",
            "description": "Audit logging and compliance"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
