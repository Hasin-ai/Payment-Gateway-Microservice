import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseHandler:
    def __init__(self):
        pass
    
    async def transform_response(
        self, 
        response_data: Dict[str, Any], 
        service_name: str
    ) -> Dict[str, Any]:
        """Transform response data from backend services"""
        
        # Ensure consistent response format
        if not isinstance(response_data, dict):
            response_data = {"data": response_data}
        
        # Add gateway metadata if not present
        if "success" not in response_data:
            response_data["success"] = True
        
        if "timestamp" not in response_data:
            response_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Service-specific transformations
        if service_name == "exchange-rate-service":
            response_data = await self._transform_exchange_rate_response(response_data)
        elif service_name == "payment-service":
            response_data = await self._transform_payment_response(response_data)
        elif service_name == "transaction-service":
            response_data = await self._transform_transaction_response(response_data)
        
        return response_data
    
    async def _transform_exchange_rate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform exchange rate service responses"""
        # Ensure rate data includes currency information
        if "data" in response and isinstance(response["data"], dict):
            rate_data = response["data"]
            if "rate_to_bdt" in rate_data and "currency_code" in rate_data:
                # Add formatted rate string
                rate_data["formatted_rate"] = f"1 {rate_data['currency_code']} = {rate_data['rate_to_bdt']} BDT"
        
        return response
    
    async def _transform_payment_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform payment service responses"""
        # Add payment status information
        if "data" in response and isinstance(response["data"], dict):
            payment_data = response["data"]
            
            # Standardize status messages
            if "status" in payment_data:
                status_messages = {
                    "PENDING": "Payment is being processed",
                    "COMPLETED": "Payment completed successfully",
                    "FAILED": "Payment failed",
                    "CANCELLED": "Payment was cancelled"
                }
                status = payment_data["status"]
                payment_data["status_message"] = status_messages.get(status, status)
        
        return response
    
    async def _transform_transaction_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform transaction service responses"""
        # Add calculated fields and formatting
        if "data" in response and isinstance(response["data"], dict):
            transaction_data = response["data"]
            
            # Add formatted amounts
            if "requested_foreign_amount" in transaction_data and "requested_foreign_currency" in transaction_data:
                amount = transaction_data["requested_foreign_amount"]
                currency = transaction_data["requested_foreign_currency"]
                transaction_data["formatted_foreign_amount"] = f"{amount:,.2f} {currency}"
            
            if "total_bdt_amount" in transaction_data:
                amount = transaction_data["total_bdt_amount"]
                transaction_data["formatted_bdt_amount"] = f"{amount:,.2f} BDT"
        
        return response
    
    def handle_error_response(
        self, 
        error: Exception, 
        service_name: str,
        request_path: str
    ) -> Dict[str, Any]:
        """Handle and format error responses"""
        error_response = {
            "success": False,
            "error": {
                "service": service_name,
                "path": request_path,
                "message": str(error),
                "type": type(error).__name__
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add specific error handling based on error type
        if hasattr(error, 'status_code'):
            error_response["error"]["status_code"] = error.status_code
        
        if hasattr(error, 'detail'):
            error_response["error"]["details"] = error.detail
        
        return error_response
