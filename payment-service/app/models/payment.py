from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.core.database import Base

class PaymentRecord(Base):
    __tablename__ = "payment_records"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False, index=True)
    internal_tran_id = Column(String(50), nullable=False, index=True)
    payment_type = Column(String(20), nullable=False)
    payment_direction = Column(String(10), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    sslcz_session_key = Column(String(100), nullable=True)
    sslcz_gateway_url = Column(Text, nullable=True)
    sslcz_tran_id = Column(String(100), nullable=True)
    sslcz_val_id = Column(String(100), nullable=True)
    sslcz_store_amount = Column(DECIMAL(15, 2), nullable=True)
    sslcz_bank_tran_id = Column(String(100), nullable=True)
    sslcz_card_type = Column(String(50), nullable=True)
    sslcz_payment_method = Column(String(50), nullable=True)
    sslcz_risk_level = Column(Integer, nullable=True)
    sslcz_raw_response = Column(JSONB, nullable=True)
    paypal_payout_batch_id = Column(String(100), nullable=True)
    paypal_payout_item_id = Column(String(100), nullable=True)
    paypal_transaction_id = Column(String(100), nullable=True)
    paypal_recipient_email = Column(String(255), nullable=True)
    paypal_fees = Column(DECIMAL(10, 2), nullable=True)
    paypal_raw_response = Column(JSONB, nullable=True)
    webhook_received = Column(Boolean, default=False)
    webhook_validated = Column(Boolean, default=False)
    webhook_payload = Column(JSONB, nullable=True)
    validation_response = Column(JSONB, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    webhook_received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PaymentRecord(id={self.id}, transaction_id={self.transaction_id}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "internal_tran_id": self.internal_tran_id,
            "payment_type": self.payment_type,
            "payment_direction": self.payment_direction,
            "status": self.status,
            "amount": float(self.amount),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_source = Column(String(20), nullable=False)
    webhook_event = Column(String(50), nullable=False)
    transaction_id = Column(String(50), nullable=True, index=True)
    headers = Column(JSONB, nullable=True)
    payload = Column(JSONB, nullable=False)
    signature = Column(String(255), nullable=True)
    processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="PENDING")
    processing_error = Column(Text, nullable=True)
    processing_attempts = Column(Integer, default=0)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, source={self.webhook_source}, event={self.webhook_event})>"
