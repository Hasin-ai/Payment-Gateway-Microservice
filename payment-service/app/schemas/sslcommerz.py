from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class SSLCommerzInitiateRequest(BaseModel):
    transaction_id: int
    internal_tran_id: str
    total_amount: Decimal
    currency: str = "BDT"
    product_name: str
    product_category: str
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: str
    
    @validator("total_amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

class SSLCommerzInitiateResponse(BaseModel):
    sessionkey: str
    gateway_url: str
    redirect_url: str
    valid_till: datetime

class SSLCommerzPaymentStatus(BaseModel):
    transaction_id: int
    internal_tran_id: str
    sslcz_status: str
    amount_matched: bool
    validation_status: str
    payment_method: Optional[str] = None
    risk_assessment: Optional[str] = None
    processing_time: datetime
