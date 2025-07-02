from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.services.transaction_service import TransactionService
from app.services.calculation_service import CalculationService
from app.schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionUpdate,
    TransactionStatusUpdate, TransactionCalculation, TransactionList,
    TransactionStats
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_user
from app.utils.exceptions import ValidationError, LimitExceededError

router = APIRouter()

@router.post("/calculate", response_model=SuccessResponse[TransactionCalculation])
async def calculate_transaction(
    currency: str = Query(..., description="Foreign currency code"),
    amount: float = Query(..., description="Amount in foreign currency"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate transaction amounts including exchange rate and fees"""
    try:
        calculation_service = CalculationService(db)
        
        calculation = await calculation_service.calculate_transaction_amounts(
            from_currency=currency.upper(),
            amount=amount
        )
        
        return SuccessResponse(
            message="Transaction calculation completed successfully",
            data=calculation
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate transaction amounts"
        )

@router.post("/", response_model=SuccessResponse[TransactionResponse])
async def create_transaction(
    transaction_data: TransactionCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    try:
        transaction_service = TransactionService(db)
        calculation_service = CalculationService(db)
        
        # Calculate transaction amounts
        calculation = await calculation_service.calculate_transaction_amounts(
            from_currency=transaction_data.requested_foreign_currency,
            amount=transaction_data.requested_foreign_amount
        )
        
        # Create transaction
        transaction = await transaction_service.create_transaction(
            user_id=current_user.id,
            transaction_data=transaction_data,
            calculation=calculation
        )
        
        # Add background task to initiate payment
        background_tasks.add_task(
            transaction_service.initiate_payment_process,
            transaction.id
        )
        
        return SuccessResponse(
            message="Transaction created successfully",
            data=TransactionResponse.from_orm(transaction)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction"
        )

@router.get("/{transaction_id}", response_model=SuccessResponse[TransactionResponse])
async def get_transaction(
    transaction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction by ID"""
    try:
        transaction_service = TransactionService(db)
        transaction = await transaction_service.get_transaction_by_id(
            transaction_id, current_user.id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return SuccessResponse(
            message="Transaction retrieved successfully",
            data=TransactionResponse.from_orm(transaction)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction"
        )

@router.get("/", response_model=SuccessResponse[TransactionList])
async def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    currency_filter: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's transactions with pagination and filtering"""
    try:
        transaction_service = TransactionService(db)
        
        transactions, total = await transaction_service.list_user_transactions(
            user_id=current_user.id,
            page=page,
            size=size,
            status_filter=status_filter,
            currency_filter=currency_filter
        )
        
        has_next = (page * size) < total
        has_previous = page > 1
        
        return SuccessResponse(
            message="Transactions retrieved successfully",
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
            detail="Failed to retrieve transactions"
        )

@router.put("/{transaction_id}/status", response_model=SuccessResponse[TransactionResponse])
async def update_transaction_status(
    transaction_id: int,
    status_update: TransactionStatusUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update transaction status (admin only or system)"""
    try:
        transaction_service = TransactionService(db)
        
        # Check permissions (admin or system)
        if current_user.role not in ["admin", "system"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        updated_transaction = await transaction_service.update_transaction_status(
            transaction_id=transaction_id,
            new_status=status_update.new_status,
            changed_by=current_user.id,
            change_reason=status_update.change_reason,
            metadata=status_update.metadata
        )
        
        return SuccessResponse(
            message="Transaction status updated successfully",
            data=TransactionResponse.from_orm(updated_transaction)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction status"
        )

@router.get("/internal/{internal_tran_id}", response_model=SuccessResponse[TransactionResponse])
async def get_transaction_by_internal_id(
    internal_tran_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction by internal transaction ID"""
    try:
        transaction_service = TransactionService(db)
        transaction = await transaction_service.get_transaction_by_internal_id(
            internal_tran_id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if user owns this transaction or is admin
        if transaction.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return SuccessResponse(
            message="Transaction retrieved successfully",
            data=TransactionResponse.from_orm(transaction)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction"
        )

@router.get("/stats/summary", response_model=SuccessResponse[TransactionStats])
async def get_transaction_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction statistics"""
    try:
        transaction_service = TransactionService(db)
        stats = await transaction_service.get_user_transaction_stats(current_user.id)
        
        return SuccessResponse(
            message="Transaction statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction statistics"
        )

@router.post("/{transaction_id}/cancel", response_model=SuccessResponse[TransactionResponse])
async def cancel_transaction(
    transaction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending transaction"""
    try:
        transaction_service = TransactionService(db)
        
        cancelled_transaction = await transaction_service.cancel_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            cancelled_by=current_user.id
        )
        
        return SuccessResponse(
            message="Transaction cancelled successfully",
            data=TransactionResponse.from_orm(cancelled_transaction)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel transaction"
        )
