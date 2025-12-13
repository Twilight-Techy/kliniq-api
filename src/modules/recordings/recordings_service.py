# src/modules/recordings/recordings_service.py
"""Service layer for recordings business logic."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import (
    User, Patient, Recording, Appointment, Clinician, Hospital, Department,
    RecordingStatus as DBRecordingStatus, AppointmentStatus
)
from .schemas import (
    RecordingResponse, RecordingListResponse, RecordingCreateRequest,
    RecordingUploadRequest, RecordingActionResponse, RecordingStatus,
    UpcomingAppointmentResponse, UpcomingAppointmentsListResponse
)


def _convert_status(db_status: DBRecordingStatus) -> RecordingStatus:
    """Convert database enum to schema enum."""
    mapping = {
        DBRecordingStatus.PROCESSING: RecordingStatus.PROCESSING,
        DBRecordingStatus.COMPLETED: RecordingStatus.COMPLETED,
        DBRecordingStatus.FAILED: RecordingStatus.FAILED,
    }
    return mapping.get(db_status, RecordingStatus.PROCESSING)


def _build_recording_response(recording: Recording) -> RecordingResponse:
    """Build RecordingResponse from database model."""
    doctor_name = None
    specialty = None
    
    if recording.appointment and recording.appointment.clinician:
        clinician = recording.appointment.clinician
        if clinician.user:
            doctor_name = f"Dr. {clinician.user.first_name} {clinician.user.last_name}"
        specialty = clinician.specialty
    elif recording.clinician and recording.clinician.user:
        doctor_name = f"Dr. {recording.clinician.user.first_name} {recording.clinician.user.last_name}"
        specialty = recording.clinician.specialty
    
    return RecordingResponse(
        id=str(recording.id),
        title=recording.title,
        appointment_id=str(recording.appointment_id) if recording.appointment_id else None,
        doctor_name=doctor_name,
        specialty=specialty,
        duration_seconds=recording.duration_seconds or 0,
        file_size_bytes=recording.file_size_bytes,
        file_url=recording.file_url,
        transcript=recording.transcript,
        status=_convert_status(recording.status),
        created_at=recording.created_at,
    )


async def get_patient_recordings(
    session: AsyncSession,
    user: User
) -> RecordingListResponse:
    """Get all recordings for the current patient."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return RecordingListResponse(recordings=[], total=0)
    
    # Query recordings with related data
    query = (
        select(Recording)
        .options(
            selectinload(Recording.appointment).selectinload(Appointment.clinician).selectinload(Clinician.user),
            selectinload(Recording.clinician).selectinload(Clinician.user),
        )
        .where(Recording.patient_id == patient.id)
        .order_by(Recording.created_at.desc())
    )
    
    result = await session.execute(query)
    recordings = result.scalars().all()
    
    recording_responses = [_build_recording_response(r) for r in recordings]
    
    return RecordingListResponse(
        recordings=recording_responses,
        total=len(recording_responses)
    )


async def get_recording_by_id(
    session: AsyncSession,
    user: User,
    recording_id: UUID
) -> Optional[RecordingResponse]:
    """Get a single recording by ID."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return None
    
    query = (
        select(Recording)
        .options(
            selectinload(Recording.appointment).selectinload(Appointment.clinician).selectinload(Clinician.user),
            selectinload(Recording.clinician).selectinload(Clinician.user),
        )
        .where(and_(Recording.id == recording_id, Recording.patient_id == patient.id))
    )
    
    result = await session.execute(query)
    recording = result.scalar_one_or_none()
    
    if not recording:
        return None
    
    return _build_recording_response(recording)


async def create_recording(
    session: AsyncSession,
    user: User,
    request: RecordingCreateRequest
) -> RecordingActionResponse:
    """Create a new recording entry."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return RecordingActionResponse(success=False, message="Patient not found")
    
    # Validate appointment if provided
    clinician_id = None
    if request.appointment_id:
        appt_result = await session.execute(
            select(Appointment)
            .options(selectinload(Appointment.clinician).selectinload(Clinician.user))
            .where(and_(
                Appointment.id == UUID(request.appointment_id),
                Appointment.patient_id == patient.id
            ))
        )
        appointment = appt_result.scalar_one_or_none()
        if not appointment:
            return RecordingActionResponse(success=False, message="Appointment not found")
        clinician_id = appointment.clinician_id
    
    # Create recording
    recording = Recording(
        patient_id=patient.id,
        appointment_id=UUID(request.appointment_id) if request.appointment_id else None,
        clinician_id=clinician_id,
        title=request.title,
        duration_seconds=request.duration_seconds,
        status=DBRecordingStatus.PROCESSING,
    )
    
    session.add(recording)
    await session.commit()
    await session.refresh(recording)
    
    # Reload with relationships
    query = (
        select(Recording)
        .options(
            selectinload(Recording.appointment).selectinload(Appointment.clinician).selectinload(Clinician.user),
            selectinload(Recording.clinician).selectinload(Clinician.user),
        )
        .where(Recording.id == recording.id)
    )
    result = await session.execute(query)
    recording = result.scalar_one()
    
    return RecordingActionResponse(
        success=True,
        message="Recording created successfully",
        recording=_build_recording_response(recording)
    )


async def update_recording_url(
    session: AsyncSession,
    user: User,
    recording_id: UUID,
    request: RecordingUploadRequest
) -> RecordingActionResponse:
    """Update recording with file URL after upload."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return RecordingActionResponse(success=False, message="Patient not found")
    
    # Get recording
    recording_result = await session.execute(
        select(Recording).where(and_(
            Recording.id == recording_id,
            Recording.patient_id == patient.id
        ))
    )
    recording = recording_result.scalar_one_or_none()
    
    if not recording:
        return RecordingActionResponse(success=False, message="Recording not found")
    
    # Update recording
    recording.file_url = request.file_url
    if request.file_size_bytes:
        recording.file_size_bytes = request.file_size_bytes
    if request.duration_seconds:
        recording.duration_seconds = request.duration_seconds
    recording.status = DBRecordingStatus.COMPLETED
    
    await session.commit()
    
    # Reload with relationships
    query = (
        select(Recording)
        .options(
            selectinload(Recording.appointment).selectinload(Appointment.clinician).selectinload(Clinician.user),
            selectinload(Recording.clinician).selectinload(Clinician.user),
        )
        .where(Recording.id == recording.id)
    )
    result = await session.execute(query)
    recording = result.scalar_one()
    
    return RecordingActionResponse(
        success=True,
        message="Recording updated successfully",
        recording=_build_recording_response(recording)
    )


async def delete_recording(
    session: AsyncSession,
    user: User,
    recording_id: UUID
) -> RecordingActionResponse:
    """Delete a recording."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return RecordingActionResponse(success=False, message="Patient not found")
    
    # Get recording
    recording_result = await session.execute(
        select(Recording).where(and_(
            Recording.id == recording_id,
            Recording.patient_id == patient.id
        ))
    )
    recording = recording_result.scalar_one_or_none()
    
    if not recording:
        return RecordingActionResponse(success=False, message="Recording not found")
    
    await session.delete(recording)
    await session.commit()
    
    return RecordingActionResponse(
        success=True,
        message="Recording deleted successfully"
    )


async def get_upcoming_appointments(
    session: AsyncSession,
    user: User
) -> UpcomingAppointmentsListResponse:
    """Get upcoming and in-progress appointments for recording selection."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return UpcomingAppointmentsListResponse(appointments=[])
    
    # Query upcoming and in-progress appointments
    query = (
        select(Appointment)
        .options(
            selectinload(Appointment.clinician).selectinload(Clinician.user),
            selectinload(Appointment.hospital),
            selectinload(Appointment.department),
        )
        .where(and_(
            Appointment.patient_id == patient.id,
            or_(
                Appointment.status == AppointmentStatus.UPCOMING,
                Appointment.status == AppointmentStatus.IN_PROGRESS
            )
        ))
        .order_by(Appointment.scheduled_date, Appointment.scheduled_time)
    )
    
    result = await session.execute(query)
    appointments = result.scalars().all()
    
    appointment_responses = []
    for appt in appointments:
        doctor_name = "Unknown Doctor"
        specialty = "General"
        
        if appt.clinician and appt.clinician.user:
            doctor_name = f"Dr. {appt.clinician.user.first_name} {appt.clinician.user.last_name}"
            specialty = appt.clinician.specialty or "General"
        
        hospital_name = appt.hospital.name if appt.hospital else "Unknown Hospital"
        
        appointment_responses.append(UpcomingAppointmentResponse(
            id=str(appt.id),
            doctor_name=doctor_name,
            specialty=specialty,
            hospital_name=hospital_name,
            scheduled_date=appt.scheduled_date.isoformat(),
            scheduled_time=appt.scheduled_time.strftime("%H:%M"),
            type=appt.type.value,
            status=appt.status.value,
        ))
    
    return UpcomingAppointmentsListResponse(appointments=appointment_responses)
