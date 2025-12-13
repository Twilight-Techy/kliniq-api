# src/modules/settings/schemas.py
"""Pydantic schemas for settings module."""

from typing import Optional
from pydantic import BaseModel


class NotificationSettings(BaseModel):
    appointments: bool = True
    messages: bool = True
    reminders: bool = True
    updates: bool = False


class SettingsResponse(BaseModel):
    preferred_language: Optional[str] = None
    notification_settings: NotificationSettings

    class Config:
        from_attributes = True


class UpdateSettingsRequest(BaseModel):
    preferred_language: Optional[str] = None
    notification_settings: Optional[NotificationSettings] = None


class SettingsActionResponse(BaseModel):
    success: bool
    message: str
    settings: Optional[SettingsResponse] = None
