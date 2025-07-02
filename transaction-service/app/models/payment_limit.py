from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.core.database import Base

class PaymentLimit(Base):
    __tablename__ = "payment_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    currency_code = Column(String(3), nullable=False)
    
    # Limit amounts
    daily_limit = Column(DECIMAL(15, 2), nullable=False)
    monthly_limit = Column(DECIMAL(15, 2), nullable=False)
    yearly_limit = Column(DECIMAL(15, 2), nullable=False)
    
    # Current usage tracking
    current_daily_used = Column(DECIMAL(15, 2), default=0)
    current_monthly_used = Column(DECIMAL(15, 2), default=0)
    current_yearly_used = Column(DECIMAL(15, 2), default=0)
    
    # Reset timestamps
    daily_reset_at = Column(DateTime(timezone=True), nullable=False)
    monthly_reset_at = Column(DateTime(timezone=True), nullable=False)
    yearly_reset_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PaymentLimit(user_id={self.user_id}, currency='{self.currency_code}')>"
    
    def to_dict(self):
        """Convert payment limit object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "currency_code": self.currency_code,
            "daily_limit": float(self.daily_limit),
            "monthly_limit": float(self.monthly_limit),
            "yearly_limit": float(self.yearly_limit),
            "current_daily_used": float(self.current_daily_used),
            "current_monthly_used": float(self.current_monthly_used),
            "current_yearly_used": float(self.current_yearly_used),
            "daily_reset_at": self.daily_reset_at.isoformat() if self.daily_reset_at else None,
            "monthly_reset_at": self.monthly_reset_at.isoformat() if self.monthly_reset_at else None,
            "yearly_reset_at": self.yearly_reset_at.isoformat() if self.yearly_reset_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_reset_needed(self):
        """Check if limits need to be reset"""
        now = datetime.utcnow()
        return {
            "daily": now >= self.daily_reset_at.replace(tzinfo=None),
            "monthly": now >= self.monthly_reset_at.replace(tzinfo=None),
            "yearly": now >= self.yearly_reset_at.replace(tzinfo=None)
        }
    
    def get_remaining_limits(self):
        """Calculate remaining limits"""
        return {
            "daily_remaining": float(self.daily_limit - self.current_daily_used),
            "monthly_remaining": float(self.monthly_limit - self.current_monthly_used),
            "yearly_remaining": float(self.yearly_limit - self.current_yearly_used)
        }
