import httpx
import logging
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json

from app.models.exchange_rate import ExchangeRate, RateUpdateLog
from app.core.config import settings
from app.utils.cache import CacheManager

logger = logging.getLogger(__name__)

class RateFetcher:
    def __init__(self, db: Session):
        self.db = db
        self.cache = CacheManager()
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_rates_from_api(self, source: str = "primary") -> Dict[str, float]:
        """Fetch exchange rates from external API"""
        try:
            if source == "primary":
                url = f"{settings.EXCHANGE_RATE_API_URL}/{settings.EXCHANGE_RATE_API_KEY}/latest/BDT"
            else:
                url = f"{settings.BACKUP_API_URL}?base=BDT"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if source == "primary":
                # ExchangeRate-API format
                if data.get("result") != "success":
                    raise Exception(f"API returned error: {data.get('error-type')}")
                
                rates = {}
                conversion_rates = data.get("conversion_rates", {})
                
                for currency in settings.SUPPORTED_CURRENCIES:
                    if currency in conversion_rates:
                        # Convert to rate_to_bdt (inverse of the rate from BDT)
                        rates[currency] = 1 / conversion_rates[currency]
                
            else:
                # Backup API format
                rates = {}
                api_rates = data.get("rates", {})
                
                for currency in settings.SUPPORTED_CURRENCIES:
                    if currency in api_rates:
                        rates[currency] = 1 / api_rates[currency]
            
            return rates
            
        except Exception as e:
            logger.error(f"Failed to fetch rates from {source} API: {e}")
            raise
    
    async def update_single_rate(self, currency_code: str, rate_value: float, source: str) -> bool:
        """Update a single exchange rate in the database"""
        try:
            # Check if we need to update (rate is older than cache duration)
            existing_rate = self.db.query(ExchangeRate).filter(
                ExchangeRate.currency_code == currency_code,
                ExchangeRate.is_active == True
            ).order_by(ExchangeRate.last_updated.desc()).first()
            
            cache_duration = timedelta(seconds=settings.RATE_CACHE_DURATION)
            now = datetime.utcnow()
            
            if existing_rate and (now - existing_rate.last_updated.replace(tzinfo=None)) < cache_duration:
                logger.info(f"Rate for {currency_code} is still fresh, skipping update")
                return False
            
            # Create new rate entry
            new_rate = ExchangeRate(
                currency_code=currency_code,
                rate_to_bdt=rate_value,
                source=source,
                last_updated=now,
                expires_at=now + cache_duration,
                is_active=True
            )
            
            self.db.add(new_rate)
            
            # Deactivate old rates for this currency
            if existing_rate:
                existing_rate.is_active = False
            
            self.db.commit()
            
            # Cache the new rate
            await self.cache.set_rate(currency_code, rate_value, source)
            
            logger.info(f"Updated rate for {currency_code}: {rate_value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update rate for {currency_code}: {e}")
            self.db.rollback()
            return False
    
    async def update_all_rates(self, force: bool = False) -> Dict[str, Any]:
        """Update all supported currency rates"""
        start_time = datetime.utcnow()
        update_log = {
            "successful_updates": 0,
            "failed_updates": 0,
            "currencies_updated": [],
            "errors": []
        }
        
        try:
            # Try primary API first
            try:
                rates = await self.fetch_rates_from_api("primary")
                source = "ExchangeRate-API"
            except Exception as e:
                logger.warning(f"Primary API failed: {e}, trying backup")
                try:
                    rates = await self.fetch_rates_from_api("backup")
                    source = "FxRatesAPI"
                except Exception as backup_error:
                    logger.error(f"Both APIs failed. Backup error: {backup_error}")
                    raise Exception("All rate sources unavailable")
            
            # Update each currency rate
            for currency_code, rate_value in rates.items():
                try:
                    if force or await self._should_update_rate(currency_code):
                        success = await self.update_single_rate(currency_code, rate_value, source)
                        if success:
                            update_log["successful_updates"] += 1
                            update_log["currencies_updated"].append(currency_code)
                        else:
                            update_log["failed_updates"] += 1
                            update_log["errors"].append(f"Failed to update {currency_code}")
                except Exception as e:
                    update_log["failed_updates"] += 1
                    update_log["errors"].append(f"Error updating {currency_code}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to update rates: {e}")
            update_log["errors"].append(f"General update error: {str(e)}")
        
        # Log the update
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        await self._log_update(source, update_log, duration_ms)
        
        update_log["update_duration_ms"] = duration_ms
        update_log["source"] = source
        
        return update_log
    
    async def update_rates_background(self, currencies: List[str], force: bool = False):
        """Background task for updating rates"""
        try:
            if currencies:
                # Update specific currencies
                for currency in currencies:
                    if currency in settings.SUPPORTED_CURRENCIES:
                        rates = await self.fetch_rates_from_api("primary")
                        if currency in rates:
                            await self.update_single_rate(currency, rates[currency], "Manual Update")
            else:
                # Update all rates
                await self.update_all_rates(force)
                
        except Exception as e:
            logger.error(f"Background rate update failed: {e}")
    
    async def _should_update_rate(self, currency_code: str) -> bool:
        """Check if a rate should be updated based on age"""
        existing_rate = self.db.query(ExchangeRate).filter(
            ExchangeRate.currency_code == currency_code,
            ExchangeRate.is_active == True
        ).order_by(ExchangeRate.last_updated.desc()).first()
        
        if not existing_rate:
            return True
        
        cache_duration = timedelta(seconds=settings.RATE_CACHE_DURATION)
        return (datetime.utcnow() - existing_rate.last_updated.replace(tzinfo=None)) >= cache_duration
    
    async def _log_update(self, source: str, update_log: Dict[str, Any], duration_ms: int):
        """Log the rate update operation"""
        try:
            log_entry = RateUpdateLog(
                update_source=source,
                currencies_updated=json.dumps(update_log["currencies_updated"]),
                success_count=update_log["successful_updates"],
                error_count=update_log["failed_updates"],
                error_details=json.dumps(update_log["errors"]) if update_log["errors"] else None,
                update_duration_ms=duration_ms
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log rate update: {e}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
