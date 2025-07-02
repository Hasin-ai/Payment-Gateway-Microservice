from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    phone_number = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # Verification
    email_verification_token = Column(String(255), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verification_token = Column(String(10), nullable=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self, include_sensitive: bool = False):
        """Convert user to dictionary"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "phone_number": self.phone_number,
            "full_name": self.full_name,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data.update({
                "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
                "phone_verified_at": self.phone_verified_at.isoformat() if self.phone_verified_at else None,
                "failed_login_attempts": self.failed_login_attempts,
                "locked_until": self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data
    
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active and not self.is_locked()
