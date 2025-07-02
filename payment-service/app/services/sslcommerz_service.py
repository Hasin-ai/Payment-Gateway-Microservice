from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio

from app.models.payment import PaymentRecord
from app.schemas.sslcommerz import (
    SSLCommerzInitiateRequest, SSLCommerzInitiateResponse,
    SSLCommerzPaymentStatus
)
from app.core.config import settings
from app.utils.exceptions import PaymentError, ValidationError

logger = logging.getLogger(__name__)

class SSLCommerzService:
    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def initiate_payment(self, request: SSLCommerzInitiateRequest) -> SSLCommerzInitiateResponse:
        """Initiate SSLCommerz payment session"""
        try:
            # Prepare SSLCommerz session data
            session_data = {
                'store_id': settings.SSLCOMMERZ_STORE_ID,
                'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
                'total_amount': str(request.total_amount),
                'currency': request.currency,
                'tran_id': request.internal_tran_id,
                'success_url': f"{settings.SSLCOMMERZ_IPN_URL.replace('/ipn', '/success')}",
                'fail_url': f"{settings.SSLCOMMERZ_IPN_URL.replace('/ipn', '/fail')}",
                'cancel_url': f"{settings.SSLCOMMERZ_IPN_URL.replace('/ipn', '/cancel')}",
                'ipn_url': settings.SSLCOMMERZ_IPN_URL,
                'multi_card_name': 'mastercard,visacard,amexcard,internetbank,mobilebank',
                'value_a': str(request.transaction_id),
                'value_b': 'payment-gateway',
                'value_c': 'international-transfer',
                'value_d': request.internal_tran_id,
                'cus_name': request.customer_name,
                'cus_email': request.customer_email,
                'cus_add1': request.customer_address,
                'cus_phone': request.customer_phone,
                'cus_city': 'Dhaka',
                'cus_state': 'Dhaka',
                'cus_postcode': '1000',
                'cus_country': 'Bangladesh',
                'product_name': request.product_name,
                'product_category': request.product_category,
                'product_profile': 'general',
                'shipping_method': 'NO',
                'num_of_item': 1
            }
            
            # Make API call to SSLCommerz
            response = await self.http_client.post(
                settings.SSLCOMMERZ_SESSION_URL,
                data=session_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') != 'SUCCESS':
                raise PaymentError(f"SSLCommerz session creation failed: {result.get('failedreason')}")
            
            # Create payment record
            payment_record = PaymentRecord(
                transaction_id=request.transaction_id,
                internal_tran_id=request.internal_tran_id,
                payment_type="sslcommerz",
                payment_direction="inbound",
                status="INITIATED",
                amount=request.total_amount,
                currency=request.currency,
                sslcz_session_key=result.get('sessionkey'),
                sslcz_gateway_url=result.get('GatewayPageURL'),
                sslcz_raw_response=result
            )
            
            self.db.add(payment_record)
            self.db.commit()
            self.db.refresh(payment_record)
            
            # Calculate session expiry
            valid_till = datetime.utcnow() + timedelta(minutes=settings.PAYMENT_TIMEOUT_MINUTES)
            
            return SSLCommerzInitiateResponse(
                sessionkey=result['sessionkey'],
                gateway_url=result['GatewayPageURL'],
                redirect_url=result['redirectGatewayURL'],
                valid_till=valid_till
            )
            
        except httpx.RequestError as e:
            logger.error(f"SSLCommerz API request failed: {e}")
            raise PaymentError("Payment gateway unavailable")
        except Exception as e:
            logger.error(f"Payment initiation failed: {e}")
            raise PaymentError("Failed to initiate payment")
    
    async def validate_payment(self, val_id: str) -> Dict[str, Any]:
        """Validate SSLCommerz payment using validation API"""
        try:
            validation_url = settings.SSLCOMMERZ_VALIDATION_URL
            params = {
                'val_id': val_id,
                'store_id': settings.SSLCOMMERZ_STORE_ID,
                'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
                'format': 'json'
            }
            
            response = await self.http_client.get(validation_url, params=params)
            response.raise_for_status()
            
            validation_data = response.json()
            
            # Update payment record with validation data
            payment_record = self.db.query(PaymentRecord).filter(
                PaymentRecord.sslcz_val_id == val_id
            ).first()
            
            if payment_record:
                payment_record.validation_response = validation_data
                payment_record.webhook_validated = True
                
                if validation_data.get('status') == 'VALID':
                    payment_record.status = "VALIDATED"
                    payment_record.completed_at = datetime.utcnow()
                elif validation_data.get('status') == 'VALIDATED':
                    payment_record.status = "ALREADY_VALIDATED"
                else:
                    payment_record.status = "VALIDATION_FAILED"
                    payment_record.error_message = f"Validation failed: {validation_data.get('status')}"
                
                self.db.commit()
                self.db.refresh(payment_record)
            
            return {
                "validation_status": validation_data.get('status'),
                "transaction_id": validation_data.get('tran_id'),
                "amount": validation_data.get('amount'),
                "store_amount": validation_data.get('store_amount'),
                "validated_on": validation_data.get('validated_on'),
                "risk_level": validation_data.get('risk_level')
            }
            
        except httpx.RequestError as e:
            logger.error(f"SSLCommerz validation API failed: {e}")
            raise PaymentError("Payment validation service unavailable")
        except Exception as e:
            logger.error(f"Payment validation failed: {e}")
            raise PaymentError("Failed to validate payment")
    
    async def get_payment_status(self, transaction_id: int) -> Optional[SSLCommerzPaymentStatus]:
        """Get payment status for a transaction"""
        payment_record = self.db.query(PaymentRecord).filter(
            and_(
                PaymentRecord.transaction_id == transaction_id,
                PaymentRecord.payment_type == "sslcommerz"
            )
        ).order_by(desc(PaymentRecord.created_at)).first()
        
        if not payment_record:
            return None
        
        # Check if amounts match (validation)
        amount_matched = True
        if payment_record.sslcz_raw_response:
            expected_amount = str(payment_record.amount)
            received_amount = payment_record.sslcz_raw_response.get('amount', '0')
            amount_matched = float(expected_amount) == float(received_amount)
        
        return SSLCommerzPaymentStatus(
            transaction_id=transaction_id,
            internal_tran_id=payment_record.internal_tran_id,
            sslcz_status=payment_record.status,
            amount_matched=amount_matched,
            validation_status=payment_record.validation_response.get('status') if payment_record.validation_response else "PENDING",
            payment_method=payment_record.sslcz_payment_method,
            risk_assessment=payment_record.sslcz_raw_response.get('risk_title') if payment_record.sslcz_raw_response else None,
            processing_time=payment_record.updated_at
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
