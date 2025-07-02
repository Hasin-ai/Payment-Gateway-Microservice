from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import httpx
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import asyncio

from app.models.payment import PaymentRecord
from app.schemas.paypal import (
    PayPalPayoutRequest, PayPalPayoutResponse,
    PayPalPayoutStatus
)
from app.core.config import settings
from app.utils.exceptions import PaymentError, ValidationError

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self._access_token = None
        self._token_expires_at = None
    
    async def get_access_token(self) -> str:
        """Get PayPal access token"""
        if self._access_token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._access_token
        
        try:
            auth_string = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = 'grant_type=client_credentials'
            
            response = await self.http_client.post(
                f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token",
                headers=headers,
                content=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            
            return self._access_token
            
        except httpx.RequestError as e:
            logger.error(f"PayPal token request failed: {e}")
            raise PaymentError("PayPal authentication failed")
        except Exception as e:
            logger.error(f"PayPal authentication failed: {e}")
            raise PaymentError("Failed to authenticate with PayPal")
    
    async def initiate_payout(self, request: PayPalPayoutRequest) -> PayPalPayoutResponse:
        """Initiate PayPal payout"""
        try:
            access_token = await self.get_access_token()
            
            # Generate unique payout batch ID
            import uuid
            batch_id = f"PG-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            
            # Prepare payout data
            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": batch_id,
                    "email_subject": "You have a payment from Payment Gateway",
                    "email_message": request.note or f"Payment for transaction {request.transaction_id}"
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": str(request.amount),
                            "currency": request.currency
                        },
                        "receiver": request.recipient_email,
                        "note": request.note or f"Payment for transaction {request.transaction_id}",
                        "sender_item_id": f"TXN-{request.transaction_id}"
                    }
                ]
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = await self.http_client.post(
                f"{settings.PAYPAL_BASE_URL}/v1/payments/payouts",
                headers=headers,
                json=payout_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract payout item ID
            payout_item_id = None
            if result.get('items') and len(result['items']) > 0:
                payout_item_id = result['items'][0].get('payout_item_id')
            
            # Create payment record
            payment_record = PaymentRecord(
                transaction_id=request.transaction_id,
                internal_tran_id=f"PAYOUT-{request.transaction_id}",
                payment_type="paypal",
                payment_direction="outbound",
                status="PENDING",
                amount=request.amount,
                currency=request.currency,
                paypal_payout_batch_id=result.get('batch_header', {}).get('payout_batch_id'),
                paypal_payout_item_id=payout_item_id,
                paypal_recipient_email=request.recipient_email,
                paypal_raw_response=result
            )
            
            self.db.add(payment_record)
            self.db.commit()
            self.db.refresh(payment_record)
            
            return PayPalPayoutResponse(
                paypal_payout_id=payout_item_id or result.get('batch_header', {}).get('payout_batch_id'),
                transaction_id=request.transaction_id,
                recipient_email=request.recipient_email,
                amount=request.amount,
                currency=request.currency,
                status="PENDING",
                created_time=datetime.utcnow(),
                links=result.get('links', [])
            )
            
        except httpx.RequestError as e:
            logger.error(f"PayPal payout request failed: {e}")
            raise PaymentError("PayPal payout service unavailable")
        except Exception as e:
            logger.error(f"Payout initiation failed: {e}")
            raise PaymentError("Failed to initiate payout")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
