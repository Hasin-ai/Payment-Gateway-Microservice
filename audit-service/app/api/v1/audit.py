from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditEventCreate, AuditEventResponse, AuditLogQuery,
    AuditLogList, BulkAuditCreate, SecurityAlert
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_service, require_admin_or_system

router = APIRouter()

@router.post("/log", response_model=SuccessResponse[AuditEventResponse])
async def create_audit_log(
    audit_event: AuditEventCreate,
    background_tasks: BackgroundTasks,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Create a new audit log entry"""
    try:
        audit_service = AuditService(db)
        
        # Add service context if not provided
        if not audit_event.service_name:
            audit_event.service_name = current_service.name
        
        # Create audit log
        audit_log = await audit_service.create_audit_log(audit_event)
        
        # Process security alerts in background
        background_tasks.add_task(
            audit_service.check_security_alerts,
            audit_event.user_id,
            audit_event.action,
            audit_event.ip_address
        )
        
        return SuccessResponse(
            message="Audit log created successfully",
            data=AuditEventResponse.from_orm(audit_log)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit log"
        )

@router.post("/bulk", response_model=SuccessResponse)
async def create_bulk_audit_logs(
    bulk_audit: BulkAuditCreate,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Create multiple audit log entries in batch"""
    try:
        audit_service = AuditService(db)
        
        result = await audit_service.create_bulk_audit_logs(
            bulk_audit.events,
            current_service.name,
            bulk_audit.batch_id
        )
        
        return SuccessResponse(
            message="Bulk audit logs created successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk audit logs"
        )

@router.get("/logs", response_model=SuccessResponse[AuditLogList])
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    record_id: Optional[int] = Query(None),
    service_name: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None),
    is_successful: Optional[bool] = Query(None),
    include_sensitive: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering and pagination"""
    try:
        audit_service = AuditService(db)
        
        query = AuditLogQuery(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            service_name=service_name,
            severity=severity,
            category=category,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            is_successful=is_successful,
            include_sensitive=include_sensitive,
            page=page,
            size=size
        )
        
        logs, total = await audit_service.get_audit_logs(query)
        
        has_next = (page * size) < total
        has_previous = page > 1
        
        return SuccessResponse(
            message="Audit logs retrieved successfully",
            data=AuditLogList(
                logs=[AuditEventResponse.from_orm(log) for log in logs],
                total=total,
                page=page,
                size=size,
                has_next=has_next,
                has_previous=has_previous
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )

@router.get("/logs/{log_id}", response_model=SuccessResponse[AuditEventResponse])
async def get_audit_log(
    log_id: int,
    include_sensitive: bool = Query(False),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get specific audit log by ID"""
    try:
        audit_service = AuditService(db)
        audit_log = await audit_service.get_audit_log_by_id(log_id, include_sensitive)
        
        if not audit_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return SuccessResponse(
            message="Audit log retrieved successfully",
            data=AuditEventResponse.from_orm(audit_log)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )

@router.get("/user/{user_id}/activity", response_model=SuccessResponse[AuditLogList])
async def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get user activity logs for the specified period"""
    try:
        audit_service = AuditService(db)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = AuditLogQuery(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )
        
        logs, total = await audit_service.get_audit_logs(query)
        
        has_next = (page * size) < total
        has_previous = page > 1
        
        return SuccessResponse(
            message="User activity retrieved successfully",
            data=AuditLogList(
                logs=[AuditEventResponse.from_orm(log) for log in logs],
                total=total,
                page=page,
                size=size,
                has_next=has_next,
                has_previous=has_previous
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )

@router.get("/security/alerts", response_model=SuccessResponse[List[SecurityAlert]])
async def get_security_alerts(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    severity: Optional[str] = Query(None),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get security alerts for the specified time period"""
    try:
        audit_service = AuditService(db)
        alerts = await audit_service.get_security_alerts(hours, severity)
        
        return SuccessResponse(
            message="Security alerts retrieved successfully",
            data=alerts
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security alerts"
        )

@router.delete("/cleanup", response_model=SuccessResponse)
async def cleanup_old_logs(
    days: int = Query(365, ge=30),  # Minimum 30 days retention
    dry_run: bool = Query(True),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Clean up old audit logs (admin only)"""
    try:
        audit_service = AuditService(db)
        result = await audit_service.cleanup_old_logs(days, dry_run)
        
        message = "Cleanup completed" if not dry_run else "Cleanup analysis completed (dry run)"
        
        return SuccessResponse(
            message=message,
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup audit logs"
        )

@router.post("/export", response_model=SuccessResponse)
async def export_audit_logs(
    query: AuditLogQuery,
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Export audit logs in specified format"""
    try:
        audit_service = AuditService(db)
        export_result = await audit_service.export_audit_logs(query, format)
        
        return SuccessResponse(
            message="Audit logs export initiated",
            data=export_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs"
        )
