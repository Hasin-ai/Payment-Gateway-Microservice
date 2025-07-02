from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.webhook_service import WebhookService
from app.utils.response import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sslcommerz/ipn")
async def sslcommerz_ipn(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        form_data = await request.form()
        webhook_service = WebhookService(db)
        
        result = await webhook_service.handle_sslcommerz_ipn(dict(form_data))
        
        return SuccessResponse(
            message="IPN processed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"SSLCommerz IPN processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        headers = dict(request.headers)
        payload = await request.json()
        
        webhook_service = WebhookService(db)
        result = await webhook_service.handle_paypal_webhook(headers, payload)
        
        return SuccessResponse(
            message="Webhook processed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"PayPal webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
