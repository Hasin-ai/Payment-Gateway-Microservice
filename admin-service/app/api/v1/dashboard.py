from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict, Any

from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardStats, PlatformMetrics
from app.utils.auth import require_admin

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    period: str = "today",
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for specified period"""
    dashboard_service = DashboardService(db)
    try:
        stats = await dashboard_service.get_dashboard_stats(period)
        return stats
    finally:
        await dashboard_service.close()

@router.get("/metrics", response_model=PlatformMetrics)
async def get_platform_metrics(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive platform metrics"""
    dashboard_service = DashboardService(db)
    try:
        metrics = await dashboard_service.get_platform_metrics()
        return metrics
    finally:
        await dashboard_service.close()

@router.get("/alerts")
async def get_system_alerts(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get system alerts and notifications"""
    dashboard_service = DashboardService(db)
    try:
        alerts = await dashboard_service.get_system_alerts()
        return alerts
    finally:
        await dashboard_service.close()