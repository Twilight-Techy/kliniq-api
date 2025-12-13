# src/modules/appointments/appointments_service.py
"""Appointments service for business logic."""

from typing import Optional, List
from datetime import date, time
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import (
    User, Patient, Clinician, Hospital, Department, PatientHospital,
    Appointment, AppointmentStatus as DBAppointmentStatus, AppointmentType as DBAppointmentType,
    AppointmentRequest, RequestStatus as DBRequestStatus, UrgencyLevel as DBUrgencyLevel
)
from .schemas import (
    AppointmentResponse, AppointmentListResponse, AppointmentActionResponse,
    AppointmentCreateRequest, AppointmentUpdateRequest, AppointmentRescheduleRequest,
    AppointmentType, AppointmentStatus,
    AppointmentRequestCreate, AppointmentRequestResponse, AppointmentRequestListResponse,
    AppointmentRequestActionResponse, UrgencyLevel, RequestStatus,
    LinkedHospitalWithDepartments, LinkedHospitalsResponse, DepartmentInfo
)


def _convert_status(db_status: DBAppointmentStatus) -> AppointmentStatus:
    """Convert database status to schema status."""
    mapping = {
        DBAppointmentStatus.UPCOMING: AppointmentStatus.UPCOMING,
        DBAppointmentStatus.COMPLETED: AppointmentStatus.COMPLETED,
        DBAppointmentStatus.CANCELLED: AppointmentStatus.CANCELLED,
        DBAppointmentStatus.IN_PROGRESS: AppointmentStatus.IN_PROGRESS,
    }
    return mapping.get(db_status, AppointmentStatus.UPCOMING)


def _convert_type(db_type: DBAppointmentType) -> AppointmentType:
    """Convert database type to schema type."""
    if db_type == DBAppointmentType.VIDEO:
        return AppointmentType.VIDEO
    return AppointmentType.IN_PERSON


async def _build_appointment_response(
    session: AsyncSession,
    appointment: Appointment
) -> AppointmentResponse:
    """Build appointment response with clinician and hospital info."""
    # Get clinician info
    doctor_name = "Unknown"
    specialty = None
    if appointment.clinician_id:
        clinician_result = await session.execute(
            select(Clinician, User)
            .join(User, Clinician.user_id == User.id)
            .where(Clinician.id == appointment.clinician_id)
        )
        clinician_data = clinician_result.first()
        if clinician_data:
            clinician, user = clinician_data
            doctor_name = f"Dr. {user.first_name} {user.last_name}"
            specialty = clinician.specialty
    
    # Get hospital info
    hospital_name = None
    if appointment.hospital_id:
        hospital_result = await session.execute(
            select(Hospital).where(Hospital.id == appointment.hospital_id)
        )
        hospital = hospital_result.scalar_one_or_none()
        if hospital:
            hospital_name = hospital.name
    
    return AppointmentResponse(
        id=appointment.id,
        doctor_name=doctor_name,
        specialty=specialty,
        hospital_name=hospital_name,
        location=appointment.location,
        scheduled_date=appointment.scheduled_date,
        scheduled_time=appointment.scheduled_time.strftime("%I:%M %p") if appointment.scheduled_time else "",
        duration_minutes=appointment.duration_minutes,
        type=_convert_type(appointment.type),
        status=_convert_status(appointment.status),
        notes=appointment.notes,
        cancellation_reason=appointment.cancellation_reason,
        created_at=appointment.created_at
    )


async def get_patient_appointments(
    session: AsyncSession,
    user: User,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> AppointmentListResponse:
    """Get patient's appointments with optional status filter."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentListResponse(appointments=[], total=0, page=page, per_page=per_page)
    
    # Build query
    query = select(Appointment).where(Appointment.patient_id == patient.id)
    
    # Apply status filter
    if status and status != "all":
        status_map = {
            "upcoming": DBAppointmentStatus.UPCOMING,
            "completed": DBAppointmentStatus.COMPLETED,
            "cancelled": DBAppointmentStatus.CANCELLED,
        }
        if status in status_map:
            query = query.where(Appointment.status == status_map[status])
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply ordering and pagination
    query = query.order_by(desc(Appointment.scheduled_date), desc(Appointment.scheduled_time))
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await session.execute(query)
    appointments = result.scalars().all()
    
    # Build responses
    appointment_responses = []
    for apt in appointments:
        response = await _build_appointment_response(session, apt)
        appointment_responses.append(response)
    
    return AppointmentListResponse(
        appointments=appointment_responses,
        total=total,
        page=page,
        per_page=per_page
    )


async def get_appointment_by_id(
    session: AsyncSession,
    user: User,
    appointment_id: UUID
) -> Optional[AppointmentResponse]:
    """Get a single appointment by ID."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return None
    
    # Get appointment
    result = await session.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.patient_id == patient.id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        return None
    
    return await _build_appointment_response(session, appointment)


async def create_appointment(
    session: AsyncSession,
    user: User,
    request: AppointmentCreateRequest
) -> AppointmentActionResponse:
    """Create a new appointment."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentActionResponse(success=False, message="Patient profile not found")
    
    # Convert type
    db_type = DBAppointmentType.VIDEO if request.type == AppointmentType.VIDEO else DBAppointmentType.IN_PERSON
    
    # Get hospital location if provided
    location = None
    if request.hospital_id:
        hospital_result = await session.execute(
            select(Hospital).where(Hospital.id == request.hospital_id)
        )
        hospital = hospital_result.scalar_one_or_none()
        if hospital:
            location = f"{hospital.name}, {hospital.city}"
    
    # Create appointment
    appointment = Appointment(
        patient_id=patient.id,
        clinician_id=request.clinician_id,
        hospital_id=request.hospital_id,
        department_id=request.department_id,
        scheduled_date=request.scheduled_date,
        scheduled_time=request.scheduled_time,
        duration_minutes=request.duration_minutes,
        type=db_type,
        status=DBAppointmentStatus.UPCOMING,
        location=location,
        notes=request.notes
    )
    session.add(appointment)
    await session.flush()
    await session.refresh(appointment)
    
    response = await _build_appointment_response(session, appointment)
    await session.commit()
    
    return AppointmentActionResponse(
        success=True,
        message="Appointment booked successfully",
        appointment=response
    )


async def update_appointment(
    session: AsyncSession,
    user: User,
    appointment_id: UUID,
    request: AppointmentUpdateRequest
) -> AppointmentActionResponse:
    """Update appointment details."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentActionResponse(success=False, message="Patient profile not found")
    
    # Get appointment
    result = await session.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.patient_id == patient.id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        return AppointmentActionResponse(success=False, message="Appointment not found")
    
    # Update fields
    if request.notes is not None:
        appointment.notes = request.notes
    if request.type is not None:
        appointment.type = DBAppointmentType.VIDEO if request.type == AppointmentType.VIDEO else DBAppointmentType.IN_PERSON
    
    await session.flush()
    response = await _build_appointment_response(session, appointment)
    await session.commit()
    
    return AppointmentActionResponse(
        success=True,
        message="Appointment updated successfully",
        appointment=response
    )


async def reschedule_appointment(
    session: AsyncSession,
    user: User,
    appointment_id: UUID,
    request: AppointmentRescheduleRequest
) -> AppointmentActionResponse:
    """Reschedule an appointment."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentActionResponse(success=False, message="Patient profile not found")
    
    # Get appointment
    result = await session.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.patient_id == patient.id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        return AppointmentActionResponse(success=False, message="Appointment not found")
    
    if appointment.status == DBAppointmentStatus.CANCELLED:
        return AppointmentActionResponse(success=False, message="Cannot reschedule a cancelled appointment")
    
    if appointment.status == DBAppointmentStatus.COMPLETED:
        return AppointmentActionResponse(success=False, message="Cannot reschedule a completed appointment")
    
    # Update date and time
    appointment.scheduled_date = request.scheduled_date
    appointment.scheduled_time = request.scheduled_time
    
    await session.flush()
    response = await _build_appointment_response(session, appointment)
    await session.commit()
    
    return AppointmentActionResponse(
        success=True,
        message="Appointment rescheduled successfully",
        appointment=response
    )


async def cancel_appointment(
    session: AsyncSession,
    user: User,
    appointment_id: UUID,
    reason: Optional[str] = None
) -> AppointmentActionResponse:
    """Cancel an appointment."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentActionResponse(success=False, message="Patient profile not found")
    
    # Get appointment
    result = await session.execute(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.patient_id == patient.id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        return AppointmentActionResponse(success=False, message="Appointment not found")
    
    if appointment.status == DBAppointmentStatus.CANCELLED:
        return AppointmentActionResponse(success=False, message="Appointment is already cancelled")
    
    if appointment.status == DBAppointmentStatus.COMPLETED:
        return AppointmentActionResponse(success=False, message="Cannot cancel a completed appointment")
    
    # Cancel appointment
    appointment.status = DBAppointmentStatus.CANCELLED
    appointment.cancellation_reason = reason
    
    await session.flush()
    response = await _build_appointment_response(session, appointment)
    await session.commit()
    
    return AppointmentActionResponse(
        success=True,
        message="Appointment cancelled successfully",
        appointment=response
    )


# ============================================================================
# APPOINTMENT REQUEST FUNCTIONS
# ============================================================================

def _convert_urgency(db_urgency: DBUrgencyLevel) -> UrgencyLevel:
    """Convert database urgency to schema urgency."""
    mapping = {
        DBUrgencyLevel.LOW: UrgencyLevel.LOW,
        DBUrgencyLevel.NORMAL: UrgencyLevel.NORMAL,
        DBUrgencyLevel.URGENT: UrgencyLevel.URGENT,
    }
    return mapping.get(db_urgency, UrgencyLevel.NORMAL)


def _convert_request_status(db_status: DBRequestStatus) -> RequestStatus:
    """Convert database request status to schema status."""
    mapping = {
        DBRequestStatus.PENDING: RequestStatus.PENDING,
        DBRequestStatus.APPROVED: RequestStatus.APPROVED,
        DBRequestStatus.REJECTED: RequestStatus.REJECTED,
    }
    return mapping.get(db_status, RequestStatus.PENDING)


async def _build_request_response(
    session: AsyncSession,
    request: AppointmentRequest
) -> AppointmentRequestResponse:
    """Build appointment request response with hospital info."""
    # Get hospital name
    hospital_name = "Unknown"
    if request.hospital_id:
        hospital_result = await session.execute(
            select(Hospital).where(Hospital.id == request.hospital_id)
        )
        hospital = hospital_result.scalar_one_or_none()
        if hospital:
            hospital_name = hospital.name
    
    return AppointmentRequestResponse(
        id=request.id,
        hospital_id=request.hospital_id,
        hospital_name=hospital_name,
        department=request.department,
        reason=request.reason,
        preferred_type=_convert_type(request.preferred_type),
        urgency=_convert_urgency(request.urgency),
        status=_convert_request_status(request.status),
        rejection_reason=request.rejection_reason,
        created_at=request.created_at
    )


async def get_appointment_requests(
    session: AsyncSession,
    user: User,
    status: Optional[str] = None
) -> AppointmentRequestListResponse:
    """Get patient's appointment requests."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentRequestListResponse(requests=[], total=0)
    
    # Build query
    query = select(AppointmentRequest).where(AppointmentRequest.patient_id == patient.id)
    
    # Apply status filter
    if status and status != "all":
        status_map = {
            "pending": DBRequestStatus.PENDING,
            "approved": DBRequestStatus.APPROVED,
            "rejected": DBRequestStatus.REJECTED,
        }
        if status in status_map:
            query = query.where(AppointmentRequest.status == status_map[status])
    
    query = query.order_by(desc(AppointmentRequest.created_at))
    
    result = await session.execute(query)
    requests = result.scalars().all()
    
    # Build responses
    request_responses = []
    for req in requests:
        response = await _build_request_response(session, req)
        request_responses.append(response)
    
    return AppointmentRequestListResponse(
        requests=request_responses,
        total=len(request_responses)
    )


async def create_appointment_request(
    session: AsyncSession,
    user: User,
    request: AppointmentRequestCreate
) -> AppointmentRequestActionResponse:
    """Create a new appointment request."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentRequestActionResponse(success=False, message="Patient profile not found")
    
    # Verify patient is linked to hospital
    link_result = await session.execute(
        select(PatientHospital)
        .where(PatientHospital.patient_id == patient.id)
        .where(PatientHospital.hospital_id == request.hospital_id)
    )
    link = link_result.scalar_one_or_none()
    if not link:
        return AppointmentRequestActionResponse(success=False, message="You must be linked to this hospital to request an appointment")
    
    # Convert types
    db_type = DBAppointmentType.VIDEO if request.preferred_type == AppointmentType.VIDEO else DBAppointmentType.IN_PERSON
    urgency_map = {
        UrgencyLevel.LOW: DBUrgencyLevel.LOW,
        UrgencyLevel.NORMAL: DBUrgencyLevel.NORMAL,
        UrgencyLevel.URGENT: DBUrgencyLevel.URGENT,
    }
    db_urgency = urgency_map.get(request.urgency, DBUrgencyLevel.NORMAL)
    
    # Create request
    apt_request = AppointmentRequest(
        patient_id=patient.id,
        hospital_id=request.hospital_id,
        department=request.department,
        reason=request.reason,
        preferred_type=db_type,
        urgency=db_urgency,
        status=DBRequestStatus.PENDING
    )
    session.add(apt_request)
    await session.flush()
    await session.refresh(apt_request)
    
    response = await _build_request_response(session, apt_request)
    await session.commit()
    
    return AppointmentRequestActionResponse(
        success=True,
        message="Appointment request submitted successfully",
        request=response
    )


async def cancel_appointment_request(
    session: AsyncSession,
    user: User,
    request_id: UUID
) -> AppointmentRequestActionResponse:
    """Cancel a pending appointment request."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return AppointmentRequestActionResponse(success=False, message="Patient profile not found")
    
    # Get request
    result = await session.execute(
        select(AppointmentRequest)
        .where(AppointmentRequest.id == request_id)
        .where(AppointmentRequest.patient_id == patient.id)
    )
    apt_request = result.scalar_one_or_none()
    if not apt_request:
        return AppointmentRequestActionResponse(success=False, message="Request not found")
    
    if apt_request.status != DBRequestStatus.PENDING:
        return AppointmentRequestActionResponse(success=False, message="Only pending requests can be cancelled")
    
    # Delete the request
    await session.delete(apt_request)
    await session.commit()
    
    return AppointmentRequestActionResponse(
        success=True,
        message="Appointment request cancelled successfully"
    )


# ============================================================================
# LINKED HOSPITALS WITH DEPARTMENTS
# ============================================================================

async def get_linked_hospitals_with_departments(
    session: AsyncSession,
    user: User
) -> LinkedHospitalsResponse:
    """Get patient's linked hospitals with their departments."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return LinkedHospitalsResponse(hospitals=[])
    
    # Get linked hospitals
    links_result = await session.execute(
        select(PatientHospital, Hospital)
        .join(Hospital, PatientHospital.hospital_id == Hospital.id)
        .where(PatientHospital.patient_id == patient.id)
        .where(Hospital.is_active == True)
    )
    hospital_links = links_result.all()
    
    # Build responses with departments
    hospitals = []
    for link, hospital in hospital_links:
        # Get departments for this hospital
        dept_result = await session.execute(
            select(Department)
            .where(Department.hospital_id == hospital.id)
            .where(Department.is_active == True)
        )
        departments = [
            DepartmentInfo(id=d.id, name=d.name)
            for d in dept_result.scalars().all()
        ]
        
        hospitals.append(LinkedHospitalWithDepartments(
            id=hospital.id,
            name=hospital.name,
            city=hospital.city,
            departments=departments
        ))
    
    return LinkedHospitalsResponse(hospitals=hospitals)
