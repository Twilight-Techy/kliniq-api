# src/modules/clinician/clinician_service.py
"""Clinician service with business logic for nurse/doctor dashboards."""

from typing import Optional, List
from datetime import datetime, date, timedelta
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import (
    User, Clinician, Patient, TriageCase, EscalatedQuery, ClinicianPoints,
    ClinicianRoleType, TriageStatus, TriageUrgency, EscalatedQueryStatus,
    PreferredLanguage, Appointment, HealthVitals, MedicalHistory, MedicalHistoryType,
    AppointmentRequest, RequestStatus, UrgencyLevel, AppointmentType, AppointmentStatus, Hospital,
    ClinicianStatus
)
from src.common.llm.llm_service import LLMService
from .schemas import (
    ClinicianDashboardResponse, ClinicianStat, TriageCaseResponse,
    EscalatedQueryResponse, PointsSummary, PointsBreakdown, RecentActivity,
    PatientListItem, PatientsListResponse,
    PatientDetailResponse, PatientDemographics, TriageDetail, VitalSigns,
    MedicalNoteResponse, PendingQueryResponse, HistoryItemResponse,
    AppointmentRequestItem, AppointmentRequestsResponse,
    ApproveRequestBody, RejectRequestBody, SidebarCountsResponse, DoctorListItem
)


def _format_relative_time(dt) -> str:
    """Format datetime or date as relative time string."""
    if not dt:
        return "Unknown"
    
    # Convert date to datetime if needed
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    
    now = datetime.now(dt.tzinfo) if hasattr(dt, 'tzinfo') and dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins} min{'s' if mins != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def _urgency_to_str(urgency: TriageUrgency) -> str:
    """Convert urgency enum to string."""
    return urgency.value if urgency else "medium"


def _language_to_str(lang: PreferredLanguage) -> str:
    """Convert language enum to string."""
    if not lang:
        return "English"
    return lang.value.capitalize()


async def get_clinician_dashboard(
    session: AsyncSession,
    user: User
) -> ClinicianDashboardResponse:
    """Get main dashboard data for clinician (nurse or doctor)."""
    
    # Get clinician record
    clinician_result = await session.execute(
        select(Clinician)
        .options(selectinload(Clinician.hospital))
        .where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    is_nurse = clinician.role_type == ClinicianRoleType.NURSE
    role = "nurse" if is_nurse else "doctor"
    hospital_name = clinician.hospital.name if clinician.hospital else None
    clinician_name = f"{user.first_name} {user.last_name}"
    
    # Get stats based on role
    if is_nurse:
        stats = await _get_nurse_stats(session, clinician)
        triage_cases = await _get_triage_cases(session, clinician)
        escalated_queries = None
    else:
        stats = await _get_doctor_stats(session, clinician)
        triage_cases = None
        escalated_queries = await _get_escalated_queries(session, clinician)
    
    # Get points summary
    points = await _get_points_summary(session, clinician)
    
    # Get recent activity
    recent_activity = await _get_recent_activity(session, clinician)
    
    return ClinicianDashboardResponse(
        clinician_name=clinician_name,
        role=role,
        hospital_name=hospital_name,
        stats=stats,
        triage_cases=triage_cases,
        escalated_queries=escalated_queries,
        points=points,
        recent_activity=recent_activity
    )


async def _get_nurse_stats(
    session: AsyncSession,
    clinician: Clinician
) -> List[ClinicianStat]:
    """Get stats for nurse dashboard."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Pending triage cases (for the hospital)
    pending_query = select(func.count(TriageCase.id)).where(
        and_(
            TriageCase.status == TriageStatus.PENDING,
            # Match hospital via patient-hospital link if needed
        )
    )
    pending_result = await session.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    # Reviewed today by this clinician
    reviewed_today_query = select(func.count(TriageCase.id)).where(
        and_(
            TriageCase.reviewed_by == clinician.id,
            func.date(TriageCase.updated_at) == today
        )
    )
    reviewed_result = await session.execute(reviewed_today_query)
    reviewed_today = reviewed_result.scalar() or 0
    
    # Reviewed yesterday for comparison
    reviewed_yesterday_query = select(func.count(TriageCase.id)).where(
        and_(
            TriageCase.reviewed_by == clinician.id,
            func.date(TriageCase.updated_at) == yesterday
        )
    )
    reviewed_yesterday_result = await session.execute(reviewed_yesterday_query)
    reviewed_yesterday = reviewed_yesterday_result.scalar() or 0
    
    # Escalated cases
    escalated_query = select(func.count(TriageCase.id)).where(
        TriageCase.status == TriageStatus.ESCALATED
    )
    escalated_result = await session.execute(escalated_query)
    escalated_count = escalated_result.scalar() or 0
    
    # Urgent pending
    urgent_query = select(func.count(TriageCase.id)).where(
        and_(
            TriageCase.status == TriageStatus.PENDING,
            TriageCase.urgency == TriageUrgency.HIGH
        )
    )
    urgent_result = await session.execute(urgent_query)
    urgent_count = urgent_result.scalar() or 0
    
    return [
        ClinicianStat(
            label="Pending Triage",
            value=pending_count,
            trend=f"{urgent_count} urgent" if urgent_count > 0 else "No urgent"
        ),
        ClinicianStat(
            label="Reviewed Today",
            value=reviewed_today,
            trend=f"+{reviewed_today - reviewed_yesterday} from yesterday" if reviewed_today >= reviewed_yesterday else f"{reviewed_today - reviewed_yesterday} from yesterday"
        ),
        ClinicianStat(
            label="Escalated",
            value=escalated_count,
            trend=f"{urgent_count} urgent"
        ),
        ClinicianStat(
            label="Avg Response",
            value="8m",  # Would need more data to calculate
            trend="Good performance"
        ),
    ]


async def _get_doctor_stats(
    session: AsyncSession,
    clinician: Clinician
) -> List[ClinicianStat]:
    """Get stats for doctor dashboard."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Pending queries for this doctor
    pending_query = select(func.count(EscalatedQuery.id)).where(
        and_(
            EscalatedQuery.status == EscalatedQueryStatus.PENDING,
        )
    )
    pending_result = await session.execute(pending_query)
    pending_count = pending_result.scalar() or 0
    
    # Answered today
    answered_today_query = select(func.count(EscalatedQuery.id)).where(
        and_(
            EscalatedQuery.answered_by == clinician.id,
            func.date(EscalatedQuery.answered_at) == today
        )
    )
    answered_result = await session.execute(answered_today_query)
    answered_today = answered_result.scalar() or 0
    
    # Answered yesterday
    answered_yesterday_query = select(func.count(EscalatedQuery.id)).where(
        and_(
            EscalatedQuery.answered_by == clinician.id,
            func.date(EscalatedQuery.answered_at) == yesterday
        )
    )
    answered_yesterday_result = await session.execute(answered_yesterday_query)
    answered_yesterday = answered_yesterday_result.scalar() or 0
    
    # Urgent pending
    urgent_query = select(func.count(EscalatedQuery.id)).where(
        and_(
            EscalatedQuery.status == EscalatedQueryStatus.PENDING,
            EscalatedQuery.urgency == TriageUrgency.HIGH
        )
    )
    urgent_result = await session.execute(urgent_query)
    urgent_count = urgent_result.scalar() or 0
    
    return [
        ClinicianStat(
            label="Pending Queries",
            value=pending_count,
            trend=f"+{pending_count} today" if pending_count > 0 else "None pending"
        ),
        ClinicianStat(
            label="Answered Today",
            value=answered_today,
            trend=f"+{answered_today - answered_yesterday} from yesterday" if answered_today >= answered_yesterday else f"{answered_today - answered_yesterday} from yesterday"
        ),
        ClinicianStat(
            label="Urgent Cases",
            value=urgent_count,
            trend="Action needed" if urgent_count > 0 else "All clear"
        ),
        ClinicianStat(
            label="Avg Response",
            value="12m",
            trend="Good performance"
        ),
    ]


async def _get_triage_cases(
    session: AsyncSession,
    clinician: Clinician,
    limit: int = 20
) -> List[TriageCaseResponse]:
    """Get triage cases for nurse dashboard."""
    query = (
        select(TriageCase)
        .options(selectinload(TriageCase.patient).selectinload(Patient.user))
        .where(
            TriageCase.status.in_([TriageStatus.PENDING, TriageStatus.IN_REVIEW])
        )
        .order_by(
            # Urgent first, then by created_at desc
            desc(TriageCase.urgency == TriageUrgency.HIGH),
            desc(TriageCase.created_at)
        )
        .limit(limit)
    )
    
    result = await session.execute(query)
    cases = result.scalars().all()
    
    response = []
    for case in cases:
        patient = case.patient
        user = patient.user if patient else None
        patient_name = f"{user.first_name} {user.last_name}" if user else "Unknown"
        patient_id = f"KLQ-{str(patient.id)[:4].upper()}" if patient else "Unknown"
        
        response.append(TriageCaseResponse(
            id=str(case.id),
            patient_name=patient_name,
            patient_id=patient_id,
            symptoms=case.symptoms or "",
            duration=case.duration,
            urgency=_urgency_to_str(case.urgency),
            language=_language_to_str(case.language),
            submitted_at=_format_relative_time(case.created_at),
            status=case.status.value if case.status else "pending",
            ai_summary=case.ai_summary
        ))
    
    return response


async def _get_escalated_queries(
    session: AsyncSession,
    clinician: Clinician,
    limit: int = 20
) -> List[EscalatedQueryResponse]:
    """Get escalated queries for doctor dashboard."""
    query = (
        select(EscalatedQuery)
        .options(selectinload(EscalatedQuery.patient).selectinload(Patient.user))
        .where(
            EscalatedQuery.status == EscalatedQueryStatus.PENDING
        )
        .order_by(
            desc(EscalatedQuery.urgency == TriageUrgency.HIGH),
            desc(EscalatedQuery.created_at)
        )
        .limit(limit)
    )
    
    result = await session.execute(query)
    queries = result.scalars().all()
    
    response = []
    for q in queries:
        patient = q.patient
        user = patient.user if patient else None
        patient_name = f"{user.first_name} {user.last_name}" if user else "Unknown"
        patient_id = f"KLQ-{str(patient.id)[:4].upper()}" if patient else "Unknown"
        
        response.append(EscalatedQueryResponse(
            id=str(q.id),
            patient_name=patient_name,
            patient_id=patient_id,
            question=q.question or "",
            nurse_note=q.nurse_note,
            urgency=_urgency_to_str(q.urgency),
            submitted_at=_format_relative_time(q.created_at),
            status=q.status.value if q.status else "pending",
            ai_draft=q.ai_draft
        ))
    
    return response


async def _get_points_summary(
    session: AsyncSession,
    clinician: Clinician
) -> PointsSummary:
    """Get points summary for clinician."""
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # This month total
    this_month_query = select(func.coalesce(func.sum(ClinicianPoints.points), 0)).where(
        and_(
            ClinicianPoints.clinician_id == clinician.id,
            ClinicianPoints.month == current_month
        )
    )
    this_month_result = await session.execute(this_month_query)
    this_month_total = this_month_result.scalar() or 0
    
    # Last month total
    last_month_query = select(func.coalesce(func.sum(ClinicianPoints.points), 0)).where(
        and_(
            ClinicianPoints.clinician_id == clinician.id,
            ClinicianPoints.month == last_month
        )
    )
    last_month_result = await session.execute(last_month_query)
    last_month_total = last_month_result.scalar() or 0
    
    # Breakdown by action for current month
    breakdown_query = (
        select(
            ClinicianPoints.action,
            func.sum(ClinicianPoints.points).label("total_points"),
            func.count(ClinicianPoints.id).label("count")
        )
        .where(
            and_(
                ClinicianPoints.clinician_id == clinician.id,
                ClinicianPoints.month == current_month
            )
        )
        .group_by(ClinicianPoints.action)
    )
    breakdown_result = await session.execute(breakdown_query)
    breakdown_rows = breakdown_result.all()
    
    breakdown = [
        PointsBreakdown(
            action=row.action,
            points=int(row.total_points),
            count=int(row.count)
        )
        for row in breakdown_rows
    ]
    
    # Default breakdown if empty
    if not breakdown:
        breakdown = [
            PointsBreakdown(action="Triage Verifications", points=0, count=0),
            PointsBreakdown(action="Query Responses", points=0, count=0),
            PointsBreakdown(action="Note Updates", points=0, count=0),
        ]
    
    return PointsSummary(
        current=clinician.total_points or 0,
        goal=500,  # Default goal
        this_month=int(this_month_total),
        last_month=int(last_month_total),
        breakdown=breakdown
    )


async def _get_recent_activity(
    session: AsyncSession,
    clinician: Clinician,
    limit: int = 5
) -> List[RecentActivity]:
    """Get recent activity for clinician."""
    # Get recent points entries as activity
    query = (
        select(ClinicianPoints)
        .where(ClinicianPoints.clinician_id == clinician.id)
        .order_by(desc(ClinicianPoints.created_at))
        .limit(limit)
    )
    
    result = await session.execute(query)
    points_history = result.scalars().all()
    
    activities = []
    for entry in points_history:
        activities.append(RecentActivity(
            action=entry.description or entry.action,
            time=_format_relative_time(entry.created_at),
            points=f"+{entry.points}"
        ))
    
    # If no activity, show placeholder
    if not activities:
        activities = [
            RecentActivity(action="No recent activity", time="", points="")
        ]
    
    return activities


# =============================================================================
# PATIENTS LIST
# =============================================================================

async def get_patients(
    session: AsyncSession,
    user: User
) -> PatientsListResponse:
    """Get list of patients with active triage cases for clinician view."""
    
    # Get clinician record
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    # Query patients who have active triage cases
    # Group by patient to get their latest triage case
    query = (
        select(Patient, TriageCase, User)
        .join(User, Patient.user_id == User.id)
        .join(TriageCase, TriageCase.patient_id == Patient.id)
        .where(
            TriageCase.status.in_([
                TriageStatus.PENDING,
                TriageStatus.IN_REVIEW,
                TriageStatus.ESCALATED
            ])
        )
        .order_by(
            Patient.id,
            desc(TriageCase.created_at)
        )
    )
    
    result = await session.execute(query)
    rows = result.all()
    
    # Deduplicate by patient and keep only the latest triage case
    patients_dict = {}
    for patient, triage, user_obj in rows:
        if patient.id not in patients_dict:
            patients_dict[patient.id] = (patient, triage, user_obj)
    
    # Get most recent appointment for each patient (for last_visit calculation)
    patient_list = []
    for patient, triage, user_obj in patients_dict.values():
        # Get most recent appointment for this patient
        appt_query = (
            select(Appointment)
            .where(Appointment.patient_id == patient.id)
            .order_by(desc(Appointment.scheduled_date))
            .limit(1)
        )
        appt_result = await session.execute(appt_query)
        recent_appt = appt_result.scalar_one_or_none()
        
        # Calculate age from date_of_birth
        age = 0
        if patient.date_of_birth:
            today = date.today()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )
        
        # Get initials for avatar
        initials = ""
        if user_obj.first_name and user_obj.last_name:
            initials = f"{user_obj.first_name[0]}{user_obj.last_name[0]}".upper()
        
        # Determine last visit
        last_visit = "Never"
        if recent_appt:
            last_visit = _format_relative_time(recent_appt.scheduled_date)
        elif triage:
            last_visit = _format_relative_time(triage.created_at)
        
        # Determine status based on triage status
        status_map = {
            TriageStatus.PENDING: "pending",
            TriageStatus.IN_REVIEW: "active",
            TriageStatus.ESCALATED: "active",
            TriageStatus.RESOLVED: "completed"
        }
        status = status_map.get(triage.status, "active")
        
        # Get condition from symptoms (truncate if too long)
        condition = triage.symptoms[:50] + "..." if len(triage.symptoms) > 50 else triage.symptoms
        
        patient_list.append(PatientListItem(
            id=str(patient.id),
            name=f"{user_obj.first_name} {user_obj.last_name}",
            patient_id=f"KLQ-{str(patient.id)[:4].upper()}",
            age=age,
            gender=patient.gender or "Unknown",
            last_visit=last_visit,
            status=status,
            urgency=_urgency_to_str(triage.urgency),
            condition=condition,
            avatar=initials
        ))
    
    return PatientsListResponse(
        patients=patient_list,
        total=len(patient_list)
    )


# =============================================================================
# PATIENT DETAIL
# =============================================================================

def _calculate_age(date_of_birth: date) -> int:
    """Calculate age from date of birth."""
    if not date_of_birth:
        return 0
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


async def _generate_ai_analysis(
    session: AsyncSession,
    triage: TriageCase,
    patient: Patient
) -> tuple[str, str]:
    """Generate AI analysis for triage case if missing."""
    if triage.ai_summary and triage.ai_summary.strip():
        # Already has AI analysis
        return triage.ai_summary, triage.nurse_notes or ""
    
    try:
        # Call N-ATLaS for AI analysis
        llm = LLMService()
        
        # Build patient context
        patient_context = f"""
Patient Age: {_calculate_age(patient.date_of_birth)} years
Gender: {patient.gender}
Blood Type: {patient.blood_type or 'Unknown'}
Allergies: {patient.allergies or 'None reported'}
"""
        
        result = await llm.triage_symptoms(
            symptoms=triage.symptoms,
            language=_language_to_str(triage.language),
            additional_info=f"Duration: {triage.duration}. {patient_context}"
        )
        
        # Extract assessment as AI summary
        ai_summary = result.get("assessment", "AI analysis unavailable")
        
        # Generate recommendation
        recommendation_prompt = f"""Based on these symptoms and assessment, provide specific recommendations for the healthcare team:

Symptoms: {triage.symptoms}
Assessment: {ai_summary}

Provide 3-4 specific clinical recommendations."""
        
        recommendation_result = await llm.chat(
            user_message=recommendation_prompt,
            context="triage",
            language="english",
            temperature=0.3
        )
        
        # Update triage with AI analysis
        triage.ai_summary = ai_summary
        await session.commit()
        
        return ai_summary, recommendation_result
        
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        return "AI analysis temporarily unavailable", "Please assess based on clinical judgment"


async def get_patient_detail(
    session: AsyncSession,
    user: User,
    patient_id: str
) -> PatientDetailResponse:
    """Get comprehensive patient detail for clinician view."""
    
    # Verify clinician
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    # Parse patient_id - accept either full UUID or KLQ-xxxx format
    try:
        patient_uuid = UUID(patient_id)
    except:
        # If not a valid UUID, might be patient record ID - query by id converted to UUID
        raise ValueError(f"Invalid patient ID format: {patient_id}")
    
    # Fetch patient with user data
    patient_query = (
        select(Patient, User)
        .join(User, Patient.user_id == User.id)
        .where(Patient.id == patient_uuid)
    )
    result = await session.execute(patient_query)
    row = result.first()
    
    if not row:
        raise ValueError(f"Patient not found: {patient_id}")
    
    patient, patient_user = row
    
    # Build demographics
    age = _calculate_age(patient.date_of_birth)
    initials = ""
    if patient_user.first_name and patient_user.last_name:
        initials = f"{patient_user.first_name[0]}{patient_user.last_name[0]}".upper()
    
    location = f"{patient.city}, {patient.state}" if patient.city and patient.state else patient.city or patient.state or "Unknown"
    
    # Determine when patient was linked
    linked_since = "Unknown"
    if hasattr(patient_user, 'created_at') and patient_user.created_at:
        linked_since = patient_user.created_at.strftime("%B %Y")
    elif patient.onboarding_completed:
        linked_since = "Recently"
    
    demographics = PatientDemographics(
        id=str(patient.id),
        patient_id=f"KLQ-{str(patient.id)[:4].upper()}",
        name=f"{patient_user.first_name} {patient_user.last_name}",
        age=age,
        gender=patient.gender or "Unknown",
        phone=patient_user.phone or "Not provided",
        location=location,
        language=_language_to_str(patient.preferred_language),
        linked_since=linked_since,
        avatar=initials,
        blood_type=patient.blood_type,
        allergies=patient.allergies
    )
    
    # Get latest active triage case
    triage_detail = None
    triage_query = (
        select(TriageCase)
        .where(
            and_(
                TriageCase.patient_id == patient.id,
                TriageCase.status.in_([
                    TriageStatus.PENDING,
                    TriageStatus.IN_REVIEW,
                    TriageStatus.ESCALATED
                ])
            )
        )
        .order_by(desc(TriageCase.created_at))
        .limit(1)
    )
    triage_result = await session.execute(triage_query)
    triage = triage_result.scalar_one_or_none()
    
    if triage:
        # Generate AI analysis if missing
        ai_summary, ai_recommendation = await _generate_ai_analysis(session, triage, patient)
        
        # Get latest vital signs
        vital_signs = None
        vitals_query = (
            select(HealthVitals)
            .where(HealthVitals.patient_id == patient.id)
            .order_by(desc(HealthVitals.recorded_at))
            .limit(1)
        )
        vitals_result = await session.execute(vitals_query)
        latest_vitals = vitals_result.scalar_one_or_none()
        
        if latest_vitals:
            bp_str = None
            if latest_vitals.blood_pressure_systolic and latest_vitals.blood_pressure_diastolic:
                bp_str = f"{latest_vitals.blood_pressure_systolic}/{latest_vitals.blood_pressure_diastolic} mmHg"
            
            vital_signs = VitalSigns(
                temperature=f"{latest_vitals.temperature}°C" if latest_vitals.temperature else None,
                blood_pressure=bp_str,
                heart_rate=f"{latest_vitals.heart_rate} bpm" if latest_vitals.heart_rate else None,
                oxygen_level=f"{latest_vitals.oxygen_saturation}%" if latest_vitals.oxygen_saturation else None,
                recorded_at=_format_relative_time(latest_vitals.recorded_at)
            )
        
        triage_detail = TriageDetail(
            id=str(triage.id),
            symptoms=triage.symptoms,
            duration=triage.duration,
            urgency=_urgency_to_str(triage.urgency),
            submitted_at=_format_relative_time(triage.created_at),
            status=triage.status.value if triage.status else "pending",
            vital_signs=vital_signs,
            ai_summary=ai_summary,
            ai_recommendation=ai_recommendation
        )
    
    # Get medical history (as medical notes)
    medical_notes = []
    notes_query = (
        select(MedicalHistory, User)
        .join(User, MedicalHistory.clinician_id == User.id, isouter=True)
        .where(MedicalHistory.patient_id == patient.id)
        .order_by(desc(MedicalHistory.date))
        .limit(10)
    )
    notes_result = await session.execute(notes_query)
    
    for history, clinician_user in notes_result:
        doctor_name = f"Dr. {clinician_user.first_name} {clinician_user.last_name}" if clinician_user else "Unknown"
        
        # Parse description for medications and lifestyle
        medications = []
        lifestyle = []
        
        if history.type == MedicalHistoryType.PRESCRIPTION:
            medications = [history.title]
        
        medical_notes.append(MedicalNoteResponse(
            id=str(history.id),
            date=history.date.strftime("%b %d, %Y"),
            diagnosis=history.title if history.type == MedicalHistoryType.DIAGNOSIS else "See description",
            medications=medications,
            lifestyle=lifestyle,
            follow_up=None,
            doctor=doctor_name
        ))
    
    # Get pending queries
    pending_queries = []
    queries_query = (
        select(EscalatedQuery)
        .where(
            and_(
                EscalatedQuery.patient_id == patient.id,
                EscalatedQuery.status == EscalatedQueryStatus.PENDING
            )
        )
        .order_by(desc(EscalatedQuery.created_at))
        .limit(5)
    )
    queries_result = await session.execute(queries_query)
    
    for query in queries_result.scalars():
        pending_queries.append(PendingQueryResponse(
            id=str(query.id),
            question=query.question,
            submitted_at=_format_relative_time(query.created_at),
            ai_draft=query.ai_draft,
            nurse_note=query.nurse_note,
            status=query.status.value if query.status else "pending"
        ))
    
    # Get medical history timeline
    history_items = []
    history_query = (
        select(MedicalHistory, User)
        .join(User, MedicalHistory.clinician_id == User.id, isouter=True)
        .where(MedicalHistory.patient_id == patient.id)
        .order_by(desc(MedicalHistory.date))
        .limit(20)
    )
    history_result = await session.execute(history_query)
    
    type_map = {
        MedicalHistoryType.DIAGNOSIS: "diagnosis",
        MedicalHistoryType.PRESCRIPTION: "prescription",
        MedicalHistoryType.TEST: "test",
        MedicalHistoryType.CONSULTATION: "consultation"
    }
    
    for history, clinician_user in history_result:
        doctor_name = f"Dr. {clinician_user.first_name} {clinician_user.last_name}" if clinician_user else "Unknown"
        
        history_items.append(HistoryItemResponse(
            id=str(history.id),
            type=type_map.get(history.type, "consultation"),
            title=history.title,
            doctor=doctor_name,
            date=history.date.strftime("%b %d, %Y"),
            description=history.description or "",
            status=history.status
        ))
    
    return PatientDetailResponse(
        patient=demographics,
        triage=triage_detail,
        medical_notes=medical_notes,
        pending_queries=pending_queries,
        history=history_items
    )

# =============================================================================
# APPOINTMENT REQUESTS
# =============================================================================

async def get_appointment_requests(
    session: AsyncSession,
    user: User,
    status_filter: Optional[str] = None
) ->  AppointmentRequestsResponse:
    """Get appointment requests for nurse review."""
    
    # Verify clinician (nurse)
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    # Build query
    query = (
        select(AppointmentRequest, Patient, User, Hospital)
        .join(Patient, AppointmentRequest.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .join(Hospital, AppointmentRequest.hospital_id == Hospital.id)
    )
    
    # Apply status filter
    if status_filter and status_filter.upper() in ["PENDING", "APPROVED", "REJECTED"]:
        query = query.where(AppointmentRequest.status == RequestStatus[status_filter.upper()])
    else:
        # Default to pending
        query = query.where(AppointmentRequest.status == RequestStatus.PENDING)
    
    query = query.order_by(desc(AppointmentRequest.created_at))
    
    result = await session.execute(query)
    rows = result.all()
    
    requests_list = []
    pending_count = 0
    urgent_count = 0
    
    for request, patient, patient_user, hospital in rows:
        # Calculate age
        age = _calculate_age(patient.date_of_birth)
        
        # Map urgency to string
        urgency_map = {
            UrgencyLevel.LOW: "low",
            UrgencyLevel.NORMAL: "normal",
            UrgencyLevel.URGENT: "urgent"
        }
        urgency_str = urgency_map.get(request.urgency, "normal")
        
        # Map preferred type to string
        type_map = {
            AppointmentType.IN_PERSON: "in-person",
            AppointmentType.VIDEO: "video"
        }
        type_str = type_map.get(request.preferred_type, "in-person")
        
        # Map status to string
        status_str = request.status.value.lower() if request.status else "pending"
        
        # Count pending and urgent
        if request.status == RequestStatus.PENDING:
            pending_count += 1
            if request.urgency == UrgencyLevel.URGENT:
                urgent_count += 1
        
        requests_list.append(AppointmentRequestItem(
            id=str(request.id),
            patient_name=f"{patient_user.first_name} {patient_user.last_name}",
            patient_age=age,
            patient_phone=patient_user.phone or "Not provided",
            patient_email=patient_user.email,
            hospital=hospital.name,
            hospital_id=request.hospital_id,
            department=request.department,
            reason=request.reason,
            preferred_type=type_str,
            urgency=urgency_str,
            status=status_str,
            submitted_at=_format_relative_time(request.created_at) if request.created_at else "N/A",
            submitted_date=request.created_at.strftime("%b %d, %Y") if request.created_at else "N/A"
        ))
    
    return AppointmentRequestsResponse(
        requests=requests_list,
        total=len(requests_list),
        pending=pending_count,
        urgent=urgent_count
    )


async def approve_appointment_request(
    session: AsyncSession,
    user: User,
    request_id: str,
    data: ApproveRequestBody
) -> None:
    """Approve appointment request and create scheduled appointment."""
    
    # Verify clinician
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    # Get the request
    request_result = await session.execute(
        select(AppointmentRequest).where(AppointmentRequest.id == UUID(request_id))
    )
    appointment_request = request_result.scalar_one_or_none()
    if not appointment_request:
        raise ValueError(f"Appointment request not found: {request_id}")
    
    # Verify request is still pending
    if appointment_request.status != RequestStatus.PENDING:
        raise ValueError(f"Request is already {appointment_request.status.value}")
    
    # Create appointment - data.scheduled_date and data.scheduled_time are already date/time objects
    new_appointment = Appointment(
        patient_id=appointment_request.patient_id,
        clinician_id=data.clinician_id,
        hospital_id=appointment_request.hospital_id,
        request_id=appointment_request.id,
        scheduled_date=data.scheduled_date,
        scheduled_time=data.scheduled_time,
        duration_minutes=30,
        type=appointment_request.preferred_type,
        status=AppointmentStatus.UPCOMING,
        notes=f"Scheduled from request. Reason: {appointment_request.reason}"
    )
    session.add(new_appointment)
    
    # Update request status
    appointment_request.status = RequestStatus.APPROVED
    appointment_request.reviewed_by = clinician.id
    appointment_request.reviewed_at = datetime.now()
    
    await session.commit()


async def reject_appointment_request(
    session: AsyncSession,
    user: User,
    request_id: str,
    data: RejectRequestBody
) -> None:
    """Reject appointment request with reason."""
    
    # Verify clinician
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    # Get the request
    request_result = await session.execute(
        select(AppointmentRequest).where(AppointmentRequest.id == UUID(request_id))
    )
    appointment_request = request_result.scalar_one_or_none()
    if not appointment_request:
        raise ValueError(f"Appointment request not found: {request_id}")
    
    # Verify request is still pending
    if appointment_request.status != RequestStatus.PENDING:
        raise ValueError(f"Request is already {appointment_request.status.value}")
    
    # Update request
    appointment_request.status = RequestStatus.REJECTED
    appointment_request.rejection_reason = data.rejection_reason
    appointment_request.reviewed_by = clinician.id
    appointment_request.reviewed_at = datetime.now()
    
    await session.commit()
# =============================================================================
# SIDEBAR COUNTS
# =============================================================================

async def get_sidebar_counts(
    session: AsyncSession,
    user: User
) -> SidebarCountsResponse:
    """Get badge counts for sidebar navigation."""
    
    # Verify clinician
    clinician_result = await session.execute(
        select(Clinician).where(Clinician.user_id == user.id)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise ValueError("Clinician profile not found")
    
    is_nurse = clinician.role_type == ClinicianRoleType.NURSE
    
    # Count active patients (those with pending/in-review/escalated triage cases)
    patients_query = (
        select(func.count(func.distinct(Patient.id)))
        .select_from(TriageCase)
        .join(Patient, TriageCase.patient_id == Patient.id)
        .where(
            TriageCase.status.in_([
                TriageStatus.PENDING,
                TriageStatus.IN_REVIEW,
                TriageStatus.ESCALATED
            ])
        )
    )
    patients_result = await session.execute(patients_query)
    patients_count = patients_result.scalar() or 0
    
    # Count pending appointment requests (nurses only)
    requests_count = 0
    if is_nurse:
        requests_query = (
            select(func.count(AppointmentRequest.id))
            .where(AppointmentRequest.status == RequestStatus.PENDING)
        )
        requests_result = await session.execute(requests_query)
        requests_count = requests_result.scalar() or 0
    
    # Count pending escalated queries (doctors only)
    pending_queries_count = 0
    if not is_nurse:
        queries_query = (
            select(func.count(EscalatedQuery.id))
            .where(EscalatedQuery.status == EscalatedQueryStatus.PENDING)
        )
        queries_result = await session.execute(queries_query)
        pending_queries_count = queries_result.scalar() or 0
    
    return SidebarCountsResponse(
        patients_count=patients_count,
        requests_count=requests_count,
        pending_queries_count=pending_queries_count
    )
# =============================================================================
# DOCTORS LIST
# =============================================================================

async def get_doctors_by_hospital(
    session: AsyncSession,
    hospital_id: str
) -> List[DoctorListItem]:
    """Get list of doctors for a specific hospital."""
    
    # Query doctors (clinicians with role_type=DOCTOR) at the given hospital
    result = await session.execute(
        select(Clinician, User)
        .join(User, Clinician.user_id == User.id)
        .where(
            and_(
                Clinician.hospital_id == UUID(hospital_id),
                Clinician.role_type == ClinicianRoleType.DOCTOR,
                Clinician.status == ClinicianStatus.ACTIVE
            )
        )
        .order_by(User.first_name, User.last_name)
    )
    
    doctors = []
    for clinician, user in result.all():
        full_name = f"{user.first_name} {user.last_name}".strip()
        # Specialty can be derived from clinician bio or set as generic
        specialty = "General Practice"  # Default, could enhance later with specialty field
        
        doctors.append(DoctorListItem(
            id=clinician.id,
            full_name=full_name,
            specialty=specialty
        ))
    
    return doctors
