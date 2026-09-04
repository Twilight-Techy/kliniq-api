# src/modules/admin/admin_controller.py
"""Hospital administration endpoints. Every route is admin-only."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.common.database.database import get_db_session
from src.models.models import User

from . import admin_service as service

router = APIRouter(prefix="/admin", tags=["Admin"])


class HospitalSettingsUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None


@router.get("/overview")
async def overview(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Headline stats, weekly consultation volume and department distribution."""
    try:
        return await service.get_overview(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/clinicians")
async def clinicians(
    role: Optional[str] = Query(None, description="doctor or nurse"),
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.list_clinicians(db, admin, role=role, search=search)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/patients")
async def patients(
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.list_patients(db, admin, search=search, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/appointments")
async def appointments(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.list_appointments(db, admin, status_filter=status, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analytics")
async def analytics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.get_analytics(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/billing")
async def billing(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.list_invoices(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports")
async def reports(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.list_reports(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/settings")
async def get_settings(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.get_settings(db, admin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/settings")
async def update_settings(
    payload: HospitalSettingsUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await service.update_settings(db, admin, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
