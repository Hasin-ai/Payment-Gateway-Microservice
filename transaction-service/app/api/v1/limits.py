from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.services.limit_service import LimitService
from app.schemas.limit import (
    PaymentLimitCheck, PaymentLimitResponse, PaymentLimitUpdate,
    PaymentLimitInfo, LimitUsageUpdate
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_user
from app.utils.exceptions import ValidationError, LimitExceededError

router = APIRouter()

@router.get("/check", response_model=SuccessResponse[PaymentLimitResponse])
async def check_payment_limits(
    currency: str = Query(..., description="Currency code (e.g., USD)"),
    amount: float = Query(..., description="Transaction amount"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if transaction amount is within payment limits"""
    try:
        limit_service = LimitService(db)
        
        limit_check = PaymentLimitCheck(
            currency_code=currency.upper(),
            amount=amount
        )
        
        limit_response = await limit_service.check_payment_limits(
            user_id=current_user.id,
            currency_code=limit_check.currency_code,
            amount=limit_check.amount
        )
        
        return SuccessResponse(
            message="Payment limits checked successfully",
            data=limit_response
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check payment limits"
        )

@router.get("/", response_model=SuccessResponse[List[PaymentLimitInfo]])
async def get_user_limits(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment limits for all currencies"""
    try:
        limit_service = LimitService(db)
        limits = await limit_service.get_user_limits(current_user.id)
        
        return SuccessResponse(
            message="Payment limits retrieved successfully",
            data=[PaymentLimitInfo.from_orm(limit) for limit in limits]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment limits"
        )

@router.get("/{currency_code}", response_model=SuccessResponse[PaymentLimitInfo])
async def get_currency_limit(
    currency_code: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment limit for specific currency"""
    try:
        limit_service = LimitService(db)
        limit = await limit_service.get_user_currency_limit(
            user_id=current_user.id,
            currency_code=currency_code.upper()
        )
        
        if not limit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment limit not found for currency: {currency_code}"
            )
        
        return SuccessResponse(
            message="Payment limit retrieved successfully",
            data=PaymentLimitInfo.from_orm(limit)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment limit"
        )

@router.put("/{currency_code}", response_model=SuccessResponse[PaymentLimitInfo])
async def update_payment_limit(
    currency_code: str,
    limit_update: PaymentLimitUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update payment limits for specific currency (admin only)"""
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        limit_service = LimitService(db)
        updated_limit = await limit_service.update_payment_limit(
            user_id=current_user.id,  # For admin, this could be target_user_id
            currency_code=currency_code.upper(),
            limit_update=limit_update
        )
        
        return SuccessResponse(
            message="Payment limit updated successfully",
            data=PaymentLimitInfo.from_orm(updated_limit)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payment limit"
        )

@router.post("/usage/update", response_model=SuccessResponse)
async def update_limit_usage(
    usage_update: LimitUsageUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update payment limit usage (internal service use)"""
    try:
        # This endpoint is typically called by other services
        if current_user.role not in ["admin", "system"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access required"
            )
        
        limit_service = LimitService(db)
        await limit_service.update_limit_usage(
            user_id=current_user.id,
            currency_code=usage_update.currency_code,
            amount=usage_update.amount,
            operation=usage_update.operation
        )
        
        return SuccessResponse(
            message="Limit usage updated successfully",
            data=None
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update limit usage"
        )

@router.post("/reset", response_model=SuccessResponse)
async def reset_expired_limits(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset expired payment limits (system task)"""
    try:
        # System or admin only
        if current_user.role not in ["admin", "system"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access required"
            )
        
        limit_service = LimitService(db)
        reset_count = await limit_service.reset_expired_limits()
        
        return SuccessResponse(
            message="Expired limits reset successfully",
            data={"reset_count": reset_count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset expired limits"
        )
