from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.preference_service import PreferenceService
from app.schemas.preferences import (
    NotificationPreferencesUpdate, NotificationPreferencesResponse,
    ContactInfoUpdate
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_service

router = APIRouter()

@router.get("/{user_id}", response_model=SuccessResponse[NotificationPreferencesResponse])
async def get_user_preferences(
    user_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences"""
    try:
        preference_service = PreferenceService(db)
        preferences = await preference_service.get_user_preferences(user_id)
        
        return SuccessResponse(
            message="Notification preferences retrieved successfully",
            data=NotificationPreferencesResponse.from_orm(preferences)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification preferences"
        )

@router.put("/{user_id}", response_model=SuccessResponse[NotificationPreferencesResponse])
async def update_user_preferences(
    user_id: int,
    preferences_update: NotificationPreferencesUpdate,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""
    try:
        preference_service = PreferenceService(db)
        updated_preferences = await preference_service.update_user_preferences(
            user_id, preferences_update
        )
        
        return SuccessResponse(
            message="Notification preferences updated successfully",
            data=NotificationPreferencesResponse.from_orm(updated_preferences)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )

@router.post("/{user_id}/contact", response_model=SuccessResponse[NotificationPreferencesResponse])
async def update_contact_info(
    user_id: int,
    contact_update: ContactInfoUpdate,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Update user's contact information for notifications"""
    try:
        preference_service = PreferenceService(db)
        updated_preferences = await preference_service.update_contact_info(
            user_id, contact_update
        )
        
        return SuccessResponse(
            message="Contact information updated successfully",
            data=NotificationPreferencesResponse.from_orm(updated_preferences)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update contact information"
        )

@router.post("/{user_id}/verify-email", response_model=SuccessResponse)
async def send_email_verification(
    user_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Send email verification notification"""
    try:
        preference_service = PreferenceService(db)
        result = await preference_service.send_email_verification(user_id)
        
        return SuccessResponse(
            message="Email verification sent successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email verification"
        )

@router.post("/{user_id}/verify-phone", response_model=SuccessResponse)
async def send_phone_verification(
    user_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Send phone number verification SMS"""
    try:
        preference_service = PreferenceService(db)
        result = await preference_service.send_phone_verification(user_id)
        
        return SuccessResponse(
            message="Phone verification SMS sent successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send phone verification"
        )

@router.get("/{user_id}/channels", response_model=SuccessResponse)
async def get_available_channels(
    user_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get available notification channels for user"""
    try:
        preference_service = PreferenceService(db)
        channels = await preference_service.get_available_channels(user_id)
        
        return SuccessResponse(
            message="Available channels retrieved successfully",
            data=channels
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available channels"
        )
