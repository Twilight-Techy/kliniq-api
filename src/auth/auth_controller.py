# src/auth/auth_controller.py

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.common.database.database import get_db_session
from src.auth import auth_service, schemas
from src.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def user_to_response(user: User) -> schemas.UserResponse:
    """Convert User model to UserResponse schema."""
    return schemas.UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_verified=user.email_verified
    )


@router.post("/signup", response_model=schemas.SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: schemas.SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.
    
    - **full_name**: User's full name (will be split into first/last name)
    - **email**: User's email address
    - **password**: Password (minimum 8 characters)
    - **password_confirm**: Password confirmation (must match)
    - **role**: User role - patient, nurse, doctor, or admin
    """
    user = await auth_service.signup_user(
        full_name=signup_data.full_name,
        email=signup_data.email,
        password=signup_data.password,
        signup_role=signup_data.role,
        db=db,
        background_tasks=background_tasks
    )
    
    return schemas.SignupResponse(user=user_to_response(user))


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    credentials: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate a user and return an access token.
    
    - **email**: User's email address
    - **password**: User's password
    """
    user, access_token = await auth_service.login_user(
        email=credentials.email,
        password=credentials.password,
        db=db
    )
    
    return schemas.LoginResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.post("/resend-verification", response_model=schemas.ResendVerificationResponse)
async def resend_verification(
    request: schemas.ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resend a verification email to the user.
    
    - **email**: User's email address
    """
    await auth_service.resend_verification_email(
        email=request.email,
        db=db,
        background_tasks=background_tasks
    )
    
    return schemas.ResendVerificationResponse()


@router.post("/verify", response_model=schemas.VerifyUserResponse)
async def verify_user(
    verification_data: schemas.VerifyUserRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Verify a user's email using the verification code.
    
    - **email**: User's email address
    - **verification_code**: Code received via email
    """
    user, access_token = await auth_service.verify_user(
        email=verification_data.email,
        verification_code=verification_data.verification_code,
        db=db,
        background_tasks=background_tasks
    )
    
    return schemas.VerifyUserResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.post("/forgot-password", response_model=schemas.ForgotPasswordResponse)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration.
    
    - **email**: User's email address
    """
    await auth_service.process_forgot_password(
        email=request.email,
        db=db,
        background_tasks=background_tasks
    )
    
    return schemas.ForgotPasswordResponse()


@router.post("/reset-password", response_model=schemas.ResetPasswordResponse)
async def reset_password(
    payload: schemas.ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Reset the user's password using a reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)
    - **confirm_new_password**: Password confirmation
    """
    success = await auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
        db=db,
        background_tasks=background_tasks
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    
    return schemas.ResetPasswordResponse()


@router.post("/change-password", response_model=schemas.ChangePasswordResponse)
async def change_password(
    change_req: schemas.ChangePasswordRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Change the current user's password.
    
    Requires authentication.
    
    - **current_password**: Current password
    - **new_password**: New password (minimum 8 characters)
    - **confirm_new_password**: Password confirmation
    """
    success = await auth_service.change_password(
        user=current_user,
        current_password=change_req.current_password,
        new_password=change_req.new_password,
        db=db,
        background_tasks=background_tasks
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )
    
    return schemas.ChangePasswordResponse()


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current authenticated user's information.
    
    Requires authentication.
    """
    return user_to_response(current_user)