from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class NotificationRecord(Base):
    __tablename__ = "notification_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    
    # Channel and delivery info
    channel = Column(String(20), nullable=False)  # email, sms, push
    recipient = Column(String(255), nullable=False)  # email address, phone number, device token
    
    # Content
    subject = Column(String(255), nullable=True)  # for emails
    message_body = Column(Text, nullable=False)
    template_id = Column(Integer, nullable=True)
    template_data = Column(JSON, nullable=True)
    
    # Status and tracking
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    # PENDING, SENT, DELIVERED, FAILED, RETRY
    
    # Provider response
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationRecord(id={self.id}, user_id={self.user_id}, type={self.notification_type})>"
    
    def to_dict(self):
        """Convert notification record to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "status": self.status,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
        }

class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    
    # Notification type preferences
    transaction_alerts = Column(Boolean, default=True, nullable=False)
    payout_alerts = Column(Boolean, default=True, nullable=False)
    security_alerts = Column(Boolean, default=True, nullable=False)
    rate_change_alerts = Column(Boolean, default=False, nullable=False)
    limit_alerts = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Contact information
    email_address = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    push_token = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationPreferences(id={self.id}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "push_enabled": self.push_enabled,
            "transaction_alerts": self.transaction_alerts,
            "payout_alerts": self.payout_alerts,
            "security_alerts": self.security_alerts,
            "rate_change_alerts": self.rate_change_alerts,
            "limit_alerts": self.limit_alerts,
            "marketing_emails": self.marketing_emails,
            "email_address": self.email_address,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
