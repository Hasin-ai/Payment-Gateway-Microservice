from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime

from app.models.payment import WebhookLog, PaymentRecord
from app.services.sslcommerz_service import SSLCommerzService
from app.services.paypal_service import PayPalService

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.sslcz_service = SSLCommerzService(db)
        self.paypal_service = PayPalService(db)
    
    async def handle_sslcommerz_ipn(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SSLCommerz IPN webhook"""
        try:
            # Log webhook
            webhook_log = WebhookLog(
                webhook_source="sslcommerz",
                webhook_event="ipn",
                transaction_id=form_data.get('tran_id'),
                payload=form_data
            )
            self.db.add(webhook_log)
            self.db.commit()
            
            # Process the webhook
            val_id = form_data.get('val_id')
            if val_id:
                result = await self.sslcz_service.validate_payment(val_id)
                webhook_log.processed = True
                webhook_log.processing_status = "SUCCESS"
                webhook_log.processed_at = datetime.utcnow()
                self.db.commit()
                return result
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"SSLCommerz IPN processing failed: {e}")
            if 'webhook_log' in locals():
                webhook_log.processing_status = "FAILED"
                webhook_log.processing_error = str(e)
                self.db.commit()
            raise
    
    async def handle_paypal_webhook(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PayPal webhook"""
        try:
            # Log webhook
            webhook_log = WebhookLog(
                webhook_source="paypal",
                webhook_event=payload.get('event_type', 'unknown'),
                headers=headers,
                payload=payload
            )
            self.db.add(webhook_log)
            self.db.commit()
            
            # Process based on event type
            event_type = payload.get('event_type')
            if event_type in ['PAYMENT.PAYOUTS-ITEM.SUCCEEDED', 'PAYMENT.PAYOUTS-ITEM.FAILED']:
                # Handle payout events
                webhook_log.processed = True
                webhook_log.processing_status = "SUCCESS"
                webhook_log.processed_at = datetime.utcnow()
                self.db.commit()
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"PayPal webhook processing failed: {e}")
            if 'webhook_log' in locals():
                webhook_log.processing_status = "FAILED"
                webhook_log.processing_error = str(e)
                self.db.commit()
            raise
