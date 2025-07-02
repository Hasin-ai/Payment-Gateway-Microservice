from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    
    # Queue metadata
    priority = Column(Integer, default=5, nullable=False)  # 1 = highest, 10 = lowest
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    
    # Payload
    template_key = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)
    subject = Column(String(255), nullable=True)
    message_body = Column(Text, nullable=True)
    
    # Processing status
    status = Column(String(20), default="QUEUED", nullable=False, index=True)
    # QUEUED, PROCESSING, COMPLETED, FAILED
    
    processing_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationQueue(id={self.id}, user_id={self.user_id}, type={self.notification_type})>"
