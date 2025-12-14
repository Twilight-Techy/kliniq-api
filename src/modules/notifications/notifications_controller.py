# Notifications Controller

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import notifications_service as service
from .schemas import (
    NotificationResponse,
    NotificationsListResponse,
    MarkReadRequest,
    MarkReadResponse
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsListResponse)
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications."""
    notifications, unread_count = await service.get_user_notifications(
        db, current_user, limit, unread_only
    )
    
    return NotificationsListResponse(
        notifications=[
            NotificationResponse(
                id=str(n.id),
                title=n.title,
                message=n.message,
                type=n.type.value if n.type else None,
                is_read=n.is_read,
                reference_id=str(n.reference_id) if n.reference_id else None,
                reference_type=n.reference_type,
                created_at=n.created_at
            )
            for n in notifications
        ],
        unread_count=unread_count
    )


@router.post("/mark-read", response_model=MarkReadResponse)
async def mark_read(
    request: MarkReadRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Mark specific notifications as read."""
    count = await service.mark_notifications_read(db, current_user, request.notification_ids)
    return MarkReadResponse(success=True, marked_count=count)


@router.post("/mark-all-read", response_model=MarkReadResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(db, current_user)
    return MarkReadResponse(success=True, marked_count=count)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    deleted = await service.delete_notification(db, current_user, notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}
