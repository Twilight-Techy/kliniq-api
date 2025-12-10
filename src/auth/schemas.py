# src/auth/schemas.py

from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from fastapi import HTTPException
from enum import Enum

from src.models.models import UserRole


class SignupRole(str, Enum):
    """Frontend role selection - maps to UserRole + ClinicianRoleType"""
    PATIENT = "patient"
    NURSE = "nurse"
    DOCTOR = "doctor"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User info returned after login/signup"""
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full name (will be split into first and last name)")
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    role: SignupRole = SignupRole.PATIENT

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password_confirm:
            raise HTTPException(
                status_code=400,
                detail="Passwords do not match."
            )
        return self


class SignupResponse(BaseModel):
    message: str = "Account created successfully. Please check your email to verify your account."
    user: UserResponse


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    message: str = "A new verification email has been sent."


class VerifyUserRequest(BaseModel):
    email: EmailStr
    verification_code: str


class VerifyUserResponse(BaseModel):
    message: str = "Email verified successfully."
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "If an account with this email exists, a password reset link has been sent."


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: Annotated[str, Field(min_length=8)]
    confirm_new_password: Annotated[str, Field(min_length=8)]

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise HTTPException(
                status_code=400,
                detail="New password and confirmation do not match."
            )
        return self


class ResetPasswordResponse(BaseModel):
    message: str = "Password reset successful."


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise HTTPException(
                status_code=400,
                detail="New password and confirmation do not match."
            )
        if self.new_password == self.current_password:
            raise HTTPException(
                status_code=400,
                detail="New password cannot be the same as the current password."
            )
        return self

    class Config:
        from_attributes = True


class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully."
