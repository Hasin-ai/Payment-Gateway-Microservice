from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.schemas.user import UserProfile, UserList, UserStats
from app.utils.response import SuccessResponse

router = APIRouter()

@router.get("/me", response_model=SuccessResponse[UserProfile])
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user = Depends(lambda db=Depends(get_db): AuthService(db).get_current_user)
):
    """Get current user's profile"""
    try:
        user_service = UserService(db)
        profile = await user_service.get_user_profile(current_user.id)
        
        return SuccessResponse(
            message="Profile retrieved successfully",
            data=UserProfile.from_orm(profile)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.get("/", response_model=SuccessResponse[UserList])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(lambda db=Depends(get_db): AuthService(db).get_current_admin_user)
):
    """List users with filtering and pagination (Admin only)"""
    try:
        user_service = UserService(db)
        users, total = await user_service.list_users(
            page=page,
            size=size,
            search=search,
            role=role,
            is_verified=is_verified
        )
        
        return SuccessResponse(
            message="Users retrieved successfully",
            data=UserList(
                users=[UserProfile.from_orm(user) for user in users],
                total=total,
                page=page,
                size=size
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )
        
