from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionResponse, TransactionList, TransactionStats
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=SuccessResponse[TransactionList])
async def get_transaction_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status_filter: Optional[str] = Query(None),
    currency_filter: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history with advanced filtering"""
    try:
        transaction_service = TransactionService(db)
        
        # Set default date range if not provided (last 30 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        transactions, total = await transaction_service.get_transaction_history(
            user_id=current_user.id,
            page=page,
            size=size,
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter,
            currency_filter=currency_filter
        )
        
        has_next = (page * size) < total
        has_previous = page > 1
        
        return SuccessResponse(
            message="Transaction history retrieved successfully",
            data=TransactionList(
                transactions=[TransactionResponse.from_orm(t) for t in transactions],
                total=total,
                page=page,
                size=size,
                has_next=has_next,
                has_previous=has_previous
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history"
        )

@router.get("/recent", response_model=SuccessResponse[List[TransactionResponse]])
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's most recent transactions"""
    try:
        transaction_service = TransactionService(db)
        transactions = await transaction_service.get_recent_transactions(
            user_id=current_user.id,
            limit=limit
        )
        
        return SuccessResponse(
            message="Recent transactions retrieved successfully",
            data=[TransactionResponse.from_orm(t) for t in transactions]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent transactions"
        )

@router.get("/stats/period", response_model=SuccessResponse[TransactionStats])
async def get_period_stats(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction statistics for a specific period"""
    try:
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        # Limit to maximum 1 year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )
        
        transaction_service = TransactionService(db)
        stats = await transaction_service.get_transaction_stats_by_period(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return SuccessResponse(
            message="Period statistics retrieved successfully",
            data=stats
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve period statistics"
        )

@router.get("/export", response_model=SuccessResponse)
async def export_transaction_history(
    format: str = Query("csv", regex="^(csv|json|pdf)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export transaction history in specified format"""
    try:
        transaction_service = TransactionService(db)
        
        # Set default date range if not provided (last 90 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        export_data = await transaction_service.export_transaction_history(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return SuccessResponse(
            message="Transaction history export generated successfully",
            data=export_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export transaction history"
        )
