# src/modules/dashboard/schemas.py
"""Dashboard module schemas."""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class AppointmentType(str, Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"


class AppointmentStatus(str, Enum):
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in-progress"


# ============================================================================
# HOSPITAL SCHEMAS
# ============================================================================

class HospitalSummary(BaseModel):
    """Linked hospital summary for dashboard."""
    id: UUID
    hospital_code: str
    name: str
    location: str
    type: str
    departments: List[str] = []
    linked_since: datetime
    total_visits: int = 0
    rating: float = 0.0
    
    class Config:
        from_attributes = True


class HospitalSearchResult(BaseModel):
    """Hospital search result."""
    id: UUID
    hospital_code: str
    name: str
    type: str
    city: str
    state: str
    rating: float
    
    class Config:
        from_attributes = True


class HospitalSearchResponse(BaseModel):
    """Search hospitals response."""
    hospitals: List[HospitalSearchResult]
    total: int


class LinkHospitalRequest(BaseModel):
    """Link hospital request - by code or ID."""
    hospital_code: Optional[str] = None
    hospital_id: Optional[UUID] = None


class LinkHospitalResponse(BaseModel):
    """Link hospital response."""
    success: bool
    message: str
    hospital: Optional[HospitalSummary] = None


# ============================================================================
# APPOINTMENT SCHEMAS
# ============================================================================

class AppointmentSummary(BaseModel):
    """Appointment summary for dashboard."""
    id: UUID
    doctor_name: str
    specialty: Optional[str] = None
    hospital_name: str
    scheduled_date: date
    scheduled_time: str
    type: AppointmentType
    status: AppointmentStatus
    
    class Config:
        from_attributes = True


# ============================================================================
# CHAT SCHEMAS
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request from patient."""
    message: str
    chat_id: Optional[UUID] = None  # Continue existing chat or start new


class ChatResponse(BaseModel):
    """Chat response from AI."""
    chat_id: UUID
    response: str
    usage: Optional[dict] = None


class ChatHistoryResponse(BaseModel):
    """Chat history item."""
    id: UUID
    title: Optional[str] = None
    messages: List[ChatMessage]
    language: str
    created_at: datetime
    updated_at: datetime


class RecentChat(BaseModel):
    """Recent chat for dashboard sidebar."""
    id: UUID
    title: Optional[str] = None
    preview: str  # First few words of last message
    updated_at: datetime


# ============================================================================
# RECORDING SCHEMAS
# ============================================================================

class RecordingSummary(BaseModel):
    """Consultation recording summary."""
    id: UUID
    title: str
    doctor_name: str
    duration_seconds: int
    has_transcript: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# MEDICAL NOTES SCHEMAS
# ============================================================================

class DoctorNote(BaseModel):
    """Doctor's note/medical history entry."""
    id: UUID
    type: str  # consultation, prescription, test, diagnosis
    title: str
    description: Optional[str] = None
    doctor_name: str
    date: date
    
    class Config:
        from_attributes = True


# ============================================================================
# HEALTH VITALS SCHEMAS
# ============================================================================

class HealthVitalsSummary(BaseModel):
    """Latest health vitals for dashboard."""
    heart_rate: Optional[int] = None  # bpm
    blood_pressure: Optional[str] = None  # "120/80"
    temperature: Optional[float] = None  # Celsius
    weight: Optional[float] = None  # kg
    oxygen_saturation: Optional[int] = None  # SpO2 %
    recorded_at: Optional[datetime] = None


# ============================================================================
# DASHBOARD MAIN SCHEMA
# ============================================================================

class DashboardStats(BaseModel):
    """Quick stats for dashboard."""
    total_appointments: int = 0
    completed_appointments: int = 0
    linked_hospitals: int = 0
    active_chats: int = 0


class DashboardResponse(BaseModel):
    """Main dashboard data response."""
    user_name: str
    preferred_language: str
    upcoming_appointments: List[AppointmentSummary]
    linked_hospitals: List[HospitalSummary]
    recent_recordings: List[RecordingSummary] = []
    doctor_notes: List[DoctorNote] = []
    health_vitals: Optional[HealthVitalsSummary] = None
    recent_chats: List[RecentChat] = []
    stats: DashboardStats
    welcome_message: str  # Language-specific greeting

