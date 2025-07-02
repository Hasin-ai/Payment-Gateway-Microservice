import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RequestTransformer:
    def __init__(self):
        self.service_transformations = {
            "user-service": self._transform_user_service,
            "transaction-service": self._transform_transaction_service,
            "payment-service": self._transform_payment_service,
            "notification-service": self._transform_notification_service,
        }
    
    async def transform_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Transform request headers"""
        # Remove hop-by-hop headers
        hop_by_hop_headers = {
            "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"
        }
        
        transformed_headers = {}
        for key, value in headers.items():
            if key.lower() not in hop_by_hop_headers:
                transformed_headers[key] = value
        
        # Add gateway identification
        transformed_headers["X-Gateway"] = "payment-gateway-v1.0.0"
        transformed_headers["X-Forwarded-By"] = "api-gateway"
        
        return transformed_headers
    
    async def transform_body(self, body: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Transform request body based on target service"""
        transformer = self.service_transformations.get(service_name)
        if transformer:
            return await transformer(body)
        return body
    
    async def _transform_user_service(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform requests for user service"""
        # Add any user service specific transformations
        return body
    
    async def _transform_transaction_service(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform requests for transaction service"""
        # Add transaction service specific transformations
        # Example: Ensure amounts are properly formatted
        if "requested_foreign_amount" in body:
            try:
                body["requested_foreign_amount"] = float(body["requested_foreign_amount"])
            except (ValueError, TypeError):
                pass
        
        return body
    
    async def _transform_payment_service(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform requests for payment service"""
        # Add payment service specific transformations
        return body
    
    async def _transform_notification_service(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform requests for notification service"""
        # Add notification service specific transformations
        return body
