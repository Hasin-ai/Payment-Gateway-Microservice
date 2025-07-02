from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.schemas.user import UserProfile, UserUpdate
from app.utils.response import SuccessResponse

router = APIRouter()

@router.get("/", response_model=SuccessResponse[UserProfile])
async def get_profile(
    db: Session = Depends(get_db),
    current_user = Depends(lambda db=Depends(get_db): AuthService(db).get_current_user)
):
    """Get user profile"""
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

@router.put("/", response_model=SuccessResponse[UserProfile])
async def update_profile(
    profile_data: UserUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(lambda db=Depends(get_db): AuthService(db).get_current_user)
):
    """Update user profile"""
    try:
        user_service = UserService(db)
        
        updated_user = await user_service.update_user_profile(
            current_user.id, 
            profile_data
        )
        
        # Log profile update in background
        background_tasks.add_task(
            user_service.log_profile_update,
            current_user.id,
            profile_data.dict(exclude_unset=True)
        )
        
        return SuccessResponse(
            message="Profile updated successfully",
            data=UserProfile.from_orm(updated_user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
        
