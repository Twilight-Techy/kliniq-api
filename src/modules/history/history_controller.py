# src/modules/history/history_controller.py
"""History controller with API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import history_service as service
from .schemas import MedicalHistoryResponse, MedicalHistoryListResponse

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=MedicalHistoryListResponse)
async def get_history(
    type: Optional[str] = Query(None, description="Filter by type: all, consultation, prescription, test, diagnosis"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get patient's medical history with optional type filter."""
    return await service.get_patient_history(db, current_user, type)


@router.get("/{history_id}", response_model=MedicalHistoryResponse)
async def get_history_item(
    history_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get a single history item by ID."""
    history = await service.get_history_by_id(db, current_user, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History item not found")
    return history
