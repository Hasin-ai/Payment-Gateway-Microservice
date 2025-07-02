from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, text
from sqlalchemy.sql import func

from app.core.database import Base

class AdminConfig(Base):
    __tablename__ = "admin_config"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_paypal_email = Column(String(255), nullable=False)
    admin_paypal_client_id = Column(String(255), nullable=False)
    admin_paypal_client_secret = Column(String(255), nullable=False)
    sslcz_store_id = Column(String(255), nullable=False)
    sslcz_store_passwd = Column(String(255), nullable=False)
    exchangerate_api_key = Column(String(255), nullable=True)
    service_fee_percentage = Column(DECIMAL(5, 2), default=2.00)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    def __repr__(self):
        return f"<AdminConfig(id={self.id}, email={self.admin_paypal_email})>"
    
    def to_dict(self):
        """Convert admin config to dictionary"""
        return {
            "id": self.id,
            "admin_paypal_email": self.admin_paypal_email,
            "service_fee_percentage": float(self.service_fee_percentage),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }