from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.models.session import UserSession
from app.schemas.user import UserUpdate, UserStats
from app.core.security import SecurityUtils

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_verified: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination"""
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.order_by(desc(User.created_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return users, total
    
    async def update_user_profile(self, user_id: int, profile_data: UserUpdate) -> User:
        """Update user profile"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Update fields
        update_data = profile_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User profile updated: {user.username}")
        return user
    
    async def log_profile_update(self, user_id: int, updated_fields: Dict[str, Any]):
        """Log profile update for audit"""
        logger.info(f"Profile updated for user {user_id}: {updated_fields}")
