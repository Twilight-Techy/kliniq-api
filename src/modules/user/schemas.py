# src/modules/user/schemas.py

from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

from src.models.models import UserRole


class ProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    first_name: str
    last_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True