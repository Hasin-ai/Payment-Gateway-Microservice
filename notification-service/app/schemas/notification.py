from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class NotificationSend(BaseModel):
    user_id: int
    notification_type: str
    channels: List[str]  # ["email", "sms", "push"]
    template_data: Dict[str, Any]
    template_key: Optional[str] = None
    subject: Optional[str] = None
    message_body: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    priority: Optional[int] = 5
    
    @validator("channels")
    def validate_channels(cls, v):
        allowed_channels = ["email", "sms", "push"]
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"Invalid channel: {channel}. Allowed: {allowed_channels}")
        return v
    
    @validator("notification_type")
    def validate_notification_type(cls, v):
        allowed_types = [
            "transaction_created", "transaction_updated", "payment_received",
            "payment_completed", "payment_failed", "limit_exceeded",
            "security_alert", "rate_change", "welcome", "verification"
        ]
        if v not in allowed_types:
            raise ValueError(f"Invalid notification type: {v}")
        return v
    
    @validator("priority")
    def validate_priority(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Priority must be between 1 (highest) and 10 (lowest)")
        return v

class NotificationResponse(BaseModel):
    notification_id: str
    user_id: int
    notification_type: str
    channels_sent: List[Dict[str, Any]]
    status: str
    created_at: datetime

class NotificationStatus(BaseModel):
    id: int
    notification_type: str
    channel: str
    recipient: str
    status: str
    retry_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class BulkNotificationSend(BaseModel):
    notification_type: str
    user_ids: List[int]
    channels: List[str]
    template_data: Dict[str, Any]
    template_key: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    priority: Optional[int] = 5
    
    @validator("user_ids")
    def validate_user_ids(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum 1000 users per bulk notification")
        return v

class NotificationStats(BaseModel):
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    channels_breakdown: Dict[str, Dict[str, int]]
