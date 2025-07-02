import httpx
from decimal import Decimal
from datetime import datetime
from typing import Optional
import logging

from app.schemas.transaction import TransactionCalculation
from app.core.config import settings
from app.utils.exceptions import ValidationError, ExternalServiceError

logger = logging.getLogger(__name__)

class CalculationService:
    def __init__(self, db):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def calculate_transaction_amounts(
        self,
        from_currency: str,
        amount: Decimal,
        service_fee_percentage: Optional[Decimal] = None
    ) -> TransactionCalculation:
        """Calculate all transaction amounts including fees"""
        try:
            # Get current exchange rate
            exchange_rate = await self._get_exchange_rate(from_currency)
            
            # Calculate BDT amount
            calculated_bdt_amount = amount * exchange_rate
            
            # Calculate service fee
            fee_percentage = service_fee_percentage or Decimal(str(settings.DEFAULT_SERVICE_FEE_PERCENTAGE))
            service_fee_bdt = calculated_bdt_amount * (fee_percentage / 100)
            
            # Calculate total BDT amount
            total_bdt_amount = calculated_bdt_amount + service_fee_bdt
            
            return TransactionCalculation(
                requested_foreign_currency=from_currency,
                requested_foreign_amount=amount,
                exchange_rate_bdt=exchange_rate,
                calculated_bdt_amount=calculated_bdt_amount,
                service_fee_percentage=fee_percentage,
                service_fee_bdt=service_fee_bdt,
                total_bdt_amount=total_bdt_amount,
                calculation_time=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate transaction amounts: {e}")
            raise ValidationError("Failed to calculate transaction amounts")
    
    async def _get_exchange_rate(self, currency_code: str) -> Decimal:
        """Get current exchange rate from exchange rate service"""
        try:
            url = f"{settings.EXCHANGE_RATE_SERVICE_URL}/api/v1/rates/current"
            params = {"currency": currency_code}
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success", False):
                raise ExternalServiceError("Exchange rate service returned error")
            
            rate_data = data.get("data", {})
            rate_to_bdt = rate_data.get("rate_to_bdt")
            
            if not rate_to_bdt:
                raise ExternalServiceError("Invalid exchange rate data")
            
            return Decimal(str(rate_to_bdt))
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch exchange rate: {e}")
            raise ExternalServiceError("Exchange rate service unavailable")
        except Exception as e:
            logger.error(f"Exchange rate calculation error: {e}")
            raise ExternalServiceError("Failed to get exchange rate")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
