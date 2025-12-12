# src/modules/onboarding/onboarding_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User, UserRole
from src.modules.onboarding import onboarding_service
from src.modules.onboarding.schemas import (
    SetLanguageRequest,
    UpdateProfileRequest,
    OnboardingStatusResponse,
    OnboardingCompleteResponse,
    LanguageResponse,
    ProfileResponse,
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the current onboarding status for the authenticated patient.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access onboarding"
        )
    
    result = await onboarding_service.get_onboarding_status(
        str(current_user.id), db
    )
    return OnboardingStatusResponse(**result)


@router.put("/language", response_model=LanguageResponse)
async def set_language(
    request: SetLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Set the patient's preferred language for communication.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access onboarding"
        )
    
    try:
        result = await onboarding_service.set_preferred_language(
            str(current_user.id),
            request.language.value,
            db
        )
        return LanguageResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update patient profile information during onboarding.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access onboarding"
        )
    
    try:
        result = await onboarding_service.update_patient_profile(
            user_id=str(current_user.id),
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            city=request.city,
            state=request.state,
            address=request.address,
            db=db
        )
        return ProfileResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Mark onboarding as complete for the patient.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access onboarding"
        )
    
    try:
        result = await onboarding_service.complete_onboarding(
            str(current_user.id), db
        )
        return OnboardingCompleteResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
