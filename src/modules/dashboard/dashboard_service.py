# src/modules/dashboard/dashboard_service.py
"""Dashboard service for patient dashboard logic."""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
import json

from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import (
    User, Patient, Hospital, Department, PatientHospital, Clinician,
    Appointment, AppointmentStatus as DBAppointmentStatus, AppointmentType as DBAppointmentType,
    Recording, RecordingStatus, MedicalHistory, MedicalHistoryType,
    HealthVitals, TriageChat, PreferredLanguage
)
from src.common.llm import LLMService
from src.common.config import settings

from .schemas import (
    DashboardResponse, DashboardStats, AppointmentSummary,
    HospitalSummary, HospitalSearchResult, HospitalSearchResponse,
    LinkHospitalResponse, ChatMessage, ChatResponse, ChatHistoryResponse,
    AppointmentType, AppointmentStatus,
    RecordingSummary, DoctorNote, HealthVitalsSummary, RecentChat
)


# Language-specific welcome messages
WELCOME_MESSAGES = {
    "ENGLISH": "Welcome back! How can I help you today? You can ask me about your medications, previous consultations, or describe any symptoms you're experiencing.",
    "HAUSA": "Barka da zuwa! Yaya zan iya taimaka maka yau? Kuna iya tambayata game da magunguna, karatun likita na baya, ko bayyana duk wani alamun cuta da kuke fuskanta.",
    "IGBO": "Nnọọ! Kedu ka m ga-esi nyere gị aka taa? Ị nwere ike ịjụ m maka ọgwụ gị, nkwurịta ọgwụ gara aga, ma ọ bụ kọwaa ihe ọrịa ọ bụla ị na-enwe.",
    "YORUBA": "Ẹ káàbọ̀! Báwo ni mo ṣe lè ràn ọ́ lọ́wọ́ lónìí? O lè béèrè lọ́wọ́ mi nípa àwọn oògùn rẹ, ìjíròrò ìṣàwárí tí ó ti kọjá, tàbí ṣàpèjúwe àwọn àmì àrùn èyíkéyìí tí o bá ń ní."
}


async def get_dashboard_data(
    session: AsyncSession,
    user: User
) -> DashboardResponse:
    """Get main dashboard data for patient."""
    
    # Get patient profile
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise ValueError("Patient profile not found")
    
    # Get preferred language
    preferred_lang = patient.preferred_language.value if patient.preferred_language else "ENGLISH"
    
    # Get upcoming appointments
    appointments_result = await session.execute(
        select(Appointment)
        .join(Patient)
        .where(Patient.user_id == user.id)
        .where(Appointment.status == DBAppointmentStatus.UPCOMING)
        .order_by(Appointment.scheduled_date, Appointment.scheduled_time)
        .limit(5)
    )
    appointments = appointments_result.scalars().all()
    
    # Get linked hospitals
    hospital_links_result = await session.execute(
        select(PatientHospital, Hospital)
        .join(Hospital)
        .join(Patient)
        .where(Patient.user_id == user.id)
        .order_by(PatientHospital.linked_at.desc())
    )
    hospital_links = hospital_links_result.all()
    
    # Get stats
    total_appointments = await session.scalar(
        select(func.count(Appointment.id))
        .join(Patient)
        .where(Patient.user_id == user.id)
    )
    
    completed_appointments = await session.scalar(
        select(func.count(Appointment.id))
        .join(Patient)
        .where(Patient.user_id == user.id)
        .where(Appointment.status == DBAppointmentStatus.COMPLETED)
    )
    
    active_chats = await session.scalar(
        select(func.count(TriageChat.id))
        .where(TriageChat.patient_id == patient.id)
        .where(TriageChat.is_active == True)
    )
    
    # Build response
    upcoming_appointments = []
    for apt in appointments:
        # Get clinician and hospital info
        clinician_result = await session.execute(
            select(Clinician, User)
            .join(User, Clinician.user_id == User.id)
            .where(Clinician.id == apt.clinician_id)
        )
        clinician_data = clinician_result.first()
        clinician = clinician_data[0] if clinician_data else None
        clinician_user = clinician_data[1] if clinician_data else None
        
        hospital_result = await session.execute(
            select(Hospital).where(Hospital.id == apt.hospital_id)
        )
        hospital = hospital_result.scalar_one_or_none()
        
        upcoming_appointments.append(AppointmentSummary(
            id=apt.id,
            doctor_name=f"Dr. {clinician_user.first_name} {clinician_user.last_name}" if clinician_user else "Unknown",
            specialty=clinician.specialty if clinician else None,
            hospital_name=hospital.name if hospital else "Unknown",
            scheduled_date=apt.scheduled_date,
            scheduled_time=apt.scheduled_time.strftime("%I:%M %p") if apt.scheduled_time else "",
            type=AppointmentType.VIDEO if apt.type == DBAppointmentType.VIDEO else AppointmentType.IN_PERSON,
            status=AppointmentStatus.UPCOMING
        ))
    
    linked_hospitals = []
    for link, hospital in hospital_links:
        # Get departments
        dept_result = await session.execute(
            select(Department).where(Department.hospital_id == hospital.id).where(Department.is_active == True)
        )
        departments = [d.name for d in dept_result.scalars().all()]
        
        linked_hospitals.append(HospitalSummary(
            id=hospital.id,
            hospital_code=hospital.hospital_code,
            name=hospital.name,
            location=f"{hospital.city}, {hospital.state}",
            type=hospital.type.value if hospital.type else "General",
            departments=departments[:4],  # Limit to 4 departments for display
            linked_since=link.linked_at,
            total_visits=link.total_visits or 0,
            rating=float(hospital.rating) if hospital.rating else 0.0
        ))
    
    # Get recent recordings
    recordings_result = await session.execute(
        select(Recording, Clinician, User)
        .join(Clinician, Recording.clinician_id == Clinician.id, isouter=True)
        .join(User, Clinician.user_id == User.id, isouter=True)
        .where(Recording.patient_id == patient.id)
        .where(Recording.status == RecordingStatus.COMPLETED)
        .order_by(desc(Recording.created_at))
        .limit(5)
    )
    recordings = recordings_result.all()
    
    recent_recordings = [
        RecordingSummary(
            id=rec.id,
            title=rec.title,
            doctor_name=f"Dr. {u.first_name} {u.last_name}" if u else "Unknown",
            duration_seconds=rec.duration_seconds,
            has_transcript=rec.transcript is not None,
            created_at=rec.created_at
        )
        for rec, clin, u in recordings
    ]
    
    # Get doctor notes (medical history)
    notes_result = await session.execute(
        select(MedicalHistory, Clinician, User)
        .join(Clinician, MedicalHistory.clinician_id == Clinician.id, isouter=True)
        .join(User, Clinician.user_id == User.id, isouter=True)
        .where(MedicalHistory.patient_id == patient.id)
        .order_by(desc(MedicalHistory.date))
        .limit(5)
    )
    notes = notes_result.all()
    
    doctor_notes = [
        DoctorNote(
            id=note.id,
            type=note.type.value if note.type else "consultation",
            title=note.title,
            description=note.description,
            doctor_name=f"Dr. {u.first_name} {u.last_name}" if u else "Unknown",
            date=note.date
        )
        for note, clin, u in notes
    ]
    
    # Get latest health vitals
    vitals_result = await session.execute(
        select(HealthVitals)
        .where(HealthVitals.patient_id == patient.id)
        .order_by(desc(HealthVitals.recorded_at))
        .limit(1)
    )
    latest_vital = vitals_result.scalar_one_or_none()
    
    health_vitals = None
    if latest_vital:
        bp_str = None
        if latest_vital.blood_pressure_systolic and latest_vital.blood_pressure_diastolic:
            bp_str = f"{latest_vital.blood_pressure_systolic}/{latest_vital.blood_pressure_diastolic}"
        health_vitals = HealthVitalsSummary(
            heart_rate=latest_vital.heart_rate,
            blood_pressure=bp_str,
            temperature=latest_vital.temperature,
            weight=latest_vital.weight,
            oxygen_saturation=latest_vital.oxygen_saturation,
            recorded_at=latest_vital.recorded_at
        )
    
    # Get recent chats
    chats_result = await session.execute(
        select(TriageChat)
        .where(TriageChat.patient_id == patient.id)
        .order_by(desc(TriageChat.updated_at))
        .limit(5)
    )
    chats = chats_result.scalars().all()
    
    recent_chats = []
    for chat in chats:
        messages = chat.messages or []
        preview = ""
        if messages:
            last_msg = messages[-1]
            preview = last_msg.get("content", "")[:50] + ("..." if len(last_msg.get("content", "")) > 50 else "")
        recent_chats.append(RecentChat(
            id=chat.id,
            title=chat.title,
            preview=preview,
            updated_at=chat.updated_at
        ))
    
    return DashboardResponse(
        user_name=f"{user.first_name} {user.last_name}",
        preferred_language=preferred_lang.lower(),
        upcoming_appointments=upcoming_appointments,
        linked_hospitals=linked_hospitals,
        recent_recordings=recent_recordings,
        doctor_notes=doctor_notes,
        health_vitals=health_vitals,
        recent_chats=recent_chats,
        stats=DashboardStats(
            total_appointments=total_appointments or 0,
            completed_appointments=completed_appointments or 0,
            linked_hospitals=len(linked_hospitals),
            active_chats=active_chats or 0
        ),
        welcome_message=WELCOME_MESSAGES.get(preferred_lang, WELCOME_MESSAGES["ENGLISH"])
    )


async def search_hospitals(
    session: AsyncSession,
    query: str,
    limit: int = 10
) -> HospitalSearchResponse:
    """Search available hospitals by name or code."""
    
    search_term = f"%{query}%"
    
    result = await session.execute(
        select(Hospital)
        .where(Hospital.is_active == True)
        .where(
            or_(
                Hospital.name.ilike(search_term),
                Hospital.hospital_code.ilike(search_term),
                Hospital.city.ilike(search_term)
            )
        )
        .order_by(Hospital.rating.desc())
        .limit(limit)
    )
    hospitals = result.scalars().all()
    
    return HospitalSearchResponse(
        hospitals=[
            HospitalSearchResult(
                id=h.id,
                hospital_code=h.hospital_code,
                name=h.name,
                type=h.type.value if h.type else "General",
                city=h.city,
                state=h.state,
                rating=float(h.rating) if h.rating else 0.0
            )
            for h in hospitals
        ],
        total=len(hospitals)
    )


async def get_all_hospitals(
    session: AsyncSession,
    limit: int = 50
) -> HospitalSearchResponse:
    """Get all available hospitals for selection."""
    
    result = await session.execute(
        select(Hospital)
        .where(Hospital.is_active == True)
        .order_by(Hospital.name)
        .limit(limit)
    )
    hospitals = result.scalars().all()
    
    return HospitalSearchResponse(
        hospitals=[
            HospitalSearchResult(
                id=h.id,
                hospital_code=h.hospital_code,
                name=h.name,
                type=h.type.value if h.type else "General",
                city=h.city,
                state=h.state,
                rating=float(h.rating) if h.rating else 0.0
            )
            for h in hospitals
        ],
        total=len(hospitals)
    )


async def link_hospital(
    session: AsyncSession,
    user: User,
    hospital_code: Optional[str] = None,
    hospital_id: Optional[UUID] = None
) -> LinkHospitalResponse:
    """Link patient to a hospital by code or ID."""
    
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return LinkHospitalResponse(success=False, message="Patient profile not found")
    
    # Find hospital
    if hospital_code:
        hospital_result = await session.execute(
            select(Hospital)
            .where(Hospital.hospital_code == hospital_code)
            .where(Hospital.is_active == True)
        )
    elif hospital_id:
        hospital_result = await session.execute(
            select(Hospital)
            .where(Hospital.id == hospital_id)
            .where(Hospital.is_active == True)
        )
    else:
        return LinkHospitalResponse(success=False, message="Please provide hospital code or ID")
    
    hospital = hospital_result.scalar_one_or_none()
    
    if not hospital:
        return LinkHospitalResponse(success=False, message="Hospital not found")
    
    # Check if already linked
    existing_link = await session.execute(
        select(PatientHospital)
        .where(PatientHospital.patient_id == patient.id)
        .where(PatientHospital.hospital_id == hospital.id)
    )
    
    if existing_link.scalar_one_or_none():
        return LinkHospitalResponse(success=False, message="You're already linked to this hospital")
    
    # Create link
    new_link = PatientHospital(
        patient_id=patient.id,
        hospital_id=hospital.id,
        total_visits=0
    )
    session.add(new_link)
    await session.flush()
    
    # Get departments for response
    dept_result = await session.execute(
        select(Department).where(Department.hospital_id == hospital.id).where(Department.is_active == True)
    )
    departments = [d.name for d in dept_result.scalars().all()]
    
    return LinkHospitalResponse(
        success=True,
        message=f"Successfully linked to {hospital.name}",
        hospital=HospitalSummary(
            id=hospital.id,
            hospital_code=hospital.hospital_code,
            name=hospital.name,
            location=f"{hospital.city}, {hospital.state}",
            type=hospital.type.value if hospital.type else "General",
            departments=departments[:4],
            linked_since=datetime.utcnow(),
            total_visits=0,
            rating=float(hospital.rating) if hospital.rating else 0.0
        )
    )


async def unlink_hospital(
    session: AsyncSession,
    user: User,
    hospital_id: UUID
) -> dict:
    """Unlink patient from a hospital."""
    
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return {"success": False, "message": "Patient profile not found"}
    
    # Find and delete link
    link_result = await session.execute(
        select(PatientHospital)
        .where(PatientHospital.patient_id == patient.id)
        .where(PatientHospital.hospital_id == hospital_id)
    )
    link = link_result.scalar_one_or_none()
    
    if not link:
        return {"success": False, "message": "Hospital link not found"}
    
    await session.delete(link)
    
    return {"success": True, "message": "Hospital unlinked successfully"}


async def process_chat(
    session: AsyncSession,
    user: User,
    message: str,
    chat_id: Optional[UUID] = None
) -> ChatResponse:
    """Process chat message with N-ATLaS LLM."""
    
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise ValueError("Patient profile not found")
    
    # Get or create chat
    if chat_id:
        chat_result = await session.execute(
            select(TriageChat)
            .where(TriageChat.id == chat_id)
            .where(TriageChat.patient_id == patient.id)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            raise ValueError("Chat not found")
    else:
        # Create new chat with patient's preferred language
        preferred_lang = patient.preferred_language if patient.preferred_language else PreferredLanguage.ENGLISH
        chat = TriageChat(
            patient_id=patient.id,
            language=preferred_lang,
            messages=[],
            is_active=True
        )
        session.add(chat)
        await session.flush()
    
    # Add user message to history
    messages = chat.messages or []
    user_msg = {
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    messages.append(user_msg)
    
    # Call LLM
    llm = LLMService()
    
    # Build conversation for LLM
    llm_messages = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]  # Last 10 messages
    
    try:
        response = await llm.chat(
            user_message=message,
            context="general",
            language=chat.language.value.lower() if chat.language else "english",
            conversation_history=llm_messages[:-1],  # Exclude the just-added user message
        )
    except Exception as e:
        # Fallback response if LLM fails
        response = "I'm sorry, I'm having trouble processing your request right now. Please try again or contact support if the issue persists."
    
    # Add assistant response to history
    assistant_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.utcnow().isoformat()
    }
    messages.append(assistant_msg)
    
    # Update chat title if first message
    if len(messages) <= 2:
        chat.title = message[:50] + ("..." if len(message) > 50 else "")
    
    # Update chat
    chat.messages = messages
    chat.updated_at = datetime.utcnow()
    
    return ChatResponse(
        chat_id=chat.id,
        response=response,
        usage=None
    )


async def get_chat_history(
    session: AsyncSession,
    user: User,
    limit: int = 10
) -> List[ChatHistoryResponse]:
    """Get patient's chat history."""
    
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return []
    
    result = await session.execute(
        select(TriageChat)
        .where(TriageChat.patient_id == patient.id)
        .order_by(TriageChat.updated_at.desc())
        .limit(limit)
    )
    chats = result.scalars().all()
    
    return [
        ChatHistoryResponse(
            id=chat.id,
            title=chat.title,
            messages=[
                ChatMessage(
                    role=m["role"],
                    content=m["content"],
                    timestamp=datetime.fromisoformat(m["timestamp"]) if isinstance(m["timestamp"], str) else m["timestamp"]
                )
                for m in (chat.messages or [])
            ],
            language=chat.language.value.lower() if chat.language else "english",
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        for chat in chats
    ]
