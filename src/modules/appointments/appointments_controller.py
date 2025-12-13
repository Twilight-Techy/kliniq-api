# src/modules/appointments/appointments_controller.py
"""Appointments controller with API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import appointments_service as service
from .schemas import (
    AppointmentResponse, AppointmentListResponse, AppointmentActionResponse,
    AppointmentCreateRequest, AppointmentUpdateRequest, 
    AppointmentRescheduleRequest, AppointmentCancelRequest,
    AppointmentRequestCreate, AppointmentRequestListResponse, AppointmentRequestActionResponse,
    LinkedHospitalsResponse
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ============================================================================
# APPOINTMENT REQUESTS ENDPOINTS (must come before /{appointment_id} routes)
# ============================================================================

@router.get("/requests", response_model=AppointmentRequestListResponse)
async def get_appointment_requests(
    status: Optional[str] = Query(None, description="Filter by status: all, pending, approved, rejected"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get patient's appointment requests."""
    return await service.get_appointment_requests(db, current_user, status)


@router.post("/requests", response_model=AppointmentRequestActionResponse, status_code=201)
async def create_appointment_request(
    request: AppointmentRequestCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Submit a new appointment request."""
    result = await service.create_appointment_request(db, current_user, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.delete("/requests/{request_id}", response_model=AppointmentRequestActionResponse)
async def cancel_appointment_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending appointment request."""
    result = await service.cancel_appointment_request(db, current_user, request_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.get("/linked-hospitals", response_model=LinkedHospitalsResponse)
async def get_linked_hospitals(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get patient's linked hospitals with their departments."""
    return await service.get_linked_hospitals_with_departments(db, current_user)


# ============================================================================
# MAIN APPOINTMENTS ENDPOINTS
# ============================================================================

@router.get("", response_model=AppointmentListResponse)
async def get_appointments(
    status: Optional[str] = Query(None, description="Filter by status: all, upcoming, completed, cancelled"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get patient's appointments with optional status filter."""
    return await service.get_patient_appointments(db, current_user, status, page, per_page)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get a single appointment by ID."""
    appointment = await service.get_appointment_by_id(db, current_user, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.post("", response_model=AppointmentActionResponse, status_code=201)
async def create_appointment(
    request: AppointmentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Create/book a new appointment."""
    result = await service.create_appointment(db, current_user, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.put("/{appointment_id}", response_model=AppointmentActionResponse)
async def update_appointment(
    appointment_id: UUID,
    request: AppointmentUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update appointment details (notes, type)."""
    result = await service.update_appointment(db, current_user, appointment_id, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.put("/{appointment_id}/reschedule", response_model=AppointmentActionResponse)
async def reschedule_appointment(
    appointment_id: UUID,
    request: AppointmentRescheduleRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Reschedule an appointment to a new date/time."""
    result = await service.reschedule_appointment(db, current_user, appointment_id, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.delete("/{appointment_id}", response_model=AppointmentActionResponse)
async def cancel_appointment(
    appointment_id: UUID,
    request: Optional[AppointmentCancelRequest] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Cancel an appointment."""
    reason = request.cancellation_reason if request else None
    result = await service.cancel_appointment(db, current_user, appointment_id, reason)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result
