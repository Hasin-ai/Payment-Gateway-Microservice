from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging
from ipaddress import ip_address

from app.models.audit_log import AuditLog, AuditQueue
from app.schemas.audit import AuditEventCreate, AuditLogQuery, SecurityAlert
from app.core.config import settings
from app.utils.data_masking import DataMasker

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.data_masker = DataMasker()
    
    async def create_audit_log(self, audit_event: AuditEventCreate) -> AuditLog:
        """Create a new audit log entry"""
        try:
            # Mask sensitive data if required
            old_data = audit_event.old_data
            new_data = audit_event.new_data
            meta_data = audit_event.meta_data
            
            if settings.MASK_SENSITIVE_DATA and audit_event.is_sensitive:
                old_data = self.data_masker.mask_sensitive_fields(old_data)
                new_data = self.data_masker.mask_sensitive_fields(new_data)
                meta_data = self.data_masker.mask_sensitive_fields(meta_data)
            
            # Determine compliance tags
            compliance_tags = audit_event.compliance_tags or []
            if self._requires_pci_compliance(audit_event):
                compliance_tags.append("PCI")
            if self._requires_gdpr_compliance(audit_event):
                compliance_tags.append("GDPR")
            
            # Create audit log
            audit_log = AuditLog(
                user_id=audit_event.user_id,
                action=audit_event.action,
                table_name=audit_event.table_name,
                record_id=audit_event.record_id,
                old_data=old_data,
                new_data=new_data,
                ip_address=str(audit_event.ip_address) if audit_event.ip_address else None,
                user_agent=audit_event.user_agent,
                request_id=audit_event.request_id,
                session_id=audit_event.session_id,
                service_name=audit_event.service_name,
                endpoint=audit_event.endpoint,
                method=audit_event.method,
                meta_data=meta_data,
                severity=audit_event.severity,
                category=audit_event.category,
                compliance_tags=compliance_tags,
                is_sensitive=audit_event.is_sensitive,
                is_successful=audit_event.is_successful
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.info(f"Audit log created: {audit_log.id} - {audit_log.action}")
            return audit_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create audit log: {e}")
            raise
    
    async def create_bulk_audit_logs(
        self, 
        events: List[AuditEventCreate], 
        service_name: str,
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create multiple audit logs in batch"""
        try:
            created_logs = []
            failed_logs = []
            
            for event in events:
                try:
                    if not event.service_name:
                        event.service_name = service_name
                    
                    audit_log = await self.create_audit_log(event)
                    created_logs.append(audit_log.id)
                    
                except Exception as e:
                    failed_logs.append({
                        "action": event.action,
                        "error": str(e)
                    })
            
            return {
                "batch_id": batch_id,
                "total_events": len(events),
                "created_count": len(created_logs),
                "failed_count": len(failed_logs),
                "created_log_ids": created_logs,
                "failed_logs": failed_logs
            }
            
        except Exception as e:
            logger.error(f"Failed to create bulk audit logs: {e}")
            raise
    
    async def get_audit_logs(self, query: AuditLogQuery) -> Tuple[List[AuditLog], int]:
        """Get audit logs with filtering"""
        try:
            # Build query
            db_query = self.db.query(AuditLog)
            
            # Apply filters
            if query.user_id is not None:
                db_query = db_query.filter(AuditLog.user_id == query.user_id)
            
            if query.action:
                db_query = db_query.filter(AuditLog.action.ilike(f"%{query.action}%"))
            
            if query.table_name:
                db_query = db_query.filter(AuditLog.table_name == query.table_name)
            
            if query.record_id is not None:
                db_query = db_query.filter(AuditLog.record_id == query.record_id)
            
            if query.service_name:
                db_query = db_query.filter(AuditLog.service_name == query.service_name)
            
            if query.severity:
                db_query = db_query.filter(AuditLog.severity == query.severity)
            
            if query.category:
                db_query = db_query.filter(AuditLog.category == query.category)
            
            if query.start_date:
                db_query = db_query.filter(AuditLog.created_at >= query.start_date)
            
            if query.end_date:
                db_query = db_query.filter(AuditLog.created_at <= query.end_date)
            
            if query.ip_address:
                db_query = db_query.filter(AuditLog.ip_address == query.ip_address)
            
            if query.is_successful is not None:
                db_query = db_query.filter(AuditLog.is_successful == query.is_successful)
            
            # Get total count
            total = db_query.count()
            
            # Apply pagination and ordering
            logs = db_query.order_by(desc(AuditLog.created_at)).offset((query.page - 1) * query.size).limit(query.size).all()
            
            return logs, total
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            raise
    
    async def get_audit_log_by_id(self, log_id: int, include_sensitive: bool = False) -> Optional[AuditLog]:
        """Get specific audit log by ID"""
        audit_log = self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
        
        if audit_log and not include_sensitive and audit_log.is_sensitive:
            # Mask sensitive data
            audit_log.old_data = "[REDACTED]" if audit_log.old_data else None
            audit_log.new_data = "[REDACTED]" if audit_log.new_data else None
            audit_log.meta_data = "[REDACTED]" if audit_log.meta_data else None
        
        return audit_log
    
    async def check_security_alerts(
        self, 
        user_id: Optional[int], 
        action: str, 
        ip_address: Optional[str]
    ):
        """Check for security alerts based on audit patterns"""
        try:
            # Check for failed login attempts
            if action == "login_failed" and user_id:
                await self._check_failed_login_attempts(user_id, ip_address)
            
            # Check for suspicious IP activity
            if ip_address:
                await self._check_suspicious_ip_activity(ip_address)
            
            # Check for privilege escalation attempts
            if "admin" in action.lower() or "privilege" in action.lower():
                await self._check_privilege_escalation(user_id, action)
            
            # Check for data access patterns
            if action in ["data_export", "bulk_download", "sensitive_access"]:
                await self._check_data_access_patterns(user_id, action)
            
        except Exception as e:
            logger.error(f"Failed to check security alerts: {e}")
    
    async def get_security_alerts(self, hours: int, severity: Optional[str] = None) -> List[SecurityAlert]:
        """Get security alerts for the specified period"""
        try:
            alerts = []
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Failed login attempts
            failed_logins = await self._get_failed_login_alerts(since, severity)
            alerts.extend(failed_logins)
            
            # Suspicious IP activity
            ip_alerts = await self._get_ip_security_alerts(since, severity)
            alerts.extend(ip_alerts)
            
            # Multiple account access
            account_alerts = await self._get_account_access_alerts(since, severity)
            alerts.extend(account_alerts)
            
            # Data access anomalies
            data_alerts = await self._get_data_access_alerts(since, severity)
            alerts.extend(data_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            raise
    
    async def cleanup_old_logs(self, days: int, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count logs to be deleted
            count_query = self.db.query(func.count(AuditLog.id)).filter(
                AuditLog.created_at < cutoff_date
            )
            
            total_to_delete = count_query.scalar()
            
            if dry_run:
                return {
                    "dry_run": True,
                    "cutoff_date": cutoff_date.isoformat(),
                    "logs_to_delete": total_to_delete,
                    "retention_days": days
                }
            
            # Delete old logs
            deleted_count = self.db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            return {
                "dry_run": False,
                "cutoff_date": cutoff_date.isoformat(),
                "logs_deleted": deleted_count,
                "retention_days": days
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup audit logs: {e}")
            raise
    
    async def export_audit_logs(self, query: AuditLogQuery, format: str) -> Dict[str, Any]:
        """Export audit logs in specified format"""
        try:
            # Get all logs matching the query (up to a reasonable limit)
            query.size = 10000  # Max export size
            logs, total = await self.get_audit_logs(query)
            
            if format == "json":
                return {
                    "format": "json",
                    "total_records": total,
                    "exported_records": len(logs),
                    "data": [log.to_dict(query.include_sensitive) for log in logs]
                }
            
            # For CSV and Excel, return metadata for file generation
            import uuid
            export_id = str(uuid.uuid4())
            
            return {
                "format": format,
                "export_id": export_id,
                "total_records": total,
                "exported_records": len(logs),
                "download_url": f"/api/v1/audit/download/{export_id}",
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            raise
    
    def _requires_pci_compliance(self, event: AuditEventCreate) -> bool:
        """Check if event requires PCI compliance tagging"""
        pci_actions = ["payment", "card", "transaction", "refund"]
        return any(action in event.action.lower() for action in pci_actions)
    
    def _requires_gdpr_compliance(self, event: AuditEventCreate) -> bool:
        """Check if event requires GDPR compliance tagging"""
        gdpr_actions = ["user_data", "personal_info", "privacy", "consent"]
        return any(action in event.action.lower() for action in gdpr_actions)
    
    async def _check_failed_login_attempts(self, user_id: int, ip_address: Optional[str]):
        """Check for suspicious failed login attempts"""
        try:
            since = datetime.utcnow() - timedelta(hours=1)
            
            failed_count = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= since
                )
            ).scalar()
            
            if failed_count >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD:
                logger.warning(f"Suspicious login activity: {failed_count} failed attempts for user {user_id}")
                
                # Create security alert log
                alert_event = AuditEventCreate(
                    user_id=user_id,
                    action="security_alert_failed_logins",
                    severity="WARNING",
                    category="security",
                    meta_data={
                        "failed_attempts": failed_count,
                        "time_window": "1 hour",
                        "ip_address": ip_address
                    },
                    is_sensitive=True
                )
                await self.create_audit_log(alert_event)
                
        except Exception as e:
            logger.error(f"Failed to check failed login attempts: {e}")
    
    async def _check_suspicious_ip_activity(self, ip_address: str):
        """Check for suspicious activity from IP address"""
        try:
            since = datetime.utcnow() - timedelta(hours=1)
            
            activity_count = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.ip_address == ip_address,
                    AuditLog.created_at >= since,
                    AuditLog.is_successful == False
                )
            ).scalar()
            
            if activity_count >= 20:  # 20 failed actions from same IP in 1 hour
                logger.warning(f"Suspicious IP activity: {activity_count} failed actions from {ip_address}")
                
                alert_event = AuditEventCreate(
                    action="security_alert_suspicious_ip",
                    severity="WARNING",
                    category="security",
                    ip_address=ip_address,
                    meta_data={
                        "failed_actions": activity_count,
                        "time_window": "1 hour"
                    },
                    is_sensitive=True
                )
                await self.create_audit_log(alert_event)
                
        except Exception as e:
            logger.error(f"Failed to check suspicious IP activity: {e}")
    
    async def _check_privilege_escalation(self, user_id: Optional[int], action: str):
        """Check for privilege escalation attempts"""
        try:
            if not user_id:
                return
            
            since = datetime.utcnow() - timedelta(hours=24)
            
            privilege_attempts = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action.like("%admin%"),
                    AuditLog.created_at >= since,
                    AuditLog.is_successful == False
                )
            ).scalar()
            
            if privilege_attempts >= 5:
                logger.warning(f"Potential privilege escalation: {privilege_attempts} admin attempts by user {user_id}")
                
                alert_event = AuditEventCreate(
                    user_id=user_id,
                    action="security_alert_privilege_escalation",
                    severity="ERROR",
                    category="security",
                    meta_data={
                        "admin_attempts": privilege_attempts,
                        "latest_action": action,
                        "time_window": "24 hours"
                    },
                    is_sensitive=True
                )
                await self.create_audit_log(alert_event)
                
        except Exception as e:
            logger.error(f"Failed to check privilege escalation: {e}")
    
    async def _check_data_access_patterns(self, user_id: Optional[int], action: str):
        """Check for unusual data access patterns"""
        try:
            if not user_id:
                return
            
            since = datetime.utcnow() - timedelta(hours=1)
            
            data_access_count = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action.in_(["data_export", "bulk_download", "sensitive_access"]),
                    AuditLog.created_at >= since
                )
            ).scalar()
            
            if data_access_count >= 10:  # 10 data access actions in 1 hour
                logger.warning(f"High data access activity: {data_access_count} actions by user {user_id}")
                
                alert_event = AuditEventCreate(
                    user_id=user_id,
                    action="security_alert_high_data_access",
                    severity="WARNING",
                    category="security",
                    meta_data={
                        "data_access_count": data_access_count,
                        "latest_action": action,
                        "time_window": "1 hour"
                    },
                    is_sensitive=True
                )
                await self.create_audit_log(alert_event)
                
        except Exception as e:
            logger.error(f"Failed to check data access patterns: {e}")
    
    async def _get_failed_login_alerts(self, since: datetime, severity: Optional[str]) -> List[SecurityAlert]:
        """Get failed login security alerts"""
        try:
            query = text("""
                SELECT user_id, ip_address, COUNT(*) as attempt_count,
                       MIN(created_at) as first_attempt, MAX(created_at) as last_attempt,
                       array_agg(id) as log_ids
                FROM audit_logs 
                WHERE action = 'login_failed'
                AND created_at >= :since
                GROUP BY user_id, ip_address
                HAVING COUNT(*) >= :threshold
            """)
            
            results = self.db.execute(query, {
                "since": since,
                "threshold": settings.SUSPICIOUS_ACTIVITY_THRESHOLD
            }).fetchall()
            
            alerts = []
            for row in results:
                alert = SecurityAlert(
                    alert_type="failed_login_attempts",
                    severity="WARNING",
                    user_id=row.user_id,
                    ip_address=row.ip_address,
                    description=f"Multiple failed login attempts: {row.attempt_count} attempts",
                    event_count=row.attempt_count,
                    first_occurrence=row.first_attempt,
                    last_occurrence=row.last_attempt,
                    related_logs=row.log_ids
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get failed login alerts: {e}")
            return []
    
    async def _get_ip_security_alerts(self, since: datetime, severity: Optional[str]) -> List[SecurityAlert]:
        """Get IP-based security alerts"""
        try:
            query = text("""
                SELECT ip_address, COUNT(*) as action_count,
                       COUNT(DISTINCT user_id) as user_count,
                       MIN(created_at) as first_action, MAX(created_at) as last_action,
                       array_agg(id) as log_ids
                FROM audit_logs 
                WHERE created_at >= :since
                AND is_successful = false
                AND ip_address IS NOT NULL
                GROUP BY ip_address
                HAVING COUNT(*) >= 20 OR COUNT(DISTINCT user_id) >= 5
            """)
            
            results = self.db.execute(query, {"since": since}).fetchall()
            
            alerts = []
            for row in results:
                if row.action_count >= 20:
                    description = f"High failure rate from IP: {row.action_count} failed actions"
                    alert_type = "suspicious_ip_activity"
                else:
                    description = f"Multiple user targeting from IP: {row.user_count} different users"
                    alert_type = "ip_user_enumeration"
                
                alert = SecurityAlert(
                    alert_type=alert_type,
                    severity="WARNING",
                    user_id=None,
                    ip_address=row.ip_address,
                    description=description,
                    event_count=row.action_count,
                    first_occurrence=row.first_action,
                    last_occurrence=row.last_action,
                    related_logs=row.log_ids
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get IP security alerts: {e}")
            return []
    
    async def _get_account_access_alerts(self, since: datetime, severity: Optional[str]) -> List[SecurityAlert]:
        """Get account access security alerts"""
        try:
            query = text("""
                SELECT user_id, COUNT(DISTINCT ip_address) as ip_count,
                       COUNT(*) as action_count,
                       MIN(created_at) as first_action, MAX(created_at) as last_action,
                       array_agg(DISTINCT ip_address::text) as ip_addresses,
                       array_agg(id) as log_ids
                FROM audit_logs 
                WHERE created_at >= :since
                AND user_id IS NOT NULL
                AND action LIKE '%login%'
                GROUP BY user_id
                HAVING COUNT(DISTINCT ip_address) >= 3
            """)
            
            results = self.db.execute(query, {"since": since}).fetchall()
            
            alerts = []
            for row in results:
                alert = SecurityAlert(
                    alert_type="multiple_ip_access",
                    severity="INFO",
                    user_id=row.user_id,
                    ip_address=None,
                    description=f"Account accessed from {row.ip_count} different IPs: {', '.join(row.ip_addresses)}",
                    event_count=row.action_count,
                    first_occurrence=row.first_action,
                    last_occurrence=row.last_action,
                    related_logs=row.log_ids
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get account access alerts: {e}")
            return []
    
    async def _get_data_access_alerts(self, since: datetime, severity: Optional[str]) -> List[SecurityAlert]:
        """Get data access security alerts"""
        try:
            query = text("""
                SELECT user_id, COUNT(*) as access_count,
                       MIN(created_at) as first_access, MAX(created_at) as last_access,
                       array_agg(action) as actions,
                       array_agg(id) as log_ids
                FROM audit_logs 
                WHERE created_at >= :since
                AND user_id IS NOT NULL
                AND (action LIKE '%export%' OR action LIKE '%download%' OR action LIKE '%sensitive%')
                GROUP BY user_id
                HAVING COUNT(*) >= 5
            """)
            
            results = self.db.execute(query, {"since": since}).fetchall()
            
            alerts = []
            for row in results:
                alert = SecurityAlert(
                    alert_type="high_data_access",
                    severity="WARNING",
                    user_id=row.user_id,
                    ip_address=None,
                    description=f"High data access activity: {row.access_count} data operations",
                    event_count=row.access_count,
                    first_occurrence=row.first_access,
                    last_occurrence=row.last_access,
                    related_logs=row.log_ids
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get data access alerts: {e}")
            return []
