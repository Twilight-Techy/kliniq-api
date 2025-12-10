# src/auth/auth_service.py

from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from fastapi import HTTPException, status, BackgroundTasks
import jwt
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jwt.exceptions import DecodeError, ExpiredSignatureError

from src.common.config import settings
from src.common.utils.email_service import send_email, send_verification_email
from src.common.utils.otp import generate_verification_code
from src.models.models import User, UserRole, Patient, Clinician, ClinicianRoleType
from src.auth.schemas import SignupRole

# Initialize the password context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the provided password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT token including an expiration date."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def split_full_name(full_name: str) -> Tuple[str, str]:
    """Split a full name into first and last name."""
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def map_signup_role_to_user_role(signup_role: SignupRole) -> UserRole:
    """Map frontend signup role to database UserRole."""
    if signup_role == SignupRole.PATIENT:
        return UserRole.PATIENT
    elif signup_role in (SignupRole.NURSE, SignupRole.DOCTOR):
        return UserRole.CLINICIAN
    elif signup_role == SignupRole.ADMIN:
        return UserRole.ADMIN
    return UserRole.PATIENT


def map_signup_role_to_clinician_type(signup_role: SignupRole) -> Optional[ClinicianRoleType]:
    """Map frontend signup role to ClinicianRoleType (for nurses/doctors only)."""
    if signup_role == SignupRole.NURSE:
        return ClinicianRoleType.NURSE
    elif signup_role == SignupRole.DOCTOR:
        return ClinicianRoleType.DOCTOR
    return None


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
    db: AsyncSession
) -> User:
    """Create a new user in the database."""
    # Check if user with provided email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists!"
        )

    verification_code = generate_verification_code()

    # Create a new User instance
    new_user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        verification_code=verification_code,
        role=role
    )
    db.add(new_user)
    await db.flush()  # Get the user ID without committing
    
    return new_user


async def create_patient_profile(user: User, db: AsyncSession) -> Patient:
    """Create a patient profile for a user."""
    patient = Patient(user_id=user.id)
    db.add(patient)
    return patient


async def create_clinician_profile(
    user: User,
    clinician_type: ClinicianRoleType,
    db: AsyncSession
) -> Clinician:
    """Create a clinician profile for a user."""
    clinician = Clinician(
        user_id=user.id,
        role_type=clinician_type
    )
    db.add(clinician)
    return clinician


async def signup_user(
    full_name: str,
    email: str,
    password: str,
    signup_role: SignupRole,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> User:
    """
    Create a new user with appropriate role-based profile and send verification email.
    
    - Patient role: Creates User + Patient profile
    - Nurse/Doctor role: Creates User + Clinician profile
    - Admin role: Creates User only (admin profile may be created separately)
    """
    # Split full name
    first_name, last_name = split_full_name(full_name)
    
    if not first_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name is required!"
        )
    
    # Map to database role
    user_role = map_signup_role_to_user_role(signup_role)
    
    # Create the base user
    new_user = await create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=user_role,
        db=db
    )
    
    # Create role-specific profile
    if signup_role == SignupRole.PATIENT:
        await create_patient_profile(new_user, db)
    elif signup_role in (SignupRole.NURSE, SignupRole.DOCTOR):
        clinician_type = map_signup_role_to_clinician_type(signup_role)
        await create_clinician_profile(new_user, clinician_type, db)
    # Admin doesn't need additional profile for now
    
    # Commit all changes
    await db.commit()
    await db.refresh(new_user)
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        new_user.email,
        new_user.first_name,
        new_user.verification_code
    )
    
    return new_user


async def resend_verification_email(
    email: str,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> None:
    """Resend a verification email to the user."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found!"
        )
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified!"
        )

    new_verification_code = generate_verification_code()
    user.verification_code = new_verification_code
    await db.commit()
    await db.refresh(user)
    
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.first_name,
        new_verification_code
    )


async def verify_user(
    email: str,
    verification_code: str,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> Tuple[User, str]:
    """
    Verify a user's email using the provided verification code.
    Returns the user and access token.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found!"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified!"
        )

    if user.verification_code != verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code!"
        )

    user.email_verified = True
    user.verification_code = None  # Clear the code after use
    await db.commit()
    await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    # Send success email
    background_tasks.add_task(
        send_email,
        subject="Email Verification Successful",
        body="Your email has been successfully verified.",
        recipients=[user.email],
        html_body="<p>Your email has been successfully verified. You can now access all features.</p>"
    )

    return user, access_token


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    """Attempt to retrieve the user by email and verify the password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return user


async def login_user(email: str, password: str, db: AsyncSession) -> Tuple[User, str]:
    """Authenticate a user and return user with JWT access token."""
    user = await authenticate_user(email, password, db)
    
    # Update last_login timestamp
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return user, access_token


def create_reset_token(email: str, expires_delta: timedelta = None) -> str:
    """Generate a JWT reset token for password recovery."""
    to_encode = {"sub": email, "type": "reset"}
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=30))
    to_encode.update({"exp": expire})
    reset_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return reset_token


async def process_forgot_password(
    email: str,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> bool:
    """
    Process a forgot-password request.
    Always returns True to prevent email enumeration.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user:
        reset_token = create_reset_token(email, expires_delta=timedelta(minutes=30))
        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        text_body = f"Click the link below to reset your password:\n{reset_link}"
        html_body = f"""
        <p>Hi {user.first_name},</p>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">Reset Password</a>
        <p>This link expires in 30 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        background_tasks.add_task(send_email, subject, text_body, [email], html_body=html_body)
    
    return True


async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> bool:
    """Verify the reset token and update the user's password."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "reset":
            return False
    except (DecodeError, ExpiredSignatureError):
        return False

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        return False

    user.password_hash = hash_password(new_password)
    await db.commit()
    await db.refresh(user)

    # Send notification email
    subject = "Your Password Has Been Reset"
    text_body = "Your password has been successfully reset. If you did not initiate this, please contact support immediately."
    html_body = f"""
    <p>Hi {user.first_name},</p>
    <p>Your password has been successfully reset.</p>
    <p>If you did not initiate this reset, please <a href="{settings.SUPPORT_URL}">contact support</a> immediately.</p>
    """
    background_tasks.add_task(send_email, subject, text_body, [user.email], html_body=html_body)

    return True


async def change_password(
    user: User,
    current_password: str,
    new_password: str,
    db: AsyncSession,
    background_tasks: BackgroundTasks
) -> bool:
    """
    Verify the current password and update to new password.
    Returns True if successful, False if current password is incorrect.
    """
    if not verify_password(current_password, user.password_hash):
        return False

    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send notification email
    subject = "Your Password Has Been Changed"
    text_body = "Your password has been successfully changed. If you did not perform this action, please contact support immediately."
    html_body = f"""
    <p>Hi {user.first_name},</p>
    <p>Your password has been successfully changed.</p>
    <p>If you did not perform this action, please <a href="{settings.SUPPORT_URL}">contact support</a> immediately.</p>
    """
    background_tasks.add_task(send_email, subject, text_body, [user.email], html_body=html_body)

    return True