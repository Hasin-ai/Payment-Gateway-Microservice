from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.settings_service import SettingsService
from app.schemas.admin import (
    SystemSettingResponse, SystemSettingCreate, SystemSettingUpdate,
    AdminConfigResponse, AdminConfigUpdate, BulkSettingsUpdate
)
from app.utils.auth import require_admin, require_super_admin

router = APIRouter()

@router.get("/", response_model=List[SystemSettingResponse])
async def list_settings(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all system settings"""
    settings_service = SettingsService(db)
    settings = await settings_service.list_all_settings()
    return settings

@router.post("/", response_model=SystemSettingResponse)
async def create_setting(
    setting_data: SystemSettingCreate,
    current_user = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Create a new system setting"""
    settings_service = SettingsService(db)
    try:
        setting = await settings_service.create_setting(setting_data)
        return setting
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{setting_key}", response_model=SystemSettingResponse)
async def update_setting(
    setting_key: str,
    setting_update: SystemSettingUpdate,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a system setting"""
    settings_service = SettingsService(db)
    try:
        setting = await settings_service.update_setting(setting_key, setting_update, current_user.id)
        return setting
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))