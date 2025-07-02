from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    currency_code = Column(String(3), nullable=False, index=True)
    rate_to_bdt = Column(Numeric(10, 4), nullable=False)
    source = Column(String(50), nullable=True)  # API source name
    last_updated = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add unique constraint for currency_code and last_updated
    __table_args__ = (
        UniqueConstraint('currency_code', 'last_updated', name='_currency_time_uc'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate(currency_code='{self.currency_code}', rate_to_bdt={self.rate_to_bdt})>"
    
    def to_dict(self):
        """Convert exchange rate object to dictionary"""
        return {
            "id": self.id,
            "currency_code": self.currency_code,
            "rate_to_bdt": float(self.rate_to_bdt),
            "source": self.source,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self):
        """Check if the exchange rate has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

class RateUpdateLog(Base):
    __tablename__ = "rate_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    update_source = Column(String(50), nullable=False)
    currencies_updated = Column(Text, nullable=True)  # JSON string of updated currencies
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_details = Column(Text, nullable=True)
    update_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RateUpdateLog(update_source='{self.update_source}', success_count={self.success_count})>"
