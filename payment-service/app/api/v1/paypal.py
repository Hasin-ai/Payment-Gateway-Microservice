from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.paypal_service import PayPalService
from app.schemas.paypal import PayPalPayoutRequest, PayPalPayoutResponse
from app.utils.response import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/payout", response_model=SuccessResponse[PayPalPayoutResponse])
async def initiate_payout(
    request: PayPalPayoutRequest,
    db: Session = Depends(get_db)
):
    try:
        paypal_service = PayPalService(db)
        result = await paypal_service.initiate_payout(request)
        await paypal_service.close()
        
        return SuccessResponse(
            message="Payout initiated successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Payout initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/status/{payout_id}")
async def get_payout_status(
    payout_id: str,
    db: Session = Depends(get_db)
):
    try:
        paypal_service = PayPalService(db)
        result = await paypal_service.get_payout_status(payout_id)
        await paypal_service.close()
        
        return SuccessResponse(
            message="Payout status retrieved successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to get payout status: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
