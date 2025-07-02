from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy.sql import func

from app.models.system_settings import SystemSettings
from app.models.admin_config import AdminConfig
from app.schemas.admin import (
    SystemSettingCreate, 
    SystemSettingUpdate, 
    SystemSettingResponse,
    AdminConfigUpdate,
    AdminConfigResponse,
    BulkSettingsUpdate
)

class SettingsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def list_all_settings(self) -> List[SystemSettingResponse]:
        """Get all system settings"""
        settings = self.db.query(SystemSettings).order_by(SystemSettings.setting_key).all()
        return [SystemSettingResponse.from_orm(setting) for setting in settings]
    
    async def get_setting_by_key(self, setting_key: str) -> Optional[SystemSettingResponse]:
        """Get a specific setting by key"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_key
        ).first()
        
        if setting:
            return SystemSettingResponse.from_orm(setting)
        return None
    
    async def create_setting(self, setting_data: SystemSettingCreate) -> SystemSettingResponse:
        """Create a new system setting"""
        # Check if setting already exists
        existing = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_data.setting_key
        ).first()
        
        if existing:
            raise ValueError(f"Setting with key '{setting_data.setting_key}' already exists")
        
        # Validate setting value based on type
        self._validate_setting_value(setting_data.setting_value, setting_data.setting_type)
        
        # Create new setting
        new_setting = SystemSettings(
            setting_key=setting_data.setting_key,
            setting_value=setting_data.setting_value,
            setting_type=setting_data.setting_type,
            description=setting_data.description,
            is_encrypted=setting_data.is_encrypted
        )
        
        self.db.add(new_setting)
        self.db.commit()
        self.db.refresh(new_setting)
        
        return SystemSettingResponse.from_orm(new_setting)
    
    async def update_setting(self, setting_key: str, setting_update: SystemSettingUpdate, user_id: int) -> SystemSettingResponse:
        """Update an existing system setting"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_key
        ).first()
        
        if not setting:
            raise ValueError(f"Setting with key '{setting_key}' not found")
        
        # Validate the new value based on the setting type
        self._validate_setting_value(setting_update.setting_value, setting.setting_type)
        
        # Update the setting
        setting.setting_value = setting_update.setting_value
        if setting_update.description is not None:
            setting.description = setting_update.description
        setting.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(setting)
        
        return SystemSettingResponse.from_orm(setting)
    
    async def delete_setting(self, setting_key: str) -> bool:
        """Delete a system setting"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_key
        ).first()
        
        if not setting:
            raise ValueError(f"Setting with key '{setting_key}' not found")
        
        self.db.delete(setting)
        self.db.commit()
        
        return True
    
    async def bulk_update_settings(self, bulk_update: BulkSettingsUpdate) -> Dict[str, Any]:
        """Update multiple settings at once"""
        updated_settings = []
        failed_updates = []
        
        for setting_key, setting_value in bulk_update.settings.items():
            try:
                setting = self.db.query(SystemSettings).filter(
                    SystemSettings.setting_key == setting_key
                ).first()
                
                if setting:
                    # Validate the new value
                    self._validate_setting_value(setting_value, setting.setting_type)
                    
                    setting.setting_value = setting_value
                    setting.updated_at = datetime.utcnow()
                    updated_settings.append(setting_key)
                else:
                    failed_updates.append({
                        "key": setting_key,
                        "error": "Setting not found"
                    })
            except Exception as e:
                failed_updates.append({
                    "key": setting_key,
                    "error": str(e)
                })
        
        if updated_settings:
            self.db.commit()
        
        return {
            "updated_count": len(updated_settings),
            "updated_settings": updated_settings,
            "failed_count": len(failed_updates),
            "failed_updates": failed_updates
        }
    
    async def get_admin_config(self) -> Optional[AdminConfigResponse]:
        """Get the current admin configuration"""
        config = self.db.query(AdminConfig).filter(
            AdminConfig.is_active == True
        ).first()
        
        if config:
            return AdminConfigResponse.from_orm(config)
        return None
    
    async def update_admin_config(self, config_update: AdminConfigUpdate) -> AdminConfigResponse:
        """Update admin configuration"""
        config = self.db.query(AdminConfig).filter(
            AdminConfig.is_active == True
        ).first()
        
        if not config:
            # Create new config if none exists
            config = AdminConfig(
                admin_paypal_email=config_update.admin_paypal_email,
                service_fee_percentage=config_update.service_fee_percentage,
                is_active=True
            )
            self.db.add(config)
        else:
            # Update existing config
            if config_update.admin_paypal_email is not None:
                config.admin_paypal_email = config_update.admin_paypal_email
            if config_update.service_fee_percentage is not None:
                config.service_fee_percentage = config_update.service_fee_percentage
            config.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(config)
        
        return AdminConfigResponse.from_orm(config)
    
    def _validate_setting_value(self, value: str, setting_type: str) -> None:
        """Validate setting value based on its type"""
        if setting_type == "number":
            try:
                float(value)
            except ValueError:
                raise ValueError(f"Invalid number value: {value}")
        
        elif setting_type == "boolean":
            if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                raise ValueError(f"Invalid boolean value: {value}")
        
        elif setting_type == "json":
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON value: {value}")
        
        # string type doesn't need validation
    
    async def get_settings_by_prefix(self, prefix: str) -> List[SystemSettingResponse]:
        """Get all settings with a specific key prefix"""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key.like(f"{prefix}%")
        ).order_by(SystemSettings.setting_key).all()
        
        return [SystemSettingResponse.from_orm(setting) for setting in settings]
    
    async def get_settings_by_type(self, setting_type: str) -> List[SystemSettingResponse]:
        """Get all settings of a specific type"""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.setting_type == setting_type
        ).order_by(SystemSettings.setting_key).all()
        
        return [SystemSettingResponse.from_orm(setting) for setting in settings]
    
    async def search_settings(self, search_term: str) -> List[SystemSettingResponse]:
        """Search settings by key or description"""
        # Fixed: Using func.lower() for case-insensitive search instead of ilike
        settings = self.db.query(SystemSettings).filter(
            or_(
                func.lower(SystemSettings.setting_key).contains(search_term.lower()),
                func.lower(SystemSettings.description).contains(search_term.lower())
            )
        ).order_by(SystemSettings.setting_key).all()
        
        return [SystemSettingResponse.from_orm(setting) for setting in settings]
