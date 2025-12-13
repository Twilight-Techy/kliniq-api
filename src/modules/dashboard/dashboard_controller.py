# src/modules/dashboard/dashboard_controller.py
"""Dashboard controller with API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import dashboard_service as service
from .schemas import (
    DashboardResponse, HospitalSearchResponse, 
    LinkHospitalRequest, LinkHospitalResponse,
    ChatRequest, ChatResponse, ChatHistoryResponse
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get main dashboard data including:
    - Upcoming appointments
    - Linked hospitals
    - Dashboard stats
    - Language-specific welcome message
    """
    try:
        return await service.get_dashboard_data(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hospitals", response_model=HospitalSearchResponse)
async def list_hospitals(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available hospitals for selection.
    """
    return await service.get_all_hospitals(db)


@router.get("/hospitals/search", response_model=HospitalSearchResponse)
async def search_hospitals(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Search hospitals by name, code, or city.
    """
    return await service.search_hospitals(db, q)


@router.post("/hospitals/link", response_model=LinkHospitalResponse)
async def link_hospital(
    request: LinkHospitalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Link patient to a hospital by code or ID.
    """
    result = await service.link_hospital(
        db, 
        current_user, 
        hospital_code=request.hospital_code,
        hospital_id=request.hospital_id
    )
    await db.commit()
    return result


@router.delete("/hospitals/{hospital_id}")
async def unlink_hospital(
    hospital_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Unlink patient from a hospital.
    """
    result = await service.unlink_hospital(db, current_user, hospital_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    await db.commit()
    return result


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Send a message to the AI assistant (N-ATLaS).
    Returns AI response and chat ID for continuing conversation.
    """
    try:
        result = await service.process_chat(
            db, 
            current_user, 
            message=request.message,
            chat_id=request.chat_id
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get patient's chat history.
    """
    return await service.get_chat_history(db, current_user, limit)
