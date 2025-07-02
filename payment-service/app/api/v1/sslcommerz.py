from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.sslcommerz_service import SSLCommerzService
from app.schemas.sslcommerz import SSLCommerzInitiateRequest, SSLCommerzInitiateResponse
from app.utils.response import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/initiate", response_model=SuccessResponse[SSLCommerzInitiateResponse])
async def initiate_payment(
    request: SSLCommerzInitiateRequest,
    db: Session = Depends(get_db)
):
    try:
        sslcz_service = SSLCommerzService(db)
        result = await sslcz_service.initiate_payment(request)
        await sslcz_service.close()
        
        return SuccessResponse(
            message="Payment session initiated successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Payment initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/status/{transaction_id}")
async def get_payment_status(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    try:
        sslcz_service = SSLCommerzService(db)
        result = await sslcz_service.get_payment_status(transaction_id)
        await sslcz_service.close()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found"
            )
        
        return SuccessResponse(
            message="Payment status retrieved successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
