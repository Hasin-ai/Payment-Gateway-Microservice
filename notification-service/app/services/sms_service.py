from typing import Dict, Any
import logging
import httpx
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.provider = settings.SMS_PROVIDER
        self.api_key = settings.SMS_API_KEY
        self.api_secret = settings.SMS_API_SECRET
        self.from_number = settings.SMS_FROM_NUMBER
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via configured provider"""
        try:
            if self.provider == "twilio":
                return await self._send_via_twilio(to_number, message)
            elif self.provider == "nexmo":
                return await self._send_via_nexmo(to_number, message)
            else:
                # Mock SMS sending for development
                return await self._send_mock_sms(to_number, message)
                
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_number
            }
    
    async def _send_via_twilio(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            twilio_message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent via Twilio to {to_number}")
            
            return {
                "success": True,
                "message_id": twilio_message.sid,
                "recipient": to_number,
                "provider": "twilio",
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Twilio SMS failed for {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_number,
                "provider": "twilio"
            }
    
    async def _send_via_nexmo(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Nexmo/Vonage"""
        try:
            url = "https://rest.nexmo.com/sms/json"
            
            data = {
                "from": self.from_number,
                "text": message,
                "to": to_number,
                "api_key": self.api_key,
                "api_secret": self.api_secret
            }
            
            response = await self.http_client.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result["messages"][0]["status"] == "0":
                logger.info(f"SMS sent via Nexmo to {to_number}")
                return {
                    "success": True,
                    "message_id": result["messages"][0]["message-id"],
                    "recipient": to_number,
                    "provider": "nexmo",
                    "sent_at": datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Nexmo error: {result['messages'][0]['error-text']}")
                
        except Exception as e:
            logger.error(f"Nexmo SMS failed for {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_number,
                "provider": "nexmo"
            }
    
    async def _send_mock_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending for development"""
        logger.info(f"MOCK SMS to {to_number}: {message}")
        
        return {
            "success": True,
            "message_id": f"mock_sms_{hash(to_number + message)}",
            "recipient": to_number,
            "provider": "mock",
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def send_bulk_sms(
        self,
        recipients: list,
        message: str
    ) -> Dict[str, Any]:
        """Send bulk SMS messages"""
        successful_sends = 0
        failed_sends = 0
        results = []
        
        for recipient in recipients:
            result = await self.send_sms(recipient, message)
            if result["success"]:
                successful_sends += 1
            else:
                failed_sends += 1
            results.append(result)
        
        return {
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "results": results
        }
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        import re
        # Bangladesh phone number pattern
        pattern = r'^\+880[1-9]\d{8}$'
        return re.match(pattern, phone_number) is not None
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
