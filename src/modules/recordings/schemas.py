# src/modules/recordings/schemas.py
"""Pydantic schemas for recordings module."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel


class RecordingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# RECORDING SCHEMAS
# ============================================================================

class RecordingResponse(BaseModel):
    id: str
    title: str
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    specialty: Optional[str] = None
    duration_seconds: int
    file_size_bytes: Optional[int] = None
    file_url: Optional[str] = None
    transcript: Optional[str] = None
    status: RecordingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class RecordingListResponse(BaseModel):
    recordings: List[RecordingResponse]
    total: int


class RecordingCreateRequest(BaseModel):
    title: str
    appointment_id: Optional[str] = None
    duration_seconds: int = 0


class RecordingUploadRequest(BaseModel):
    file_url: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None


class RecordingActionResponse(BaseModel):
    success: bool
    message: str
    recording: Optional[RecordingResponse] = None


# ============================================================================
# APPOINTMENT SELECTION SCHEMAS
# ============================================================================

class UpcomingAppointmentResponse(BaseModel):
    id: str
    doctor_name: str
    specialty: str
    hospital_name: str
    scheduled_date: str
    scheduled_time: str
    type: str
    status: str

    class Config:
        from_attributes = True


class UpcomingAppointmentsListResponse(BaseModel):
    appointments: List[UpcomingAppointmentResponse]


# ============================================================================
# TRANSCRIPTION SCHEMAS
# ============================================================================

class TranscriptionResponse(BaseModel):
    """Response from transcription request."""
    text: str
    language: str
    original_language: Optional[str] = None
    cached: bool = False
    translated: bool = False
    error: Optional[str] = None
