# Notifications Schemas

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class NotificationTypeEnum(str, Enum):
    APPOINTMENT = "appointment"
    PRESCRIPTION = "prescription"
    RESULT = "result"
    SYSTEM = "system"


class NotificationBase(BaseModel):
    title: str
    message: str
    type: Optional[NotificationTypeEnum] = None


class NotificationCreate(NotificationBase):
    user_id: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: Optional[str] = None
    is_read: bool
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationsListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


class MarkReadResponse(BaseModel):
    success: bool
    marked_count: int
