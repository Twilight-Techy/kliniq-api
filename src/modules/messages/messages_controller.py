# src/modules/messages/messages_controller.py
"""Messages controller with API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session
from src.auth.dependencies import get_current_user
from src.models.models import User

from . import messages_service as service
from .schemas import (
    ConversationListResponse, ConversationDetailResponse,
    SendMessageRequest, SendMessageResponse,
    StartConversationRequest, StartConversationResponse,
    MarkReadResponse, AvailableCliniciansListResponse,
    EditMessageRequest, EditMessageResponse, DeleteMessageResponse
)

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get all conversations for the current user."""
    return await service.get_user_conversations(db, current_user)


@router.post("/conversations", response_model=StartConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Start a new conversation with a clinician."""
    result = await service.start_conversation(db, current_user, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get a conversation with all its messages."""
    result = await service.get_conversation_messages(db, current_user, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.post("/conversations/{conversation_id}", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Send a message in a conversation."""
    result = await service.send_message(db, current_user, conversation_id, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.put("/conversations/{conversation_id}/read", response_model=MarkReadResponse)
async def mark_as_read(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Mark all messages in a conversation as read."""
    result = await service.mark_messages_read(db, current_user, conversation_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.get("/available-clinicians", response_model=AvailableCliniciansListResponse)
async def get_available_clinicians(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get clinicians from linked hospitals to start new conversations with."""
    return await service.get_available_clinicians(db, current_user)


@router.put("/messages/{message_id}", response_model=EditMessageResponse)
async def edit_message(
    message_id: str,
    request: EditMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Edit a message (only sender can edit)."""
    result = await service.edit_message(db, current_user, message_id, request.content)
    if not result.success:
        raise HTTPException(status_code=403, detail=result.message)
    return result


@router.delete("/messages/{message_id}", response_model=DeleteMessageResponse)
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a message (only sender can delete)."""
    result = await service.delete_message(db, current_user, message_id)
    if not result.success:
        raise HTTPException(status_code=403, detail=result.message)
    return result
