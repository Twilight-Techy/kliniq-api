# Notifications Service

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Notification, NotificationType, User


async def get_user_notifications(
    db: AsyncSession,
    user: User,
    limit: int = 20,
    unread_only: bool = False
) -> tuple[List[Notification], int]:
    """Get notifications for a user with unread count."""
    
    # Base query
    query = select(Notification).where(Notification.user_id == user.id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    query = query.order_by(desc(Notification.created_at)).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # Get unread count
    count_query = select(func.count(Notification.id)).where(
        Notification.user_id == user.id,
        Notification.is_read == False
    )
    count_result = await db.execute(count_query)
    unread_count = count_result.scalar() or 0
    
    return list(notifications), unread_count


async def mark_notifications_read(
    db: AsyncSession,
    user: User,
    notification_ids: List[str]
) -> int:
    """Mark notifications as read. Returns count of updated notifications."""
    
    uuids = [UUID(id) for id in notification_ids]
    
    stmt = (
        update(Notification)
        .where(
            Notification.id.in_(uuids),
            Notification.user_id == user.id
        )
        .values(is_read=True)
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount


async def mark_all_read(db: AsyncSession, user: User) -> int:
    """Mark all notifications as read for a user."""
    
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.is_read == False
        )
        .values(is_read=True)
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: Optional[NotificationType] = None,
    reference_id: Optional[UUID] = None,
    reference_type: Optional[str] = None
) -> Notification:
    """Create a new notification."""
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        reference_id=reference_id,
        reference_type=reference_type
    )
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return notification


async def delete_notification(db: AsyncSession, user: User, notification_id: str) -> bool:
    """Delete a notification. Returns True if deleted."""
    
    query = select(Notification).where(
        Notification.id == UUID(notification_id),
        Notification.user_id == user.id
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()
    
    if notification:
        await db.delete(notification)
        await db.commit()
        return True
    
    return False
