# src/modules/onboarding/onboarding_service.py

from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.models import User, Patient, PreferredLanguage


async def get_patient_by_user_id(user_id: str, db: AsyncSession) -> Optional[Patient]:
    """Get patient record by user ID."""
    result = await db.execute(
        select(Patient).where(Patient.user_id == user_id)
    )
    return result.scalars().first()


async def get_onboarding_status(user_id: str, db: AsyncSession) -> dict:
    """
    Check the onboarding status for a patient.
    Returns status info including completion state and current progress.
    """
    patient = await get_patient_by_user_id(user_id, db)
    
    if not patient:
        return {
            "onboarding_completed": False,
            "preferred_language": None,
            "has_profile_info": False
        }
    
    has_profile_info = bool(
        patient.date_of_birth or 
        patient.gender or 
        patient.city
    )
    
    return {
        "onboarding_completed": patient.onboarding_completed,
        "preferred_language": patient.preferred_language.value if patient.preferred_language else None,
        "has_profile_info": has_profile_info
    }


async def set_preferred_language(
    user_id: str, 
    language: str, 
    db: AsyncSession
) -> dict:
    """
    Set the patient's preferred language.
    """
    patient = await get_patient_by_user_id(user_id, db)
    
    if not patient:
        raise ValueError("Patient profile not found")
    
    # Map string to enum
    language_enum = PreferredLanguage(language)
    patient.preferred_language = language_enum
    
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    return {
        "success": True,
        "language": language_enum.value
    }


async def update_patient_profile(
    user_id: str,
    phone: Optional[str],
    date_of_birth: Optional[date],
    gender: Optional[str],
    city: Optional[str],
    state: Optional[str],
    address: Optional[str],
    db: AsyncSession
) -> dict:
    """
    Update patient profile information during onboarding.
    Also updates the user's phone number.
    """
    patient = await get_patient_by_user_id(user_id, db)
    
    if not patient:
        raise ValueError("Patient profile not found")
    
    # Update patient fields
    if date_of_birth is not None:
        patient.date_of_birth = date_of_birth
    if gender is not None:
        patient.gender = gender
    if city is not None:
        patient.city = city
    if state is not None:
        patient.state = state
    if address is not None:
        patient.address = address
    
    db.add(patient)
    
    # Update user's phone number
    if phone is not None:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if user:
            user.phone = phone
            db.add(user)
    
    await db.commit()
    await db.refresh(patient)
    
    return {
        "success": True,
        "message": "Profile updated successfully"
    }


async def complete_onboarding(user_id: str, db: AsyncSession) -> dict:
    """
    Mark onboarding as complete for the patient.
    """
    patient = await get_patient_by_user_id(user_id, db)
    
    if not patient:
        raise ValueError("Patient profile not found")
    
    patient.onboarding_completed = True
    
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    return {
        "success": True,
        "message": "Onboarding completed successfully"
    }
