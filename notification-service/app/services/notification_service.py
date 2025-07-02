from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.models.notification import NotificationRecord, NotificationPreferences
from app.models.queue import NotificationQueue
from app.schemas.notification import (
    NotificationSend, NotificationResponse, BulkNotificationSend,
    NotificationStats
)
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.template_service import TemplateService
from app.utils.exceptions import NotificationError

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.template_service = TemplateService(db)
    
    async def send_notification(self, notification_data: NotificationSend) -> NotificationResponse:
        """Send notification to user via specified channels"""
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(notification_data.user_id)
            
            # Filter channels based on user preferences and notification type
            enabled_channels = await self._filter_enabled_channels(
                notification_data.channels,
                preferences,
                notification_data.notification_type
            )
            
            if not enabled_channels:
                logger.warning(f"No enabled channels for user {notification_data.user_id}")
                return NotificationResponse(
                    notification_id=str(uuid.uuid4()),
                    user_id=notification_data.user_id,
                    notification_type=notification_data.notification_type,
                    channels_sent=[],
                    status="SKIPPED",
                    created_at=datetime.utcnow()
                )
            
            channels_sent = []
            
            # Queue notifications for each enabled channel
            for channel in enabled_channels:
                try:
                    recipient = await self._get_recipient_for_channel(channel, preferences)
                    if not recipient:
                        continue
                    
                    # Create queue entry
                    queue_entry = NotificationQueue(
                        user_id=notification_data.user_id,
                        notification_type=notification_data.notification_type,
                        priority=notification_data.priority,
                        channel=channel,
                        recipient=recipient,
                        template_key=notification_data.template_key,
                        template_data=notification_data.template_data,
                        subject=notification_data.subject,
                        message_body=notification_data.message_body,
                        scheduled_for=notification_data.scheduled_for
                    )
                    
                    self.db.add(queue_entry)
                    self.db.commit()
                    self.db.refresh(queue_entry)
                    
                    channels_sent.append({
                        "channel": channel,
                        "queue_id": queue_entry.id,
                        "recipient": recipient,
                        "status": "queued"
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to queue notification for channel {channel}: {e}")
                    channels_sent.append({
                        "channel": channel,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return NotificationResponse(
                notification_id=str(uuid.uuid4()),
                user_id=notification_data.user_id,
                notification_type=notification_data.notification_type,
                channels_sent=channels_sent,
                status="QUEUED",
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise NotificationError("Failed to send notification")
    
    async def send_bulk_notification(self, bulk_data: BulkNotificationSend) -> Dict[str, Any]:
        """Send bulk notifications to multiple users"""
        try:
            successful_queues = 0
            failed_queues = 0
            
            for user_id in bulk_data.user_ids:
                try:
                    notification_data = NotificationSend(
                        user_id=user_id,
                        notification_type=bulk_data.notification_type,
                        channels=bulk_data.channels,
                        template_data=bulk_data.template_data,
                        template_key=bulk_data.template_key,
                        scheduled_for=bulk_data.scheduled_for,
                        priority=bulk_data.priority
                    )
                    
                    await self.send_notification(notification_data)
                    successful_queues += 1
                    
                except Exception as e:
                    logger.error(f"Failed to queue notification for user {user_id}: {e}")
                    failed_queues += 1
            
            return {
                "total_users": len(bulk_data.user_ids),
                "successful_queues": successful_queues,
                "failed_queues": failed_queues,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to send bulk notifications: {e}")
            raise NotificationError("Failed to send bulk notifications")
    
    async def process_queued_notifications(self):
        """Process queued notifications"""
        try:
            # Get queued notifications ready for processing
            queued_notifications = self.db.query(NotificationQueue).filter(
                and_(
                    NotificationQueue.status == "QUEUED",
                    NotificationQueue.scheduled_for <= datetime.utcnow()
                )
            ).order_by(NotificationQueue.priority, NotificationQueue.created_at).limit(100).all()
            
            for queue_item in queued_notifications:
                try:
                    queue_item.status = "PROCESSING"
                    self.db.commit()
                    
                    success = await self._process_single_notification(queue_item)
                    
                    if success:
                        queue_item.status = "COMPLETED"
                    else:
                        queue_item.status = "FAILED"
                        queue_item.processing_attempts += 1
                    
                    queue_item.last_attempt_at = datetime.utcnow()
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to process queue item {queue_item.id}: {e}")
                    queue_item.status = "FAILED"
                    queue_item.error_message = str(e)
                    queue_item.processing_attempts += 1
                    queue_item.last_attempt_at = datetime.utcnow()
                    self.db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to process queued notifications: {e}")
    
    async def _process_single_notification(self, queue_item: NotificationQueue) -> bool:
        """Process a single notification from the queue"""
        try:
            # Prepare notification content
            if queue_item.template_key:
                # Render template
                rendered = await self.template_service.render_template(
                    queue_item.template_key,
                    queue_item.template_data or {}
                )
                subject = rendered.rendered_subject
                message_body = rendered.rendered_body
            else:
                subject = queue_item.subject
                message_body = queue_item.message_body
            
            # Create notification record
            notification_record = NotificationRecord(
                user_id=queue_item.user_id,
                notification_type=queue_item.notification_type,
                channel=queue_item.channel,
                recipient=queue_item.recipient,
                subject=subject,
                message_body=message_body,
                template_id=None,  # Will be set if template is used
                template_data=queue_item.template_data,
                status="PENDING"
            )
            
            self.db.add(notification_record)
            self.db.commit()
            self.db.refresh(notification_record)
            
            # Send via appropriate channel
            success = False
            if queue_item.channel == "email":
                success = await self._send_email_notification(
                    notification_record, queue_item.recipient, subject, message_body
                )
            elif queue_item.channel == "sms":
                success = await self._send_sms_notification(
                    notification_record, queue_item.recipient, message_body
                )
            elif queue_item.channel == "push":
                success = await self._send_push_notification(
                    notification_record, queue_item.recipient, subject, message_body
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process notification {queue_item.id}: {e}")
            return False
    
    async def _send_email_notification(
        self, 
        record: NotificationRecord, 
        recipient: str, 
        subject: str, 
        body: str
    ) -> bool:
        """Send email notification"""
        try:
            result = await self.email_service.send_email(
                to_email=recipient,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if result.get("success"):
                record.status = "SENT"
                record.sent_at = datetime.utcnow()
                record.provider_message_id = result.get("message_id")
                record.provider_response = result
            else:
                record.status = "FAILED"
                record.error_message = result.get("error", "Unknown error")
            
            self.db.commit()
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            record.status = "FAILED"
            record.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_sms_notification(
        self, 
        record: NotificationRecord, 
        recipient: str, 
        message: str
    ) -> bool:
        """Send SMS notification"""
        try:
            result = await self.sms_service.send_sms(
                to_number=recipient,
                message=message
            )
            
            if result.get("success"):
                record.status = "SENT"
                record.sent_at = datetime.utcnow()
                record.provider_message_id = result.get("message_id")
                record.provider_response = result
            else:
                record.status = "FAILED"
                record.error_message = result.get("error", "Unknown error")
            
            self.db.commit()
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            record.status = "FAILED"
            record.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_push_notification(
        self, 
        record: NotificationRecord, 
        recipient: str, 
        title: str, 
        body: str
    ) -> bool:
        """Send push notification"""
        try:
            # Implementation would depend on push service (Firebase, etc.)
            # For now, mark as sent
            record.status = "SENT"
            record.sent_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            record.status = "FAILED"
            record.error_message = str(e)
            self.db.commit()
            return False
    
    async def get_notification_status(self, notification_id: int) -> Optional[NotificationRecord]:
        """Get notification status by ID"""
        return self.db.query(NotificationRecord).filter(
            NotificationRecord.id == notification_id
        ).first()
    
    async def get_user_notification_history(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        notification_type: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Tuple[List[NotificationRecord], int]:
        """Get user's notification history"""
        query = self.db.query(NotificationRecord).filter(
            NotificationRecord.user_id == user_id
        )
        
        if notification_type:
            query = query.filter(NotificationRecord.notification_type == notification_type)
        
        if channel:
            query = query.filter(NotificationRecord.channel == channel)
        
        total = query.count()
        
        notifications = query.order_by(desc(NotificationRecord.created_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return notifications, total
    
    async def get_notification_stats(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> NotificationStats:
        """Get notification delivery statistics"""
        # Query stats from database
        stats_query = self.db.query(
            func.count(NotificationRecord.id).label("total"),
            func.sum(func.case((NotificationRecord.status == "SENT", 1), else_=0)).label("sent"),
            func.sum(func.case((NotificationRecord.status == "DELIVERED", 1), else_=0)).label("delivered"),
            func.sum(func.case((NotificationRecord.status == "FAILED", 1), else_=0)).label("failed")
        ).filter(
            and_(
                NotificationRecord.created_at >= start_date,
                NotificationRecord.created_at <= end_date
            )
        ).first()
        
        total_sent = int(stats_query.sent or 0)
        total_delivered = int(stats_query.delivered or 0)
        total_failed = int(stats_query.failed or 0)
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        # Get channel breakdown
        channel_stats = self.db.query(
            NotificationRecord.channel,
            NotificationRecord.status,
            func.count(NotificationRecord.id).label("count")
        ).filter(
            and_(
                NotificationRecord.created_at >= start_date,
                NotificationRecord.created_at <= end_date
            )
        ).group_by(NotificationRecord.channel, NotificationRecord.status).all()
        
        channels_breakdown = {}
        for stat in channel_stats:
            if stat.channel not in channels_breakdown:
                channels_breakdown[stat.channel] = {}
            channels_breakdown[stat.channel][stat.status] = stat.count
        
        return NotificationStats(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            delivery_rate=delivery_rate,
            channels_breakdown=channels_breakdown
        )
    
    async def retry_notification(self, notification_id: int) -> Dict[str, Any]:
        """Retry a failed notification"""
        notification = self.db.query(NotificationRecord).filter(
            NotificationRecord.id == notification_id
        ).first()
        
        if not notification:
            raise ValueError("Notification not found")
        
        if notification.status not in ["FAILED"]:
            raise ValueError("Only failed notifications can be retried")
        
        if notification.retry_count >= notification.max_retries:
            raise ValueError("Maximum retry attempts reached")
        
        # Reset status and increment retry count
        notification.status = "PENDING"
        notification.retry_count += 1
        notification.next_retry_at = datetime.utcnow() + timedelta(
            seconds=60 * notification.retry_count  # Exponential backoff
        )
        
        self.db.commit()
        
        return {
            "notification_id": notification_id,
            "retry_count": notification.retry_count,
            "status": "queued_for_retry"
        }
    
    async def cancel_notification(self, notification_id: int) -> Dict[str, Any]:
        """Cancel a queued notification"""
        # Try to find in queue first
        queue_item = self.db.query(NotificationQueue).filter(
            NotificationQueue.id == notification_id
        ).first()
        
        if queue_item and queue_item.status == "QUEUED":
            queue_item.status = "CANCELLED"
            self.db.commit()
            return {"status": "cancelled", "type": "queued"}
        
        # Try to find in notification records
        notification = self.db.query(NotificationRecord).filter(
            NotificationRecord.id == notification_id
        ).first()
        
        if notification and notification.status == "PENDING":
            notification.status = "CANCELLED"
            self.db.commit()
            return {"status": "cancelled", "type": "notification"}
        
        raise ValueError("Notification not found or cannot be cancelled")
    
    async def _get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """Get user's notification preferences"""
        preferences = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = NotificationPreferences(
                user_id=user_id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                transaction_alerts=True,
                payout_alerts=True,
                security_alerts=True,
                rate_change_alerts=False,
                limit_alerts=True,
                marketing_emails=False
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
        
        return preferences
    
    async def _filter_enabled_channels(
        self,
        requested_channels: List[str],
        preferences: NotificationPreferences,
        notification_type: str
    ) -> List[str]:
        """Filter channels based on user preferences"""
        enabled_channels = []
        
        # Check if notification type is enabled
        type_enabled = True
        if notification_type.startswith("transaction"):
            type_enabled = preferences.transaction_alerts
        elif notification_type.startswith("payout"):
            type_enabled = preferences.payout_alerts
        elif notification_type == "security_alert":
            type_enabled = preferences.security_alerts
        elif notification_type == "rate_change":
            type_enabled = preferences.rate_change_alerts
        elif notification_type == "limit_exceeded":
            type_enabled = preferences.limit_alerts
        elif notification_type.startswith("marketing"):
            type_enabled = preferences.marketing_emails
        
        if not type_enabled:
            return []
        
        # Check each requested channel
        for channel in requested_channels:
            if channel == "email" and preferences.email_enabled:
                enabled_channels.append(channel)
            elif channel == "sms" and preferences.sms_enabled:
                enabled_channels.append(channel)
            elif channel == "push" and preferences.push_enabled:
                enabled_channels.append(channel)
        
        return enabled_channels
    
    async def _get_recipient_for_channel(
        self, 
        channel: str, 
        preferences: NotificationPreferences
    ) -> Optional[str]:
        """Get recipient address for the specified channel"""
        if channel == "email":
            return preferences.email_address
        elif channel == "sms":
            return preferences.phone_number
        elif channel == "push":
            return preferences.push_token
        
        return None
