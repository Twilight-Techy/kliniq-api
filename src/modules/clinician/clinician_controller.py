# src/modules/clinician/clinician_controller.py
"""Clinician controller with API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import clinician_service as service
from .schemas import ClinicianDashboardResponse, PatientsListResponse


router = APIRouter(prefix="/clinician", tags=["Clinician"])


@router.get("", response_model=ClinicianDashboardResponse)
async def get_clinician_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get main clinician dashboard data including:
    - Stats (pending triage/queries, reviewed today, etc.)
    - Triage cases (for nurses) or escalated queries (for doctors)
    - Points summary and breakdown
    - Recent activity
    """
    try:
        return await service.get_clinician_dashboard(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients", response_model=PatientsListResponse)
async def get_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get list of patients with active triage cases.
    
    Returns patients who have pending, in-review, or escalated triage cases,
    including their demographics, latest triage info, and urgency level.
    """
    try:
        return await service.get_patients(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}", response_model=service.PatientDetailResponse)
async def get_patient_detail(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive patient detail for clinician view.
    
    Returns complete patient information including:
    - Demographics and medical background
    - Latest triage case with AI-generated analysis
    - Vital signs
    - Medical notes and history
    - Pending queries with AI draft responses
    """
    try:
        return await service.get_patient_detail(db, current_user, patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# APPOINTMENT REQUESTS
# =============================================================================

@router.get("/requests", response_model=service.AppointmentRequestsResponse)
async def get_appointment_requests(
    status: str = "pending",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get appointment requests for nurse review."""
    try:
        return await service.get_appointment_requests(db, current_user, status)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/requests/{request_id}/approve")
async def approve_appointment_request(
    request_id: str,
    data: service.ApproveRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve appointment request and schedule appointment."""
    try:
        await service.approve_appointment_request(db, current_user, request_id, data)
        return {"message": "Appointment request approved and scheduled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/reject")
async def reject_appointment_request(
    request_id: str,
    data: service.RejectRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Reject appointment request with reason."""
    try:
        await service.reject_appointment_request(db, current_user, request_id, data)
        return {"message": "Appointment request rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# SIDEBAR COUNTS
# =============================================================================

@router.get("/counts", response_model=service.SidebarCountsResponse)
async def get_sidebar_counts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get badge counts for sidebar navigation."""
    try:
        return await service.get_sidebar_counts(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# =============================================================================
# DOCTORS LIST
# =============================================================================

@router.get("/doctors/{hospital_id}")
async def get_doctors_by_hospital(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get list of doctors for a specific hospital for appointment scheduling."""
    try:
        return await service.get_doctors_by_hospital(db, hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

