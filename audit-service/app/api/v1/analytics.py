from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.audit import AuditStats
from app.utils.response import SuccessResponse
from app.utils.auth import require_admin_or_system

router = APIRouter()

@router.get("/stats", response_model=SuccessResponse[AuditStats])
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[int] = Query(None),
    service_name: Optional[str] = Query(None),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get audit statistics for the specified period"""
    try:
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = await analytics_service.get_audit_statistics(
            start_date, end_date, user_id, service_name
        )
        
        return SuccessResponse(
            message="Audit statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics"
        )

@router.get("/trends", response_model=SuccessResponse)
async def get_activity_trends(
    days: int = Query(30, ge=7, le=365),
    granularity: str = Query("daily", regex="^(hourly|daily|weekly)$"),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Get activity trends over time"""
    try:
        analytics_service = AnalyticsService(db)
        trends = await analytics_service.get_activity_trends(days, granularity)
        
        return SuccessResponse(
            message="Activity trends retrieved successfully",
            data=trends
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity trends"
        )

@router.get("/compliance/report", response_model=SuccessResponse)
async def get_compliance_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    compliance_tag: Optional[str] = Query(None),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Generate compliance report for audit purposes"""
    try:
        # Validate date range
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )
        
        analytics_service = AnalyticsService(db)
        report = await analytics_service.generate_compliance_report(
            start_date, end_date, compliance_tag
        )
        
        return SuccessResponse(
            message="Compliance report generated successfully",
            data=report
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )

@router.get("/anomalies", response_model=SuccessResponse)
async def detect_anomalies(
    hours: int = Query(24, ge=1, le=168),
    threshold: float = Query(2.0, ge=1.0, le=5.0),
    current_service = Depends(require_admin_or_system),
    db: Session = Depends(get_db)
):
    """Detect anomalous activity patterns"""
    try:
        analytics_service = AnalyticsService(db)
        anomalies = await analytics_service.detect_anomalies(hours, threshold)
        
        return SuccessResponse(
            message="Anomaly detection completed",
            data=anomalies
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect anomalies"
        )
