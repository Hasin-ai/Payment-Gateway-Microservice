import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_address = settings.EMAIL_FROM_ADDRESS
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
        attachments: list = None
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_address}>"
            message["To"] = to_email
            
            # Add body
            if is_html:
                html_part = MIMEText(body, "html")
                message.attach(html_part)
            else:
                text_part = MIMEText(body, "plain")
                message.attach(text_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    message.attach(attachment)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                
                server.login(self.username, self.password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            
            return {
                "success": True,
                "message_id": f"email_{hash(to_email + subject)}",
                "recipient": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }
    
    async def send_bulk_email(
        self,
        recipients: list,
        subject: str,
        body: str,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """Send bulk emails"""
        successful_sends = 0
        failed_sends = 0
        results = []
        
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body, is_html)
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
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
