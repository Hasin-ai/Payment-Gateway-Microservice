from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    internal_tran_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Request details
    requested_foreign_currency = Column(String(3), nullable=False)
    requested_foreign_amount = Column(DECIMAL(15, 2), nullable=False)
    recipient_paypal_email = Column(String(255), nullable=False)
    payment_purpose = Column(Text, nullable=True)
    
    # Exchange rate and BDT calculations
    exchange_rate_bdt = Column(DECIMAL(10, 4), nullable=False)
    calculated_bdt_amount = Column(DECIMAL(15, 2), nullable=False)
    service_fee_bdt = Column(DECIMAL(15, 2), nullable=False)
    total_bdt_amount = Column(DECIMAL(15, 2), nullable=False)
    
    # SSLCommerz payment details
    sslcz_tran_id = Column(String(100), nullable=True)
    sslcz_val_id = Column(String(100), nullable=True)
    sslcz_received_bdt_amount = Column(DECIMAL(15, 2), nullable=True)
    sslcz_store_amount_bdt = Column(DECIMAL(15, 2), nullable=True)
    sslcz_card_type = Column(String(50), nullable=True)
    sslcz_bank_tran_id = Column(String(100), nullable=True)
    sslcz_payment_method = Column(String(50), nullable=True)
    sslcz_ipn_payload = Column(JSONB, nullable=True)
    sslcz_validation_payload = Column(JSONB, nullable=True)
    
    # PayPal payout details
    paypal_payout_tran_id = Column(String(100), nullable=True)
    paypal_payout_status = Column(String(50), nullable=True)
    paypal_payout_payload = Column(JSONB, nullable=True)
    
    # Transaction status and tracking
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    bdt_received_at = Column(DateTime(timezone=True), nullable=True)
    payout_initiated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, internal_tran_id='{self.internal_tran_id}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert transaction object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "internal_tran_id": self.internal_tran_id,
            "requested_foreign_currency": self.requested_foreign_currency,
            "requested_foreign_amount": float(self.requested_foreign_amount),
            "recipient_paypal_email": self.recipient_paypal_email,
            "payment_purpose": self.payment_purpose,
            "exchange_rate_bdt": float(self.exchange_rate_bdt),
            "calculated_bdt_amount": float(self.calculated_bdt_amount),
            "service_fee_bdt": float(self.service_fee_bdt),
            "total_bdt_amount": float(self.total_bdt_amount),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "bdt_received_at": self.bdt_received_at.isoformat() if self.bdt_received_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class TransactionStatusHistory(Base):
    __tablename__ = "transaction_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, nullable=True)
    change_reason = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TransactionStatusHistory(transaction_id={self.transaction_id}, new_status='{self.new_status}')>"
