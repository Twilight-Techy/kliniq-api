# src/modules/messages/schemas.py
"""Pydantic schemas for messages module."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class MessageResponse(BaseModel):
    id: str
    sender_type: str  # "patient" or "clinician"  
    sender_name: str
    content: str
    message_type: str
    is_read: bool
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    audio_duration: Optional[int] = None
    original_language: Optional[str] = None  # Language the audio was spoken in
    transcripts: Optional[dict] = None  # Multi-language transcripts {"english": "...", "yoruba": "..."}
    created_at: datetime
    is_mine: bool  # True if sent by current user

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int


class ConversationResponse(BaseModel):
    id: str
    clinician_id: str
    clinician_name: str
    clinician_role: str
    clinician_avatar: str  # Initials e.g. "OA"
    last_message: Optional[str] = None
    last_message_time: Optional[str] = None
    unread_count: int = 0
    is_online: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


class SendMessageResponse(BaseModel):
    success: bool
    message: str
    sent_message: Optional[MessageResponse] = None


class StartConversationRequest(BaseModel):
    clinician_id: str
    initial_message: Optional[str] = None


class StartConversationResponse(BaseModel):
    success: bool
    message: str
    conversation: Optional[ConversationResponse] = None


class MarkReadResponse(BaseModel):
    success: bool
    message: str
    marked_count: int = 0


class AvailableClinicianResponse(BaseModel):
    """A clinician available to start a conversation with."""
    user_id: str
    clinician_id: str
    name: str
    role: str
    specialty: Optional[str] = None
    avatar: str  # Initials
    hospital_name: str
    hospital_id: str
    is_online: bool = False

    class Config:
        from_attributes = True


class AvailableCliniciansListResponse(BaseModel):
    clinicians: List[AvailableClinicianResponse]
    total: int


class EditMessageRequest(BaseModel):
    content: str


class EditMessageResponse(BaseModel):
    success: bool
    message: str
    updated_message: Optional[MessageResponse] = None


class DeleteMessageResponse(BaseModel):
    success: bool
    message: str
