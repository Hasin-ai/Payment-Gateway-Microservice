from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.models.exchange_rate import ExchangeRate
from app.schemas.rate import RateCalculationRequest, RateCalculationResponse
from app.core.config import settings
from app.utils.exceptions import RateNotFoundError, ValidationError

logger = logging.getLogger(__name__)

class RateService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_current_rate(self, currency_code: str) -> Optional[ExchangeRate]:
        """Get the most recent active exchange rate for a currency"""
        rate = self.db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.currency_code == currency_code,
                ExchangeRate.is_active == True
            )
        ).order_by(desc(ExchangeRate.last_updated)).first()
        
        if rate and rate.is_expired():
            logger.warning(f"Rate for {currency_code} has expired")
            # Still return the rate but log the expiration
        
        return rate
    
    async def get_all_current_rates(self) -> List[ExchangeRate]:
        """Get current exchange rates for all supported currencies"""
        rates = []
        for currency in settings.SUPPORTED_CURRENCIES:
            rate = await self.get_current_rate(currency)
            if rate:
                rates.append(rate)
        
        return rates
    
    async def calculate_bdt_amount(self, request: RateCalculationRequest) -> RateCalculationResponse:
        """Calculate BDT amount from foreign currency with service fees"""
        if request.from_currency == "BDT":
            raise ValidationError("Cannot convert from BDT to BDT")
        
        # Get current exchange rate
        rate = await self.get_current_rate(request.from_currency)
        if not rate:
            raise RateNotFoundError(f"Exchange rate not available for {request.from_currency}")
        
        # Calculate converted amount
        exchange_rate = rate.rate_to_bdt
        converted_amount = request.amount * exchange_rate
        
        # Calculate service fee
        service_fee_percentage = request.service_fee_percentage or Decimal(settings.DEFAULT_SERVICE_FEE_PERCENTAGE)
        service_fee_amount = converted_amount * (service_fee_percentage / 100)
        
        # Calculate total amount
        total_amount = converted_amount + service_fee_amount
        
        return RateCalculationResponse(
            original_amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            exchange_rate=exchange_rate,
            converted_amount=converted_amount,
            service_fee_percentage=service_fee_percentage,
            service_fee_amount=service_fee_amount,
            total_amount=total_amount,
            calculation_time=datetime.utcnow()
        )
    
    async def get_rate_history(self, currency_code: str, start_date: datetime, end_date: datetime) -> List[ExchangeRate]:
        """Get exchange rate history for a currency within a date range"""
        rates = self.db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.currency_code == currency_code,
                ExchangeRate.last_updated >= start_date,
                ExchangeRate.last_updated <= end_date
            )
        ).order_by(desc(ExchangeRate.last_updated)).all()
        
        return rates
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health information about the rate service"""
        health_info = {
            "status": "healthy",
            "currencies_supported": len(settings.SUPPORTED_CURRENCIES),
            "supported_currencies": settings.SUPPORTED_CURRENCIES,
            "rates_status": {}
        }
        
        for currency in settings.SUPPORTED_CURRENCIES:
            rate = await self.get_current_rate(currency)
            if rate:
                health_info["rates_status"][currency] = {
                    "available": True,
                    "last_updated": rate.last_updated.isoformat(),
                    "is_expired": rate.is_expired(),
                    "source": rate.source
                }
            else:
                health_info["rates_status"][currency] = {
                    "available": False,
                    "last_updated": None,
                    "is_expired": True,
                    "source": None
                }
        
        # Calculate overall health
        available_rates = sum(1 for status in health_info["rates_status"].values() if status["available"])
        if available_rates == 0:
            health_info["status"] = "critical"
        elif available_rates < len(settings.SUPPORTED_CURRENCIES) * 0.8:
            health_info["status"] = "warning"
        
        return health_info
    
    async def compare_currencies(self, base_currency: str, target_currencies: List[str], amount: float) -> Dict[str, Any]:
        """Compare exchange rates across multiple currencies"""
        if base_currency == "BDT":
            # Converting from BDT to other currencies
            comparisons = []
            for target_currency in target_currencies:
                rate = await self.get_current_rate(target_currency)
                if rate:
                    converted_amount = Decimal(amount) / rate.rate_to_bdt
                    comparisons.append({
                        "currency": target_currency,
                        "rate": float(rate.rate_to_bdt),
                        "converted_amount": float(converted_amount),
                        "available": True
                    })
                else:
                    comparisons.append({
                        "currency": target_currency,
                        "rate": None,
                        "converted_amount": None,
                        "available": False
                    })
        else:
            # Converting from foreign currency to BDT and other currencies
            base_rate = await self.get_current_rate(base_currency)
            if not base_rate:
                raise RateNotFoundError(f"Base currency rate not available: {base_currency}")
            
            bdt_amount = Decimal(amount) * base_rate.rate_to_bdt
            
            comparisons = [{
                "currency": "BDT",
                "rate": float(base_rate.rate_to_bdt),
                "converted_amount": float(bdt_amount),
                "available": True
            }]
            
            for target_currency in target_currencies:
                if target_currency == base_currency:
                    continue
                    
                target_rate = await self.get_current_rate(target_currency)
                if target_rate:
                    # Convert BDT to target currency
                    converted_amount = bdt_amount / target_rate.rate_to_bdt
                    comparisons.append({
                        "currency": target_currency,
                        "rate": float(target_rate.rate_to_bdt),
                        "converted_amount": float(converted_amount),
                        "available": True
                    })
                else:
                    comparisons.append({
                        "currency": target_currency,
                        "rate": None,
                        "converted_amount": None,
                        "available": False
                    })
        
        return {
            "base_currency": base_currency,
            "base_amount": amount,
            "comparisons": comparisons,
            "comparison_time": datetime.utcnow().isoformat()
        }
