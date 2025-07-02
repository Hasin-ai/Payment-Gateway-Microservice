from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.routing import APIRoute
import httpx
import json
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.service_discovery import get_service_discovery
from app.utils.request_transformer import RequestTransformer
from app.utils.response_handler import ResponseHandler
from app.utils.cache_manager import CacheManager
from app.utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class ProxyRoute:
    def __init__(self, service_name: str, path_prefix: str):
        self.service_name = service_name
        self.path_prefix = path_prefix
        self.circuit_breaker = CircuitBreaker(service_name)
        self.cache_manager = CacheManager()
        self.request_transformer = RequestTransformer()
        self.response_handler = ResponseHandler()

    async def proxy_request(self, request: Request) -> Dict[str, Any]:
        """Proxy request to backend service"""
        try:
            # Get service URL from service discovery
            service_discovery = get_service_discovery()
            service_url = await service_discovery.get_service_url(self.service_name)
            
            if not service_url:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {self.service_name} not available"
                )
            
            # Extract path after prefix
            original_path = str(request.url.path)
            target_path = original_path.replace(self.path_prefix, "", 1)
            if not target_path.startswith("/"):
                target_path = "/" + target_path
            
            # Build target URL
            target_url = f"{service_url.rstrip('/')}{target_path}"
            if request.url.query:
                target_url += f"?{request.url.query}"
            
            # Check cache for GET requests
            if request.method == "GET" and settings.CACHE_ENABLED:
                cached_response = await self.cache_manager.get(target_url)
                if cached_response:
                    logger.info(f"Cache hit for {target_url}")
                    return cached_response
            
            # Transform request if needed
            headers = await self.request_transformer.transform_headers(dict(request.headers))
            body = None
            
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    try:
                        # Transform request body if needed
                        body_json = json.loads(body)
                        body_json = await self.request_transformer.transform_body(
                            body_json, self.service_name
                        )
                        body = json.dumps(body_json).encode()
                    except json.JSONDecodeError:
                        pass  # Keep original body if not JSON
            
            # Make request through circuit breaker
            response_data = await self.circuit_breaker.call(
                self._make_request,
                target_url,
                request.method,
                headers,
                body
            )
            
            # Cache GET responses
            if request.method == "GET" and settings.CACHE_ENABLED:
                await self.cache_manager.set(target_url, response_data, settings.CACHE_TTL)
            
            # Transform response if needed
            transformed_response = await self.response_handler.transform_response(
                response_data, self.service_name
            )
            
            return transformed_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to proxy request to {self.service_name}"
            )
    
    async def _make_request(
        self, 
        url: str, 
        method: str, 
        headers: Dict[str, str], 
        body: Optional[bytes]
    ) -> Dict[str, Any]:
        """Make actual HTTP request to backend service"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(settings.REQUEST_TIMEOUT)) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body
            )
            
            # Log request/response if enabled
            if settings.LOG_REQUESTS:
                logger.info(f"{method} {url} -> {response.status_code}")
            
            if settings.LOG_RESPONSES:
                logger.debug(f"Response: {response.text[:500]}...")
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}

def setup_routes(app: FastAPI):
    """Setup dynamic routes for all services"""
    
    # Service route configurations
    service_routes = [
        {"service": "user-service", "prefix": "/api/v1/auth", "description": "Authentication endpoints"},
        {"service": "user-service", "prefix": "/api/v1/users", "description": "User management"},
        {"service": "user-service", "prefix": "/api/v1/profile", "description": "User profile"},
        
        {"service": "transaction-service", "prefix": "/api/v1/transactions", "description": "Transaction management"},
        {"service": "transaction-service", "prefix": "/api/v1/limits", "description": "Payment limits"},
        {"service": "transaction-service", "prefix": "/api/v1/history", "description": "Transaction history"},
        
        {"service": "payment-service", "prefix": "/api/v1/sslcommerz", "description": "SSLCommerz payments"},
        {"service": "payment-service", "prefix": "/api/v1/paypal", "description": "PayPal payouts"},
        {"service": "payment-service", "prefix": "/api/v1/webhooks", "description": "Payment webhooks"},
        
        {"service": "exchange-rate-service", "prefix": "/api/v1/rates", "description": "Exchange rates"},
        
        {"service": "notification-service", "prefix": "/api/v1/notifications", "description": "Notifications"},
        {"service": "notification-service", "prefix": "/api/v1/preferences", "description": "Notification preferences"},
        {"service": "notification-service", "prefix": "/api/v1/templates", "description": "Notification templates"},
        
        {"service": "admin-service", "prefix": "/api/v1/admin", "description": "Admin operations"},
        
        {"service": "audit-service", "prefix": "/api/v1/audit", "description": "Audit logs"},
        {"service": "audit-service", "prefix": "/api/v1/analytics", "description": "Audit analytics"},
    ]
    
    # Create proxy routes
    for route_config in service_routes:
        service_name = route_config["service"]
        prefix = route_config["prefix"]
        
        proxy_route = ProxyRoute(service_name, prefix)
        
        # Create dynamic route handler with closure
        def create_route_handler(proxy: ProxyRoute):
            async def route_handler(request: Request):
                return await proxy.proxy_request(request)
            return route_handler
        
        route_handler = create_route_handler(proxy_route)
        
        # Add route for all HTTP methods
        app.add_api_route(
            f"{prefix}/{{path:path}}",
            route_handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            tags=[service_name],
            summary=f"Proxy to {service_name}",
            description=route_config["description"]
        )
        
        # Add route for exact prefix match (no additional path)
        app.add_api_route(
            prefix,
            route_handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            tags=[service_name],
            summary=f"Proxy to {service_name}",
            description=route_config["description"]
        )

    logger.info(f"Configured {len(service_routes)} proxy routes")
