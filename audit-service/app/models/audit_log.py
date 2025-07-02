from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET, JSONB
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Can be null for system actions
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    table_name = Column(String(50), nullable=True)
    record_id = Column(Integer, nullable=True)
    
    # Data changes
    old_data = Column(JSONB, nullable=True)
    new_data = Column(JSONB, nullable=True)
    
    # Request context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Service context
    service_name = Column(String(50), nullable=True)
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    
    # Additional metadata
    meta_data = Column(JSONB, nullable=True)
    severity = Column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    category = Column(String(50), nullable=True)  # authentication, transaction, payment, admin
    
    # Compliance and security
    compliance_tags = Column(JSONB, nullable=True)  # PCI, GDPR, etc.
    is_sensitive = Column(Boolean, default=False)
    is_successful = Column(Boolean, nullable=True)  # True, False, null for non-action logs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert audit log to dictionary with optional sensitive data filtering"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "service_name": self.service_name,
            "endpoint": self.endpoint,
            "method": self.method,
            "severity": self.severity,
            "category": self.category,
            "compliance_tags": self.compliance_tags,
            "is_sensitive": self.is_sensitive,
            "is_successful": self.is_successful,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        # Include sensitive data only if explicitly requested and authorized
        if include_sensitive or not self.is_sensitive:
            data["old_data"] = self.old_data
            data["new_data"] = self.new_data
            data["meta_data"] = self.meta_data
        else:
            data["old_data"] = "[REDACTED]" if self.old_data else None
            data["new_data"] = "[REDACTED]" if self.new_data else None
            data["meta_data"] = "[REDACTED]" if self.meta_data else None
        
        return data

class AuditQueue(Base):
    __tablename__ = "audit_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Queue metadata
    event_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=5)  # 1 = highest, 10 = lowest
    
    # Event data
    payload = Column(JSONB, nullable=False)
    source_service = Column(String(50), nullable=True)
    
    # Processing status
    status = Column(String(20), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    processing_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<AuditQueue(id={self.id}, event_type='{self.event_type}', status='{self.status}')>"

# Create indexes for better performance
Index('idx_audit_logs_user_action', AuditLog.user_id, AuditLog.action)
Index('idx_audit_logs_table_record', AuditLog.table_name, AuditLog.record_id)
Index('idx_audit_logs_created_severity', AuditLog.created_at, AuditLog.severity)
Index('idx_audit_logs_category_created', AuditLog.category, AuditLog.created_at)
Index('idx_audit_queue_status_priority', AuditQueue.status, AuditQueue.priority)
