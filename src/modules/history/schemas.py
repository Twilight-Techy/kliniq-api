# src/modules/history/schemas.py
"""Pydantic schemas for medical history module."""

from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel


class MedicalHistoryType(str, Enum):
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    TEST = "test"
    DIAGNOSIS = "diagnosis"


class MedicalHistoryResponse(BaseModel):
    id: str
    type: MedicalHistoryType
    title: str
    doctor_name: Optional[str] = None
    description: Optional[str] = None
    date: str  # Formatted date string
    status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalHistoryListResponse(BaseModel):
    history: List[MedicalHistoryResponse]
    total: int
