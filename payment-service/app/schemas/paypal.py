from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

class PayPalPayoutRequest(BaseModel):
    transaction_id: int
    recipient_email: str
    amount: Decimal
    currency: str = "USD"
    note: Optional[str] = None
    
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

class PayPalPayoutResponse(BaseModel):
    paypal_payout_id: str
    transaction_id: int
    recipient_email: str
    amount: Decimal
    currency: str
    status: str
    created_time: datetime
    links: List[Dict[str, Any]] = []

class PayPalPayoutStatus(BaseModel):
    payout_batch_id: Optional[str] = None
    payout_item_id: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_status: Optional[str] = None
    payout_batch_status: Optional[str] = None
    amount: Optional[Dict[str, Any]] = None
    fees: Optional[Dict[str, Any]] = None
    time_processed: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None
