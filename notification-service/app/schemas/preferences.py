from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    transaction_alerts: Optional[bool] = None
    payout_alerts: Optional[bool] = None
    security_alerts: Optional[bool] = None
    rate_change_alerts: Optional[bool] = None
    limit_alerts: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    push_token: Optional[str] = None
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v and not v.startswith("+880"):
            raise ValueError("Phone number must start with +880 for Bangladesh")
        return v

class NotificationPreferencesResponse(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    transaction_alerts: bool
    payout_alerts: bool
    security_alerts: bool
    rate_change_alerts: bool
    limit_alerts: bool
    marketing_emails: bool
    email_address: Optional[str]
    phone_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ContactInfoUpdate(BaseModel):
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    push_token: Optional[str] = None
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v and not v.startswith("+880"):
            raise ValueError("Phone number must start with +880 for Bangladesh")
        return v
