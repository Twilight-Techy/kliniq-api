# src/router/routers.py

from fastapi import FastAPI
from src.auth.auth_controller import router as auth_router
from src.modules.user.user_controller import router as user_router
from src.modules.onboarding.onboarding_controller import router as onboarding_router
from src.modules.dashboard.dashboard_controller import router as dashboard_router
from src.modules.appointments.appointments_controller import router as appointments_router
from src.modules.recordings.recordings_controller import router as recordings_router
from src.modules.history.history_controller import router as history_router
from src.modules.settings.settings_controller import router as settings_router
from src.modules.messages.messages_controller import router as messages_router
from src.modules.notifications.notifications_controller import router as notifications_router
from src.modules.clinician.clinician_controller import router as clinician_router

def include_routers(app: FastAPI) -> None:
    """Include all API routers in the FastAPI application."""
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(onboarding_router)
    app.include_router(dashboard_router)
    app.include_router(appointments_router)
    app.include_router(recordings_router)
    app.include_router(history_router)
    app.include_router(settings_router)
    app.include_router(messages_router)
    app.include_router(notifications_router)
    app.include_router(clinician_router)

