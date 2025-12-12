# src/modules/onboarding/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class LanguageOption(str, Enum):
    """Supported languages for the Kliniq platform."""
    ENGLISH = "english"
    HAUSA = "hausa"
    IGBO = "igbo"
    YORUBA = "yoruba"


class SetLanguageRequest(BaseModel):
    """Request schema for setting the patient's preferred language."""
    language: LanguageOption = Field(..., description="The patient's preferred language")


class UpdateProfileRequest(BaseModel):
    """Request schema for updating patient profile information during onboarding."""
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=20, description="Gender")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Region")
    address: Optional[str] = Field(None, description="Full address")


class OnboardingStatusResponse(BaseModel):
    """Response schema for onboarding status check."""
    onboarding_completed: bool
    preferred_language: Optional[str] = None
    has_profile_info: bool = False


class OnboardingCompleteResponse(BaseModel):
    """Response schema for completing onboarding."""
    success: bool
    message: str


class LanguageResponse(BaseModel):
    """Response schema for language update."""
    success: bool
    language: str


class ProfileResponse(BaseModel):
    """Response schema for profile update."""
    success: bool
    message: str
