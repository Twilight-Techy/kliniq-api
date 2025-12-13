# src/modules/settings/settings_controller.py
"""Settings controller with API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import settings_service as service
from .schemas import SettingsResponse, UpdateSettingsRequest, SettingsActionResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get current patient settings."""
    return await service.get_patient_settings(db, current_user)


@router.put("", response_model=SettingsActionResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update patient settings."""
    result = await service.update_patient_settings(db, current_user, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result
