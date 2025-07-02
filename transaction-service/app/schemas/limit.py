from pydantic import BaseModel, validator
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal

class PaymentLimitCheck(BaseModel):
    currency_code: str
    amount: Decimal
    
    @validator("currency_code")
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
    
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

class PaymentLimitResponse(BaseModel):
    can_proceed: bool
    currency_code: str
    requested_amount: Decimal
    daily_limit: Decimal
    monthly_limit: Decimal
    yearly_limit: Decimal
    daily_remaining: Decimal
    monthly_remaining: Decimal
    yearly_remaining: Decimal
    limiting_factor: Optional[str] = None
    message: str

class PaymentLimitInfo(BaseModel):
    id: int
    user_id: int
    currency_code: str
    daily_limit: Decimal
    monthly_limit: Decimal
    yearly_limit: Decimal
    current_daily_used: Decimal
    current_monthly_used: Decimal
    current_yearly_used: Decimal
    daily_remaining: Decimal
    monthly_remaining: Decimal
    yearly_remaining: Decimal
    daily_reset_at: datetime
    monthly_reset_at: datetime
    yearly_reset_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaymentLimitUpdate(BaseModel):
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    yearly_limit: Optional[Decimal] = None
    
    @validator("daily_limit", "monthly_limit", "yearly_limit")
    def validate_limits(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Limit must be greater than 0")
        return v

class LimitUsageUpdate(BaseModel):
    currency_code: str
    amount: Decimal
    operation: str = "add"  # "add" or "subtract"
    
    @validator("currency_code")
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
    
    @validator("operation")
    def validate_operation(cls, v):
        if v not in ["add", "subtract"]:
            raise ValueError("Operation must be 'add' or 'subtract'")
        return v
