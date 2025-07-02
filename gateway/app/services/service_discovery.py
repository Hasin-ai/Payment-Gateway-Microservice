import asyncio
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class ServiceDiscovery:
    def __init__(self):
        self.services: Dict[str, str] = {}
        self.service_health: Dict[str, Dict] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize service discovery"""
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        
        # Load static service configuration
        self.services = {
            "user-service": settings.USER_SERVICE_URL,
            "transaction-service": settings.TRANSACTION_SERVICE_URL,
            "payment-service": settings.PAYMENT_SERVICE_URL,
            "exchange-rate-service": settings.EXCHANGE_RATE_SERVICE_URL,
            "notification-service": settings.NOTIFICATION_SERVICE_URL,
            "admin-service": settings.ADMIN_SERVICE_URL,
            "audit-service": settings.AUDIT_SERVICE_URL,
        }
        
        # Start health check background task
        self._health_check_task = asyncio.create_task(self._periodic_health_check())
        
        logger.info(f"Service discovery initialized with {len(self.services)} services")
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL by name"""
        service_url = self.services.get(service_name)
        
        if service_url and await self._is_service_healthy(service_name):
            return service_url
        
        logger.warning(f"Service {service_name} not available or unhealthy")
        return None
    
    async def discover_all_services(self) -> List[Dict[str, any]]:
        """Discover all available services"""
        services_info = []
        
        for service_name, service_url in self.services.items():
            health_info = self.service_health.get(service_name, {})
            
            services_info.append({
                "name": service_name,
                "url": service_url,
                "status": health_info.get("status", "unknown"),
                "last_check": health_info.get("last_check"),
                "response_time": health_info.get("response_time"),
                "version": health_info.get("version")
            })
        
        return services_info
    
    async def get_all_service_health(self) -> Dict[str, Dict]:
        """Get health status for all services"""
        return self.service_health.copy()
    
    async def _is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy"""
        health_info = self.service_health.get(service_name, {})
        
        # If we haven't checked recently, assume healthy for now
        last_check = self.last_health_check.get(service_name)
        if not last_check or datetime.utcnow() - last_check > timedelta(minutes=5):
            return True
        
        return health_info.get("status") == "healthy"
    
    async def _periodic_health_check(self):
        """Periodic health check for all services"""
        while True:
            try:
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
                await self._check_all_services_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_all_services_health(self):
        """Check health of all services"""
        tasks = []
        for service_name in self.services.keys():
            task = asyncio.create_task(self._check_service_health(service_name))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        if not self.http_client:
            return
        
        service_url = self.services.get(service_name)
        if not service_url:
            return
        
        health_url = f"{service_url.rstrip('/')}/health"
        
        try:
            start_time = datetime.utcnow()
            response = await self.http_client.get(health_url)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
            
            if response.status_code == 200:
                health_data = response.json()
                
                self.service_health[service_name] = {
                    "status": "healthy",
                    "last_check": datetime.utcnow().isoformat(),
                    "response_time": round(response_time, 2),
                    "version": health_data.get("version"),
                    "details": health_data
                }
            else:
                self.service_health[service_name] = {
                    "status": "unhealthy",
                    "last_check": datetime.utcnow().isoformat(),
                    "response_time": round(response_time, 2),
                    "error": f"HTTP {response.status_code}"
                }
            
            self.last_health_check[service_name] = datetime.utcnow()
            
        except Exception as e:
            self.service_health[service_name] = {
                "status": "unhealthy",
                "last_check": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            self.last_health_check[service_name] = datetime.utcnow()
            
            logger.warning(f"Health check failed for {service_name}: {e}")
    
    async def close(self):
        """Close service discovery"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.http_client:
            await self.http_client.aclose()

# Global service discovery instance
_service_discovery: Optional[ServiceDiscovery] = None

async def initialize_service_discovery() -> ServiceDiscovery:
    """Initialize and return service discovery instance"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.initialize()
    return _service_discovery

def get_service_discovery() -> ServiceDiscovery:
    """Get global service discovery instance"""
    if _service_discovery is None:
        raise RuntimeError("Service discovery not initialized. Call initialize_service_discovery() first.")
    return _service_discovery

def set_service_discovery(service_discovery: ServiceDiscovery):
    """Set global service discovery instance"""
    global _service_discovery
    _service_discovery = service_discovery
