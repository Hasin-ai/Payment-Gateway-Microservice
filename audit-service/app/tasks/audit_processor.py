import asyncio
import logging
from datetime import datetime
import json
from typing import Dict

from app.core.database import get_db_session
from app.services.audit_service import AuditService
from app.models.audit_log import AuditQueue
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuditProcessor:
    def __init__(self):
        self.running = False
        self.process_interval = settings.AUDIT_PROCESSOR_INTERVAL
    
    async def start_processing(self):
        """Start the audit processor"""
        self.running = True
        logger.info(f"Starting audit processor with {self.process_interval}s interval")
        
        while self.running:
            try:
                await self.process_queued_events()
                await asyncio.sleep(self.process_interval)
            except asyncio.CancelledError:
                logger.info("Audit processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in audit processor: {e}")
                await asyncio.sleep(self.process_interval)
    
    async def process_queued_events(self):
        """Process queued audit events"""
        try:
            db = get_db_session()
            audit_service = AuditService(db)
            
            # Get pending events
            pending_events = db.query(AuditQueue).filter(
                AuditQueue.status == "PENDING"
            ).order_by(
                AuditQueue.priority.asc(),
                AuditQueue.created_at.asc()
            ).limit(settings.MAX_AUDIT_BATCH_SIZE).all()
            
            for event in pending_events:
                try:
                    # Mark as processing
                    event.status = "PROCESSING"
                    event.processing_attempts += 1
                    event.last_attempt_at = datetime.utcnow()
                    db.commit()
                    
                    # Process the event
                    await self._process_single_event(event, audit_service)
                    
                    # Mark as completed
                    event.status = "COMPLETED"
                    event.processed_at = datetime.utcnow()
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to process audit event {event.id}: {e}")
                    
                    # Mark as failed if max attempts reached
                    if event.processing_attempts >= 3:
                        event.status = "FAILED"
                        event.error_message = str(e)
                    else:
                        event.status = "PENDING"  # Retry later
                    
                    db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to process queued audit events: {e}")
    
    async def _process_single_event(self, event: AuditQueue, audit_service: AuditService):
        """Process a single audit event"""
        try:
            payload = event.payload
            
            if event.event_type == "audit_log":
                # Create audit log from payload
                from app.schemas.audit import AuditEventCreate
                audit_event = AuditEventCreate(**payload)
                await audit_service.create_audit_log(audit_event)
                
            elif event.event_type == "security_alert":
                # Process security alert
                await self._process_security_alert(payload, audit_service)
                
            elif event.event_type == "compliance_event":
                # Process compliance event
                await self._process_compliance_event(payload, audit_service)
                
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
            
        except Exception as e:
            logger.error(f"Failed to process audit event {event.id}: {e}")
            raise
    
    async def _process_security_alert(self, payload: Dict, audit_service: AuditService):
        """Process security alert event"""
        try:
            # Create audit log for security alert
            from app.schemas.audit import AuditEventCreate
            
            alert_event = AuditEventCreate(
                user_id=payload.get("user_id"),
                action="security_alert",
                severity="WARNING",
                category="security",
                meta_data=payload,
                is_sensitive=True
            )
            
            await audit_service.create_audit_log(alert_event)
            
        except Exception as e:
            logger.error(f"Failed to process security alert: {e}")
            raise
    
    async def _process_compliance_event(self, payload: Dict, audit_service: AuditService):
        """Process compliance event"""
        try:
            # Create audit log for compliance event
            from app.schemas.audit import AuditEventCreate
            
            compliance_event = AuditEventCreate(
                user_id=payload.get("user_id"),
                action="compliance_event",
                severity="INFO",
                category="compliance",
                compliance_tags=payload.get("compliance_tags", []),
                meta_data=payload,
                is_sensitive=True
            )
            
            await audit_service.create_audit_log(compliance_event)
            
        except Exception as e:
            logger.error(f"Failed to process compliance event: {e}")
            raise
    
    def stop(self):
        """Stop the processor"""
        self.running = False
        logger.info("Stopping audit processor")
