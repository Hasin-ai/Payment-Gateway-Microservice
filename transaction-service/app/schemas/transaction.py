from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

class TransactionCreate(BaseModel):
    requested_foreign_currency: str
    requested_foreign_amount: Decimal
    recipient_paypal_email: EmailStr
    payment_purpose: Optional[str] = None
    
    @validator("requested_foreign_currency")
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
    
    @validator("requested_foreign_amount")
    def validate_amount(cls, v):
        if v <= Decimal("10.0"):
            raise ValueError("Minimum transaction amount is 10.00")
        if v > Decimal("10000.0"):
            raise ValueError("Maximum transaction amount is 10,000.00")
        return v

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    internal_tran_id: str
    requested_foreign_currency: str
    requested_foreign_amount: Decimal
    recipient_paypal_email: str
    payment_purpose: Optional[str]
    exchange_rate_bdt: Decimal
    calculated_bdt_amount: Decimal
    service_fee_bdt: Decimal
    total_bdt_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    bdt_received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sslcommerz_payment_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    sslcz_tran_id: Optional[str] = None
    sslcz_val_id: Optional[str] = None
    sslcz_received_bdt_amount: Optional[Decimal] = None
    paypal_payout_tran_id: Optional[str] = None
    paypal_payout_status: Optional[str] = None
    failure_reason: Optional[str] = None

class TransactionStatusUpdate(BaseModel):
    new_status: str
    change_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator("new_status")
    def validate_status(cls, v):
        allowed_statuses = [
            "PENDING", "BDT_RECEIVED", "PROCESSING", 
            "COMPLETED", "FAILED", "CANCELLED", "REFUNDED"
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

class TransactionCalculation(BaseModel):
    requested_foreign_currency: str
    requested_foreign_amount: Decimal
    exchange_rate_bdt: Decimal
    calculated_bdt_amount: Decimal
    service_fee_percentage: Decimal
    service_fee_bdt: Decimal
    total_bdt_amount: Decimal
    calculation_time: datetime

class TransactionList(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool

class TransactionStats(BaseModel):
    total_transactions: int
    completed_transactions: int
    pending_transactions: int
    failed_transactions: int
    total_volume_bdt: Decimal
    total_volume_foreign: Decimal
    average_transaction_size: Decimal
