from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_key = Column(String(100), unique=True, nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template content
    channel = Column(String(20), nullable=False)  # email, sms, push
    subject_template = Column(String(500), nullable=True)  # for emails
    body_template = Column(Text, nullable=False)
    
    # Template variables
    required_variables = Column(JSON, nullable=True)  # List of required template variables
    optional_variables = Column(JSON, nullable=True)  # List of optional template variables
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    category = Column(String(50), nullable=True)  # transaction, security, marketing, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, key={self.template_key})>"
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            "id": self.id,
            "template_key": self.template_key,
            "template_name": self.template_name,
            "description": self.description,
            "channel": self.channel,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "required_variables": self.required_variables,
            "optional_variables": self.optional_variables,
            "is_active": self.is_active,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
