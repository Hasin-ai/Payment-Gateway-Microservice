from sqlalchemy.orm import Session
from typing import Optional

from app.models.admin_config import AdminConfig
from app.models.system_settings import SystemSettings

class AdminService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_admin_config(self) -> Optional[AdminConfig]:
        """Get the current admin configuration"""
        return self.db.query(AdminConfig).filter(
            AdminConfig.is_active == True
        ).first()
    
    async def update_admin_config(self, config_data: dict) -> AdminConfig:
        """Update admin configuration"""
        config = await self.get_admin_config()
        
        if not config:
            # Create new config if none exists
            config = AdminConfig(**config_data)
            self.db.add(config)
        else:
            # Update existing config
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    async def get_system_setting(self, key: str) -> Optional[SystemSettings]:
        """Get a system setting by key"""
        return self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == key
        ).first()
    
    async def update_system_setting(self, key: str, value: str) -> SystemSettings:
        """Update or create a system setting"""
        setting = await self.get_system_setting(key)
        
        if not setting:
            setting = SystemSettings(setting_key=key, setting_value=value)
            self.db.add(setting)
        else:
            setting.setting_value = value
        
        self.db.commit()
        self.db.refresh(setting)
        
        return setting
    
    async def get_all_settings(self) -> list[SystemSettings]:
        """Get all system settings"""
        return self.db.query(SystemSettings).all()