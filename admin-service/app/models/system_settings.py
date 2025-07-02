from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=False)
    setting_type = Column(String(20), default="string", nullable=False)  # string, number, boolean, json
    description = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemSettings(key={self.setting_key}, value={self.setting_value[:50] if self.setting_value else ''})>"
    
    def to_dict(self):
        """Convert system setting to dictionary"""
        return {
            "id": self.id,
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "setting_type": self.setting_type,
            "description": self.description,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_typed_value(self):
        """Get the setting value with proper type conversion"""
        if self.setting_type == "number":
            try:
                return float(self.setting_value)
            except ValueError:
                return 0
        elif self.setting_type == "boolean":
            return self.setting_value.lower() in ("true", "1", "yes")
        elif self.setting_type == "json":
            import json
            try:
                return json.loads(self.setting_value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.setting_value