# src/modules/history/history_service.py
"""Service layer for medical history business logic."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import (
    User, Patient, MedicalHistory, Clinician,
    MedicalHistoryType as DBMedicalHistoryType
)
from .schemas import (
    MedicalHistoryResponse, MedicalHistoryListResponse, MedicalHistoryType
)


def _convert_type(db_type: DBMedicalHistoryType) -> MedicalHistoryType:
    """Convert database enum to schema enum."""
    mapping = {
        DBMedicalHistoryType.CONSULTATION: MedicalHistoryType.CONSULTATION,
        DBMedicalHistoryType.PRESCRIPTION: MedicalHistoryType.PRESCRIPTION,
        DBMedicalHistoryType.TEST: MedicalHistoryType.TEST,
        DBMedicalHistoryType.DIAGNOSIS: MedicalHistoryType.DIAGNOSIS,
    }
    return mapping.get(db_type, MedicalHistoryType.CONSULTATION)


def _build_history_response(history: MedicalHistory) -> MedicalHistoryResponse:
    """Build MedicalHistoryResponse from database model."""
    doctor_name = None
    
    if history.clinician and history.clinician.user:
        doctor_name = f"Dr. {history.clinician.user.first_name} {history.clinician.user.last_name}"
    
    return MedicalHistoryResponse(
        id=str(history.id),
        type=_convert_type(history.type),
        title=history.title,
        doctor_name=doctor_name,
        description=history.description,
        date=history.date.strftime("%b %d, %Y"),
        status=history.status,
        created_at=history.created_at,
    )


async def get_patient_history(
    session: AsyncSession,
    user: User,
    history_type: Optional[str] = None
) -> MedicalHistoryListResponse:
    """Get all medical history for the current patient."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return MedicalHistoryListResponse(history=[], total=0)
    
    # Build query
    query = (
        select(MedicalHistory)
        .options(
            selectinload(MedicalHistory.clinician).selectinload(Clinician.user),
        )
        .where(MedicalHistory.patient_id == patient.id)
    )
    
    # Filter by type if provided
    if history_type and history_type != "all":
        type_mapping = {
            "consultation": DBMedicalHistoryType.CONSULTATION,
            "prescription": DBMedicalHistoryType.PRESCRIPTION,
            "test": DBMedicalHistoryType.TEST,
            "diagnosis": DBMedicalHistoryType.DIAGNOSIS,
        }
        if history_type in type_mapping:
            query = query.where(MedicalHistory.type == type_mapping[history_type])
    
    query = query.order_by(MedicalHistory.date.desc(), MedicalHistory.created_at.desc())
    
    result = await session.execute(query)
    history_items = result.scalars().all()
    
    history_responses = [_build_history_response(h) for h in history_items]
    
    return MedicalHistoryListResponse(
        history=history_responses,
        total=len(history_responses)
    )


async def get_history_by_id(
    session: AsyncSession,
    user: User,
    history_id: UUID
) -> Optional[MedicalHistoryResponse]:
    """Get a single history item by ID."""
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return None
    
    query = (
        select(MedicalHistory)
        .options(
            selectinload(MedicalHistory.clinician).selectinload(Clinician.user),
        )
        .where(
            MedicalHistory.id == history_id,
            MedicalHistory.patient_id == patient.id
        )
    )
    
    result = await session.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        return None
    
    return _build_history_response(history)
