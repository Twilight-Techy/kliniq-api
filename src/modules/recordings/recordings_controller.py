# src/modules/recordings/recordings_controller.py
"""Recordings controller with API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import recordings_service as service
from .schemas import (
    RecordingResponse, RecordingListResponse, RecordingActionResponse,
    RecordingCreateRequest, RecordingUploadRequest,
    UpcomingAppointmentsListResponse
)

router = APIRouter(prefix="/recordings", tags=["Recordings"])


# ============================================================================
# APPOINTMENT SELECTION (must come before /{recording_id})
# ============================================================================

@router.get("/appointments", response_model=UpcomingAppointmentsListResponse)
async def get_upcoming_appointments(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get upcoming and in-progress appointments for recording selection."""
    return await service.get_upcoming_appointments(db, current_user)


# ============================================================================
# RECORDINGS ENDPOINTS
# ============================================================================

@router.get("", response_model=RecordingListResponse)
async def get_recordings(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get all recordings for the current patient."""
    return await service.get_patient_recordings(db, current_user)


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get a single recording by ID."""
    recording = await service.get_recording_by_id(db, current_user, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording


@router.post("", response_model=RecordingActionResponse, status_code=201)
async def create_recording(
    request: RecordingCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new recording entry."""
    result = await service.create_recording(db, current_user, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.put("/{recording_id}/upload", response_model=RecordingActionResponse)
async def upload_recording(
    recording_id: UUID,
    request: RecordingUploadRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update recording with file URL after upload."""
    result = await service.update_recording_url(db, current_user, recording_id, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.delete("/{recording_id}", response_model=RecordingActionResponse)
async def delete_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a recording."""
    result = await service.delete_recording(db, current_user, recording_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result
