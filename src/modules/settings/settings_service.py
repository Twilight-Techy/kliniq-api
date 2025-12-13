# src/modules/settings/settings_service.py
"""Service layer for settings business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, Patient, PreferredLanguage
from .schemas import (
    SettingsResponse, UpdateSettingsRequest, SettingsActionResponse,
    NotificationSettings
)


def _get_language_code(lang: PreferredLanguage) -> str:
    """Convert PreferredLanguage enum to language code."""
    mapping = {
        PreferredLanguage.ENGLISH: "en",
        PreferredLanguage.YORUBA: "yo",
        PreferredLanguage.IGBO: "ig",
        PreferredLanguage.HAUSA: "ha",
    }
    return mapping.get(lang, "en")


def _get_language_enum(code: str) -> PreferredLanguage:
    """Convert language code to PreferredLanguage enum."""
    mapping = {
        "en": PreferredLanguage.ENGLISH,
        "yo": PreferredLanguage.YORUBA,
        "ig": PreferredLanguage.IGBO,
        "ha": PreferredLanguage.HAUSA,
    }
    return mapping.get(code, PreferredLanguage.ENGLISH)


def _build_settings_response(patient: Patient) -> SettingsResponse:
    """Build SettingsResponse from patient model."""
    # Get notification settings with defaults
    notif_settings = patient.notification_settings or {}
    
    return SettingsResponse(
        preferred_language=_get_language_code(patient.preferred_language) if patient.preferred_language else "en",
        notification_settings=NotificationSettings(
            appointments=notif_settings.get("appointments", True),
            messages=notif_settings.get("messages", True),
            reminders=notif_settings.get("reminders", True),
            updates=notif_settings.get("updates", False),
        )
    )


async def get_patient_settings(
    session: AsyncSession,
    user: User
) -> SettingsResponse:
    """Get current patient settings."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        # Return defaults
        return SettingsResponse(
            preferred_language="en",
            notification_settings=NotificationSettings()
        )
    
    return _build_settings_response(patient)


async def update_patient_settings(
    session: AsyncSession,
    user: User,
    request: UpdateSettingsRequest
) -> SettingsActionResponse:
    """Update patient settings."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return SettingsActionResponse(
            success=False,
            message="Patient not found"
        )
    
    # Update language if provided
    if request.preferred_language is not None:
        patient.preferred_language = _get_language_enum(request.preferred_language)
    
    # Update notification settings if provided
    if request.notification_settings is not None:
        patient.notification_settings = {
            "appointments": request.notification_settings.appointments,
            "messages": request.notification_settings.messages,
            "reminders": request.notification_settings.reminders,
            "updates": request.notification_settings.updates,
        }
    
    await session.commit()
    await session.refresh(patient)
    
    return SettingsActionResponse(
        success=True,
        message="Settings updated successfully",
        settings=_build_settings_response(patient)
    )
