# src/user/user_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.user import user_service, schemas
from src.common.database.database import get_db_session
from src.models.models import User
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile", response_model=schemas.ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve the profile for the currently authenticated user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return current_user

@router.put("/profile", response_model=schemas.ProfileResponse)
async def update_profile(
    profile_data: schemas.UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update the profile of the currently authenticated user.
    
    Only the provided fields will be updated.
    """
    updated_user = await user_service.update_user_profile(current_user, profile_data.model_dump(), db)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return updated_user