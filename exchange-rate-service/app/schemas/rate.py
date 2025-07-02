from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class RateRequest(BaseModel):
    currency_code: str
    
    @validator("currency_code")
    def validate_currency_code(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()

class RateCalculationRequest(BaseModel):
    from_currency: str
    to_currency: str = "BDT"
    amount: Decimal
    service_fee_percentage: Optional[Decimal] = None
    
    @validator("from_currency", "to_currency")
    def validate_currency_codes(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
    
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
    
    @validator("service_fee_percentage")
    def validate_service_fee(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Service fee percentage must be between 0 and 100")
        return v

class ExchangeRateResponse(BaseModel):
    currency_code: str
    rate_to_bdt: Decimal
    source: Optional[str]
    last_updated: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class RateCalculationResponse(BaseModel):
    original_amount: Decimal
    from_currency: str
    to_currency: str
    exchange_rate: Decimal
    converted_amount: Decimal
    service_fee_percentage: Decimal
    service_fee_amount: Decimal
    total_amount: Decimal
    calculation_time: datetime

class MultipleRatesResponse(BaseModel):
    rates: List[ExchangeRateResponse]
    base_currency: str = "BDT"
    last_updated: datetime

class RateHistoryResponse(BaseModel):
    currency_code: str
    rates: List[ExchangeRateResponse]
    period_start: datetime
    period_end: datetime

class RateUpdateStatus(BaseModel):
    currency_code: str
    status: str  # success, failed, skipped
    rate: Optional[Decimal] = None
    error: Optional[str] = None
    updated_at: datetime

class BulkRateUpdateResponse(BaseModel):
    update_id: str
    total_currencies: int
    successful_updates: int
    failed_updates: int
    update_status: List[RateUpdateStatus]
    update_duration_ms: int
    timestamp: datetime
