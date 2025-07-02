from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationSend, NotificationResponse, NotificationStatus,
    BulkNotificationSend, NotificationStats
)
from app.utils.response import SuccessResponse
from app.utils.auth import get_current_service

router = APIRouter()

@router.post("/send", response_model=SuccessResponse[NotificationResponse])
async def send_notification(
    notification_data: NotificationSend,
    background_tasks: BackgroundTasks,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Send notification to user via specified channels"""
    try:
        notification_service = NotificationService(db)
        
        # Queue notification for processing
        result = await notification_service.send_notification(notification_data)
        
        # Process in background for immediate response
        background_tasks.add_task(
            notification_service.process_queued_notifications
        )
        
        return SuccessResponse(
            message="Notification queued successfully",
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
            detail="Failed to send notification"
        )

@router.post("/send/bulk", response_model=SuccessResponse[Dict[str, Any]])
async def send_bulk_notification(
    bulk_data: BulkNotificationSend,
    background_tasks: BackgroundTasks,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Send bulk notifications to multiple users"""
    try:
        notification_service = NotificationService(db)
        
        result = await notification_service.send_bulk_notification(bulk_data)
        
        # Process in background
        background_tasks.add_task(
            notification_service.process_queued_notifications
        )
        
        return SuccessResponse(
            message="Bulk notifications queued successfully",
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
            detail="Failed to send bulk notifications"
        )

@router.get("/status/{notification_id}", response_model=SuccessResponse[NotificationStatus])
async def get_notification_status(
    notification_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get notification delivery status"""
    try:
        notification_service = NotificationService(db)
        status_info = await notification_service.get_notification_status(notification_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return SuccessResponse(
            message="Notification status retrieved successfully",
            data=status_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification status"
        )

@router.get("/history/{user_id}", response_model=SuccessResponse[List[NotificationStatus]])
async def get_user_notification_history(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    notification_type: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get user's notification history"""
    try:
        notification_service = NotificationService(db)
        notifications, total = await notification_service.get_user_notification_history(
            user_id=user_id,
            page=page,
            size=size,
            notification_type=notification_type,
            channel=channel
        )
        
        return SuccessResponse(
            message="Notification history retrieved successfully",
            data={
                "notifications": [NotificationStatus.from_orm(n) for n in notifications],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification history"
        )

@router.get("/stats", response_model=SuccessResponse[NotificationStats])
async def get_notification_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Get notification delivery statistics"""
    try:
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        notification_service = NotificationService(db)
        stats = await notification_service.get_notification_stats(start_date, end_date)
        
        return SuccessResponse(
            message="Notification statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics"
        )

@router.post("/retry/{notification_id}", response_model=SuccessResponse)
async def retry_failed_notification(
    notification_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Retry a failed notification"""
    try:
        notification_service = NotificationService(db)
        result = await notification_service.retry_notification(notification_id)
        
        return SuccessResponse(
            message="Notification retry initiated successfully",
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
            detail="Failed to retry notification"
        )

@router.delete("/{notification_id}", response_model=SuccessResponse)
async def cancel_notification(
    notification_id: int,
    current_service = Depends(get_current_service),
    db: Session = Depends(get_db)
):
    """Cancel a queued notification"""
    try:
        notification_service = NotificationService(db)
        result = await notification_service.cancel_notification(notification_id)
        
        return SuccessResponse(
            message="Notification cancelled successfully",
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
            detail="Failed to cancel notification"
        )
