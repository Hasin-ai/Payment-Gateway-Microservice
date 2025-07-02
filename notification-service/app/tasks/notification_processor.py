import asyncio
import logging
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.services.notification_service import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationProcessor:
    def __init__(self):
        self.running = False
        self.process_interval = settings.QUEUE_PROCESSOR_INTERVAL
    
    async def start_processing(self):
        """Start the notification processor"""
        self.running = True
        logger.info(f"Starting notification processor with {self.process_interval}s interval")
        
        while self.running:
            try:
                await self.process_notifications()
                await asyncio.sleep(self.process_interval)
            except asyncio.CancelledError:
                logger.info("Notification processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")
                await asyncio.sleep(self.process_interval)
    
    async def process_notifications(self):
        """Process queued notifications"""
        try:
            db = get_db_session()
            notification_service = NotificationService(db)
            
            await notification_service.process_queued_notifications()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to process notifications: {e}")
    
    def stop(self):
        """Stop the processor"""
        self.running = False
        logger.info("Stopping notification processor")
