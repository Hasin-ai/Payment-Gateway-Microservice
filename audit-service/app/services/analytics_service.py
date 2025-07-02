from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.models.audit_log import AuditLog
from app.schemas.audit import AuditStats

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_audit_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[int] = None,
        service_name: Optional[str] = None
    ) -> AuditStats:
        """Get comprehensive audit statistics"""
        try:
            base_query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            )
            
            if user_id:
                base_query = base_query.filter(AuditLog.user_id == user_id)
            
            if service_name:
                base_query = base_query.filter(AuditLog.service_name == service_name)
            
            # Total logs
            total_logs = base_query.count()
            
            # Logs by severity
            severity_stats = {}
            severity_results = base_query.with_entities(
                AuditLog.severity, func.count(AuditLog.id)
            ).group_by(AuditLog.severity).all()
            
            for severity, count in severity_results:
                severity_stats[severity] = count
            
            # Logs by category
            category_stats = {}
            category_results = base_query.filter(
                AuditLog.category.isnot(None)
            ).with_entities(
                AuditLog.category, func.count(AuditLog.id)
            ).group_by(AuditLog.category).all()
            
            for category, count in category_results:
                category_stats[category] = count
            
            # Logs by service
            service_stats = {}
            service_results = base_query.filter(
                AuditLog.service_name.isnot(None)
            ).with_entities(
                AuditLog.service_name, func.count(AuditLog.id)
            ).group_by(AuditLog.service_name).all()
            
            for service, count in service_results:
                service_stats[service] = count
            
            # Success/failure stats
            failed_actions = base_query.filter(AuditLog.is_successful == False).count()
            successful_actions = base_query.filter(AuditLog.is_successful == True).count()
            
            # Unique users
            unique_users = base_query.filter(
                AuditLog.user_id.isnot(None)
            ).distinct(AuditLog.user_id).count()
            
            return AuditStats(
                total_logs=total_logs,
                logs_by_severity=severity_stats,
                logs_by_category=category_stats,
                logs_by_service=service_stats,
                failed_actions=failed_actions,
                successful_actions=successful_actions,
                unique_users=unique_users,
                date_range={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            raise
    
    async def get_activity_trends(self, days: int, granularity: str) -> Dict[str, Any]:
        """Get activity trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            if granularity == "hourly":
                date_trunc = "hour"
                expected_points = days * 24
            elif granularity == "daily":
                date_trunc = "day"
                expected_points = days
            else:  # weekly
                date_trunc = "week"
                expected_points = days // 7
            
            query = text(f"""
                SELECT 
                    date_trunc('{date_trunc}', created_at) as time_bucket,
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN severity = 'ERROR' THEN 1 END) as error_events,
                    COUNT(CASE WHEN severity = 'WARNING' THEN 1 END) as warning_events,
                    COUNT(CASE WHEN is_successful = false THEN 1 END) as failed_events,
                    COUNT(DISTINCT user_id) as unique_users
                FROM audit_logs 
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
            
            results = self.db.execute(query, {
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()
            
            trends = []
            for row in results:
                trends.append({
                    "time_bucket": row.time_bucket.isoformat(),
                    "total_events": row.total_events,
                    "error_events": row.error_events,
                    "warning_events": row.warning_events,
                    "failed_events": row.failed_events,
                    "unique_users": row.unique_users
                })
            
            return {
                "granularity": granularity,
                "period_days": days,
                "expected_data_points": expected_points,
                "actual_data_points": len(trends),
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Failed to get activity trends: {e}")
            raise
    
    async def generate_compliance_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        compliance_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            base_query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            )
            
            if compliance_tag:
                base_query = base_query.filter(
                    AuditLog.compliance_tags.contains([compliance_tag])
                )
            
            # Total compliance events
            total_events = base_query.count()
            
            # Events by compliance tag
            compliance_stats = {}
            if not compliance_tag:
                compliance_query = text("""
                    SELECT 
                        tag,
                        COUNT(*) as event_count
                    FROM audit_logs, 
                         jsonb_array_elements_text(compliance_tags) as tag
                    WHERE created_at >= :start_date AND created_at <= :end_date
                    GROUP BY tag
                    ORDER BY event_count DESC
                """)
                
                compliance_results = self.db.execute(compliance_query, {
                    "start_date": start_date,
                    "end_date": end_date
                }).fetchall()
                
                for row in compliance_results:
                    compliance_stats[row.tag] = row.event_count
            
            # Sensitive data access events
            sensitive_events = base_query.filter(AuditLog.is_sensitive == True).count()
            
            # Failed compliance events
            failed_events = base_query.filter(AuditLog.is_successful == False).count()
            
            # User activity for compliance
            user_activity = base_query.filter(
                AuditLog.user_id.isnot(None)
            ).with_entities(
                AuditLog.user_id, func.count(AuditLog.id)
            ).group_by(AuditLog.user_id).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            top_users = [{"user_id": user_id, "event_count": count} for user_id, count in user_activity]
            
            return {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "compliance_tag": compliance_tag,
                "summary": {
                    "total_events": total_events,
                    "sensitive_events": sensitive_events,
                    "failed_events": failed_events,
                    "compliance_coverage": compliance_stats
                },
                "top_users": top_users,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise
    
    async def detect_anomalies(self, hours: int, threshold: float) -> List[Dict[str, Any]]:
        """Detect anomalous activity patterns"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get baseline activity (previous period)
            baseline_start = start_time - timedelta(hours=hours)
            baseline_end = start_time
            
            # Current period activity by user
            current_query = text("""
                SELECT 
                    user_id,
                    COUNT(*) as current_activity,
                    COUNT(CASE WHEN is_successful = false THEN 1 END) as current_failures
                FROM audit_logs 
                WHERE created_at >= :start_time AND created_at <= :end_time
                AND user_id IS NOT NULL
                GROUP BY user_id
            """)
            
            # Baseline period activity by user
            baseline_query = text("""
                SELECT 
                    user_id,
                    COUNT(*) as baseline_activity,
                    COUNT(CASE WHEN is_successful = false THEN 1 END) as baseline_failures
                FROM audit_logs 
                WHERE created_at >= :baseline_start AND created_at <= :baseline_end
                AND user_id IS NOT NULL
                GROUP BY user_id
            """)
            
            current_results = self.db.execute(current_query, {
                "start_time": start_time,
                "end_time": end_time
            }).fetchall()
            
            baseline_results = self.db.execute(baseline_query, {
                "baseline_start": baseline_start,
                "baseline_end": baseline_end
            }).fetchall()
            
            # Create lookup for baseline data
            baseline_data = {row.user_id: row for row in baseline_results}
            
            anomalies = []
            
            for current_row in current_results:
                user_id = current_row.user_id
                current_activity = current_row.current_activity
                current_failures = current_row.current_failures
                
                baseline_row = baseline_data.get(user_id)
                baseline_activity = baseline_row.baseline_activity if baseline_row else 0
                baseline_failures = baseline_row.baseline_failures if baseline_row else 0
                
                # Check for activity anomalies
                if baseline_activity > 0:
                    activity_ratio = current_activity / baseline_activity
                    if activity_ratio >= threshold:
                        anomalies.append({
                            "type": "high_activity",
                            "user_id": user_id,
                            "current_activity": current_activity,
                            "baseline_activity": baseline_activity,
                            "ratio": activity_ratio,
                            "severity": "WARNING" if activity_ratio < threshold * 2 else "ERROR"
                        })
                
                # Check for failure anomalies
                if baseline_failures == 0 and current_failures > 5:
                    anomalies.append({
                        "type": "new_failures",
                        "user_id": user_id,
                        "current_failures": current_failures,
                        "baseline_failures": baseline_failures,
                        "severity": "WARNING"
                    })
                elif baseline_failures > 0:
                    failure_ratio = current_failures / baseline_failures
                    if failure_ratio >= threshold:
                        anomalies.append({
                            "type": "increased_failures",
                            "user_id": user_id,
                            "current_failures": current_failures,
                            "baseline_failures": baseline_failures,
                            "ratio": failure_ratio,
                            "severity": "ERROR"
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
