# src/modules/clinician/schemas.py
"""Schemas for clinician dashboard responses."""

from typing import List, Optional
from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel


class ClinicianStat(BaseModel):
    """Single stat item."""
    label: str
    value: str | int
    trend: Optional[str] = None


class TriageCaseResponse(BaseModel):
    """Triage case for nurse dashboard."""
    id: str
    patient_name: str
    patient_id: str
    symptoms: str
    duration: Optional[str] = None
    urgency: str  # low, medium, high
    language: str
    submitted_at: str  # relative time
    status: str  # pending, in-review, escalated, resolved
    ai_summary: Optional[str] = None


class EscalatedQueryResponse(BaseModel):
    """Escalated query for doctor dashboard."""
    id: str
    patient_name: str
    patient_id: str
    question: str
    nurse_note: Optional[str] = None
    urgency: str  # medium, high
    submitted_at: str
    status: str  # pending, answered
    ai_draft: Optional[str] = None


class PointsBreakdown(BaseModel):
    """Points breakdown by action."""
    action: str
    points: int
    count: int


class PointsSummary(BaseModel):
    """Points summary for clinician."""
    current: int
    goal: int
    this_month: int
    last_month: int
    breakdown: List[PointsBreakdown]


class RecentActivity(BaseModel):
    """Single activity item."""
    action: str
    time: str
    points: str


class ClinicianDashboardResponse(BaseModel):
    """Main dashboard response for clinician."""
    clinician_name: str
    role: str  # nurse or doctor
    hospital_name: Optional[str] = None
    stats: List[ClinicianStat]
    triage_cases: Optional[List[TriageCaseResponse]] = None  # For nurses
    escalated_queries: Optional[List[EscalatedQueryResponse]] = None  # For doctors
    points: PointsSummary
    recent_activity: List[RecentActivity]


# =============================================================================
# PATIENTS LIST
# =============================================================================

class PatientListItem(BaseModel):
    """Patient item for clinician patients list."""
    id: str
    name: str
    patient_id: str  # KLQ-xxxx format
    age: int
    gender: str
    last_visit: str  # relative time
    status: str  # active, pending, completed
    urgency: str  # low, medium, high
    condition: str  # latest triage symptom summary
    avatar: str  # initials


class PatientsListResponse(BaseModel):
    """Response for patients list endpoint."""
    patients: List[PatientListItem]
    total: int


# =============================================================================
# PATIENT DETAIL
# =============================================================================

class PatientDemographics(BaseModel):
    """Patient demographics and basic info."""
    id: str
    patient_id: str  # KLQ-xxxx format
    name: str
    age: int
    gender: str
    phone: str
    location: str  # city, state
    language: str
    linked_since: str
    avatar: str  # initials
    blood_type: Optional[str] = None
    allergies: Optional[str] = None  # comma-separated or description


class VitalSigns(BaseModel):
    """Vital signs measurements."""
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = None  # systolic/diastolic
    heart_rate: Optional[str] = None
    oxygen_level: Optional[str] = None
    recorded_at: str


class TriageDetail(BaseModel):
    """Detailed triage information with AI analysis."""
    id: str
    symptoms: str
    duration: Optional[str] = None
    urgency: str  # low, medium, high
    submitted_at: str
    status: str
    vital_signs: Optional[VitalSigns] = None
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None


class MedicalNoteResponse(BaseModel):
    """Medical note from doctor visit."""
    id: str
    date: str
    diagnosis: str
    medications: List[str]
    lifestyle: List[str]
    follow_up: Optional[str] = None
    doctor: str


class PendingQueryResponse(BaseModel):
    """Patient query pending clinician response."""
    id: str
    question: str
    submitted_at: str
    ai_draft: Optional[str] = None
    nurse_note: Optional[str] = None
    status: str  # pending, answered


class HistoryItemResponse(BaseModel):
    """Single item in medical history."""
    id: str
    type: str  # consultation, prescription, test, diagnosis
    title: str
    doctor: str
    date: str
    description: str
    status: Optional[str] = None


class PatientDetailResponse(BaseModel):
    """Complete patient detail for clinician view."""
    patient: PatientDemographics
    triage: Optional[TriageDetail] = None
    medical_notes: List[MedicalNoteResponse]
    pending_queries: List[PendingQueryResponse]
    history: List[HistoryItemResponse]


# =============================================================================
# APPOINTMENT REQUESTS
# =============================================================================

class AppointmentRequestItem(BaseModel):
    """Individual appointment request for list view."""
    id: UUID
    patient_name: str
    patient_age: int
    patient_phone: str
    patient_email: str
    hospital: str
    hospital_id: UUID  # Added for fetching doctors
    department: str
    reason: str
    preferred_type: str
    urgency: str
    status: str
    submitted_at: str
    submitted_date: str


class AppointmentRequestsResponse(BaseModel):
    """Response for appointment requests list."""
    requests: list[AppointmentRequestItem]
    total: int
    pending: int
    urgent: int


class ApproveRequestBody(BaseModel):
    """Request body for approving appointment request."""
    clinician_id: UUID
    scheduled_date: date
    scheduled_time: time


class RejectRequestBody(BaseModel):
    """Request body for rejecting appointment request."""
    rejection_reason: str


# =============================================================================
# SIDEBAR COUNTS
# =============================================================================

class SidebarCountsResponse(BaseModel):
    """Response for sidebar navigation badge counts."""
    patients_count: int
    requests_count: int
    pending_queries_count: int


# =============================================================================
# DOCTORS LIST
# =============================================================================

class DoctorListItem(BaseModel):
    """Doctor information for appointment scheduling."""
    id: UUID
    full_name: str
    specialty: str | None
