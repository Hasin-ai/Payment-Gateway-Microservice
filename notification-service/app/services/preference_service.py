from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.models.notification import NotificationPreferences
from app.schemas.preferences import (
    NotificationPreferencesUpdate, ContactInfoUpdate
)
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class PreferenceService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """Get user's notification preferences"""
        preferences = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = NotificationPreferences(
                user_id=user_id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                transaction_alerts=True,
                payout_alerts=True,
                security_alerts=True,
                rate_change_alerts=False,
                limit_alerts=True,
                marketing_emails=False
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
        
        return preferences
    
    async def update_user_preferences(
        self, 
        user_id: int, 
        preferences_update: NotificationPreferencesUpdate
    ) -> NotificationPreferences:
        """Update user's notification preferences"""
        preferences = await self.get_user_preferences(user_id)
        
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        self.db.commit()
        self.db.refresh(preferences)
        
        logger.info(f"Updated preferences for user {user_id}")
        return preferences
    
    async def update_contact_info(
        self, 
        user_id: int, 
        contact_update: ContactInfoUpdate
    ) -> NotificationPreferences:
        """Update user's contact information"""
        preferences = await self.get_user_preferences(user_id)
        
        update_data = contact_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        self.db.commit()
        self.db.refresh(preferences)
        
        logger.info(f"Updated contact info for user {user_id}")
        return preferences
    
    async def send_email_verification(self, user_id: int) -> Dict[str, Any]:
        """Send email verification notification"""
        # Implementation would send verification email
        return {
            "user_id": user_id,
            "verification_sent": True,
            "method": "email"
        }
    
    async def send_phone_verification(self, user_id: int) -> Dict[str, Any]:
        """Send phone verification SMS"""
        # Implementation would send verification SMS
        return {
            "user_id": user_id,
            "verification_sent": True,
            "method": "sms"
        }
    
    async def get_available_channels(self, user_id: int) -> Dict[str, Any]:
        """Get available notification channels for user"""
        preferences = await self.get_user_preferences(user_id)
        
        channels = {
            "email": {
                "enabled": preferences.email_enabled,
                "configured": bool(preferences.email_address),
                "address": preferences.email_address
            },
            "sms": {
                "enabled": preferences.sms_enabled,
                "configured": bool(preferences.phone_number),
                "number": preferences.phone_number
            },
            "push": {
                "enabled": preferences.push_enabled,
                "configured": bool(preferences.push_token)
            }
        }
        
        return channels
