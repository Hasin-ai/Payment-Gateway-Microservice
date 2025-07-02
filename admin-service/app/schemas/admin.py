from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

class AdminConfigUpdate(BaseModel):
    admin_paypal_email: Optional[EmailStr] = None
    service_fee_percentage: Optional[Decimal] = None
    
    @validator("service_fee_percentage")
    def validate_service_fee(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Service fee percentage must be between 0 and 100")
        return v

class AdminConfigResponse(BaseModel):
    id: int
    admin_paypal_email: str
    service_fee_percentage: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SystemSettingUpdate(BaseModel):
    setting_value: str
    description: Optional[str] = None

class SystemSettingCreate(BaseModel):
    setting_key: str
    setting_value: str
    setting_type: str = "string"
    description: Optional[str] = None
    is_encrypted: bool = False
    
    @validator("setting_type")
    def validate_setting_type(cls, v):
        allowed_types = ["string", "number", "boolean", "json"]
        if v not in allowed_types:
            raise ValueError(f"Setting type must be one of: {allowed_types}")
        return v

class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: str
    setting_type: str
    description: Optional[str]
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BulkSettingsUpdate(BaseModel):
    settings: Dict[str, str]

class UserManagementAction(BaseModel):
    action: str  # activate, deactivate, verify, unverify, change_role
    reason: Optional[str] = None
    
    @validator("action")
    def validate_action(cls, v):
        allowed_actions = ["activate", "deactivate", "verify", "unverify", "change_role"]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {allowed_actions}")
        return v

class UserRoleUpdate(BaseModel):
    new_role: str
    reason: Optional[str] = None
    
    @validator("new_role")
    def validate_role(cls, v):
        allowed_roles = ["admin", "user", "support"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v