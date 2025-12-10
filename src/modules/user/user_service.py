# src/user/user_service.py

from sqlalchemy import func
from sqlalchemy.future import select
from src.models.models import User
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_profile(current_user: User) -> User:
    """
    Retrieve the current user's profile.
    
    In this example, we simply return the current user instance.
    Additional business logic or data transformations can be applied here if needed.
    """
    return current_user

async def update_user_profile(current_user: User, profile_data: dict, db: AsyncSession) -> User:
    """
    Update the current user's profile with provided data.
    
    Only the fields provided (non-None) will be updated.
    """
    for key, value in profile_data.items():
        if value is not None and hasattr(current_user, key):
            setattr(current_user, key, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user