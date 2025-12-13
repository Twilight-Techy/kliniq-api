# src/modules/appointments/schemas.py
"""Appointments module Pydantic schemas."""

from typing import Optional, List
from datetime import date, time, datetime
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class AppointmentType(str, Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"


class AppointmentStatus(str, Enum):
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in-progress"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class AppointmentCreateRequest(BaseModel):
    """Request to create/book a new appointment."""
    clinician_id: Optional[UUID] = None
    hospital_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = Field(default=30, ge=15, le=120)
    type: AppointmentType = AppointmentType.IN_PERSON
    notes: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    """Request to update appointment details."""
    notes: Optional[str] = None
    type: Optional[AppointmentType] = None


class AppointmentRescheduleRequest(BaseModel):
    """Request to reschedule an appointment."""
    scheduled_date: date
    scheduled_time: time


class AppointmentCancelRequest(BaseModel):
    """Request to cancel an appointment."""
    cancellation_reason: Optional[str] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ClinicianInfo(BaseModel):
    """Clinician summary for appointment response."""
    id: UUID
    name: str
    specialty: Optional[str] = None


class HospitalInfo(BaseModel):
    """Hospital summary for appointment response."""
    id: UUID
    name: str
    location: str


class AppointmentResponse(BaseModel):
    """Full appointment details."""
    id: UUID
    doctor_name: str
    specialty: Optional[str] = None
    hospital_name: Optional[str] = None
    location: Optional[str] = None
    scheduled_date: date
    scheduled_time: str
    duration_minutes: int
    type: AppointmentType
    status: AppointmentStatus
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Paginated list of appointments."""
    appointments: List[AppointmentResponse]
    total: int
    page: int = 1
    per_page: int = 20


class AppointmentActionResponse(BaseModel):
    """Generic response for appointment actions."""
    success: bool
    message: str
    appointment: Optional[AppointmentResponse] = None


# ============================================================================
# APPOINTMENT REQUEST SCHEMAS
# ============================================================================

class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AppointmentRequestCreate(BaseModel):
    """Request to submit a new appointment request."""
    hospital_id: UUID
    department: str
    reason: str
    preferred_type: AppointmentType = AppointmentType.IN_PERSON
    urgency: UrgencyLevel = UrgencyLevel.NORMAL


class AppointmentRequestResponse(BaseModel):
    """Full appointment request details."""
    id: UUID
    hospital_id: UUID
    hospital_name: str
    department: str
    reason: str
    preferred_type: AppointmentType
    urgency: UrgencyLevel
    status: RequestStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentRequestListResponse(BaseModel):
    """List of appointment requests."""
    requests: List[AppointmentRequestResponse]
    total: int


class AppointmentRequestActionResponse(BaseModel):
    """Response for appointment request actions."""
    success: bool
    message: str
    request: Optional[AppointmentRequestResponse] = None


# ============================================================================
# LINKED HOSPITALS WITH DEPARTMENTS
# ============================================================================

class DepartmentInfo(BaseModel):
    """Department info for dropdowns."""
    id: UUID
    name: str


class LinkedHospitalWithDepartments(BaseModel):
    """Linked hospital with its departments for the request modal."""
    id: UUID
    name: str
    city: str
    departments: List[DepartmentInfo]


class LinkedHospitalsResponse(BaseModel):
    """Response with linked hospitals for appointment request form."""
    hospitals: List[LinkedHospitalWithDepartments]

