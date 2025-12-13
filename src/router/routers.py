# src/router/routers.py

from fastapi import FastAPI
from src.auth.auth_controller import router as auth_router
from src.modules.user.user_controller import router as user_router
from src.modules.onboarding.onboarding_controller import router as onboarding_router
from src.modules.dashboard.dashboard_controller import router as dashboard_router

def include_routers(app: FastAPI) -> None:
    """Include all API routers in the FastAPI application."""
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(onboarding_router)
    app.include_router(dashboard_router)
    
    # TODO: Add new Kliniq module routers here as they are created
    # app.include_router(hospital_router)
    # app.include_router(patient_router)
    # app.include_router(clinician_router)
    # app.include_router(appointment_router)
    # app.include_router(notification_router)
    # app.include_router(message_router)

