# src/modules/messages/messages_service.py
"""Service layer for messages business logic."""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from src.models.models import (
    User, Patient, Clinician, Conversation, Message, MessageType, PreferredLanguage
)
from .schemas import (
    ConversationResponse, ConversationListResponse, ConversationDetailResponse,
    MessageResponse, MessageListResponse,
    SendMessageRequest, SendMessageResponse,
    StartConversationRequest, StartConversationResponse,
    MarkReadResponse
)


def _get_initials(name: str) -> str:
    """Get initials from a name."""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return name[:2].upper() if name else "??"


def _format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time string."""
    now = datetime.utcnow()
    diff = now - dt.replace(tzinfo=None)
    
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days}d ago"


def _get_user_display_info(user: User) -> tuple[str, str]:
    """Get display name and role for a user."""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"
    
    if user.role.value == "clinician":
        # Try to get clinician info
        if hasattr(user, 'clinician') and user.clinician:
            clinician = user.clinician
            role = clinician.specialty or (clinician.role_type.value if clinician.role_type else "Clinician")
            if clinician.role_type and clinician.role_type.value == "doctor":
                full_name = f"Dr. {full_name}"
            return full_name, role
        return full_name, "Clinician"
    elif user.role.value == "patient":
        return full_name, "Patient"
    else:
        return full_name, user.role.value.title()


def _build_message_response(
    message: Message, 
    current_user_id: UUID
) -> MessageResponse:
    """Build MessageResponse from Message model."""
    is_mine = message.sender_id == current_user_id
    sender = message.sender
    sender_name, _ = _get_user_display_info(sender) if sender else ("Unknown", "Unknown")
    
    return MessageResponse(
        id=str(message.id),
        sender_type=sender.role.value if sender else "unknown",
        sender_name="You" if is_mine else sender_name,
        content=message.content,
        message_type=message.message_type.value if message.message_type else "text",
        is_read=message.is_read,
        attachment_url=message.attachment_url,
        attachment_name=message.attachment_name,
        audio_duration=message.audio_duration,
        original_language=message.original_language.value if message.original_language else None,
        transcripts=message.transcripts,
        created_at=message.created_at,
        is_mine=is_mine
    )


async def _build_conversation_response(
    session: AsyncSession,
    conversation: Conversation,
    current_user_id: UUID
) -> ConversationResponse:
    """Build ConversationResponse with last message and unread count."""
    # Determine which participant is the "other" person
    if conversation.participant_1_id == current_user_id:
        other_user = conversation.participant_2
    else:
        other_user = conversation.participant_1
    
    other_name, other_role = _get_user_display_info(other_user)
    
    # Get last message
    last_msg_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    last_message = last_msg_result.scalar_one_or_none()
    
    # Count unread messages (messages from other user that current user hasn't read)
    unread_result = await session.execute(
        select(func.count(Message.id))
        .where(
            Message.conversation_id == conversation.id,
            Message.sender_id != current_user_id,
            Message.is_read == False
        )
    )
    unread_count = unread_result.scalar() or 0
    
    # Check if other user is online (for clinicians)
    is_online = False
    if hasattr(other_user, 'clinician') and other_user.clinician:
        is_online = other_user.clinician.status == "active" if hasattr(other_user.clinician, 'status') else False
    
    return ConversationResponse(
        id=str(conversation.id),
        clinician_id=str(other_user.id),  # Using clinician_id for "other user id"
        clinician_name=other_name,
        clinician_role=other_role,
        clinician_avatar=_get_initials(other_name),
        last_message=last_message.content[:80] + "..." if last_message and len(last_message.content) > 80 else (last_message.content if last_message else None),
        last_message_time=_format_time_ago(last_message.created_at) if last_message else None,
        unread_count=unread_count,
        is_online=is_online,
        created_at=conversation.created_at
    )


async def get_user_conversations(
    session: AsyncSession,
    user: User
) -> ConversationListResponse:
    """Get all conversations for the user."""
    # Get conversations where user is either participant
    result = await session.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participant_1).selectinload(User.clinician),
            selectinload(Conversation.participant_2).selectinload(User.clinician)
        )
        .where(
            or_(
                Conversation.participant_1_id == user.id,
                Conversation.participant_2_id == user.id
            )
        )
        .order_by(desc(Conversation.updated_at))
    )
    conversations = result.scalars().all()
    
    # Build responses
    conversation_responses = []
    for conv in conversations:
        conv_response = await _build_conversation_response(session, conv, user.id)
        conversation_responses.append(conv_response)
    
    return ConversationListResponse(
        conversations=conversation_responses,
        total=len(conversation_responses)
    )


async def get_conversation_messages(
    session: AsyncSession,
    user: User,
    conversation_id: str
) -> Optional[ConversationDetailResponse]:
    """Get a conversation with all its messages."""
    conv_id = UUID(conversation_id)
    
    # Get conversation and verify user is a participant
    result = await session.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participant_1).selectinload(User.clinician),
            selectinload(Conversation.participant_2).selectinload(User.clinician)
        )
        .where(
            Conversation.id == conv_id,
            or_(
                Conversation.participant_1_id == user.id,
                Conversation.participant_2_id == user.id
            )
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        return None
    
    # Get messages with sender info
    messages_result = await session.execute(
        select(Message)
        .options(selectinload(Message.sender))
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    # Build response
    conv_response = await _build_conversation_response(session, conversation, user.id)
    
    # Build message responses
    message_responses = [
        _build_message_response(msg, user.id)
        for msg in messages
    ]
    
    return ConversationDetailResponse(
        conversation=conv_response,
        messages=message_responses
    )


async def send_message(
    session: AsyncSession,
    user: User,
    conversation_id: str,
    request: SendMessageRequest
) -> SendMessageResponse:
    """Send a message in a conversation."""
    conv_id = UUID(conversation_id)
    
    # Verify conversation exists and user is a participant
    conv_result = await session.execute(
        select(Conversation)
        .where(
            Conversation.id == conv_id,
            or_(
                Conversation.participant_1_id == user.id,
                Conversation.participant_2_id == user.id
            )
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        return SendMessageResponse(success=False, message="Conversation not found")
    
    # Create message
    message_type = MessageType.TEXT
    if request.message_type == "audio":
        message_type = MessageType.AUDIO
    elif request.message_type == "file":
        message_type = MessageType.FILE
    elif request.message_type == "image":
        message_type = MessageType.IMAGE
    
    # For audio messages, get sender's preferred language
    sender_preferred_language = None
    if message_type == MessageType.AUDIO:
        patient_result = await session.execute(
            select(Patient).where(Patient.user_id == user.id)
        )
        sender_patient = patient_result.scalar_one_or_none()
        if sender_patient and sender_patient.preferred_language:
            sender_preferred_language = sender_patient.preferred_language
    
    new_message = Message(
        conversation_id=conv_id,
        sender_id=user.id,
        content=request.content,
        message_type=message_type,
        is_read=False,
        attachment_url=request.attachment_url,
        attachment_name=request.attachment_name,
        original_language=sender_preferred_language
    )
    
    session.add(new_message)
    
    # Update conversation timestamps
    conversation.updated_at = datetime.utcnow()
    conversation.last_message_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(new_message)
    
    # Load sender relationship
    await session.refresh(new_message, ["sender"])
    
    return SendMessageResponse(
        success=True,
        message="Message sent",
        sent_message=_build_message_response(new_message, user.id)
    )


async def start_conversation(
    session: AsyncSession,
    user: User,
    request: StartConversationRequest
) -> StartConversationResponse:
    """Start a new conversation with another user (or get existing one)."""
    other_user_id = UUID(request.clinician_id)  # "clinician_id" is really "other_user_id"
    
    # Get the other user
    other_user_result = await session.execute(
        select(User)
        .options(selectinload(User.clinician))
        .where(User.id == other_user_id)
    )
    other_user = other_user_result.scalar_one_or_none()
    
    if not other_user:
        return StartConversationResponse(success=False, message="User not found")
    
    # Check if conversation already exists (in either direction)
    existing_result = await session.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participant_1).selectinload(User.clinician),
            selectinload(Conversation.participant_2).selectinload(User.clinician)
        )
        .where(
            or_(
                and_(
                    Conversation.participant_1_id == user.id,
                    Conversation.participant_2_id == other_user_id
                ),
                and_(
                    Conversation.participant_1_id == other_user_id,
                    Conversation.participant_2_id == user.id
                )
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        conv_response = await _build_conversation_response(session, existing, user.id)
        return StartConversationResponse(
            success=True,
            message="Conversation already exists",
            conversation=conv_response
        )
    
    # Create new conversation (smaller ID first for consistency)
    p1_id, p2_id = (user.id, other_user_id) if str(user.id) < str(other_user_id) else (other_user_id, user.id)
    
    new_conversation = Conversation(
        participant_1_id=p1_id,
        participant_2_id=p2_id
    )
    session.add(new_conversation)
    await session.flush()
    
    # Send initial message if provided
    if request.initial_message:
        initial_msg = Message(
            conversation_id=new_conversation.id,
            sender_id=user.id,
            content=request.initial_message,
            message_type=MessageType.TEXT,
            is_read=False
        )
        session.add(initial_msg)
        new_conversation.last_message_at = datetime.utcnow()
    
    await session.commit()
    
    # Reload with relationships
    result = await session.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participant_1).selectinload(User.clinician),
            selectinload(Conversation.participant_2).selectinload(User.clinician)
        )
        .where(Conversation.id == new_conversation.id)
    )
    new_conversation = result.scalar_one()
    
    conv_response = await _build_conversation_response(session, new_conversation, user.id)
    
    return StartConversationResponse(
        success=True,
        message="Conversation started",
        conversation=conv_response
    )


async def mark_messages_read(
    session: AsyncSession,
    user: User,
    conversation_id: str
) -> MarkReadResponse:
    """Mark all messages from the other user as read."""
    conv_id = UUID(conversation_id)
    
    # Verify conversation and get it
    conv_result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            or_(
                Conversation.participant_1_id == user.id,
                Conversation.participant_2_id == user.id
            )
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        return MarkReadResponse(success=False, message="Conversation not found")
    
    # Mark messages from other user as read
    result = await session.execute(
        update(Message)
        .where(
            Message.conversation_id == conv_id,
            Message.sender_id != user.id,
            Message.is_read == False
        )
        .values(is_read=True)
    )
    
    await session.commit()
    
    return MarkReadResponse(
        success=True,
        message="Messages marked as read",
        marked_count=result.rowcount
    )


async def get_available_clinicians(
    session: AsyncSession,
    user: User
) -> "AvailableCliniciansListResponse":
    """Get clinicians from linked hospitals that the user can start conversations with."""
    from .schemas import AvailableClinicianResponse, AvailableCliniciansListResponse
    from src.models.models import Patient, PatientHospital, Hospital, Clinician
    
    # Get patient
    patient_result = await session.execute(
        select(Patient).where(Patient.user_id == user.id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        return AvailableCliniciansListResponse(clinicians=[], total=0)
    
    # Get linked hospital IDs
    linked_result = await session.execute(
        select(PatientHospital.hospital_id)
        .where(PatientHospital.patient_id == patient.id)
    )
    linked_hospital_ids = [row[0] for row in linked_result.all()]
    
    if not linked_hospital_ids:
        return AvailableCliniciansListResponse(clinicians=[], total=0)
    
    # Get existing conversation partner IDs
    existing_convs = await session.execute(
        select(Conversation.participant_1_id, Conversation.participant_2_id)
        .where(
            or_(
                Conversation.participant_1_id == user.id,
                Conversation.participant_2_id == user.id
            )
        )
    )
    existing_partner_ids = set()
    for row in existing_convs.all():
        if row[0] != user.id:
            existing_partner_ids.add(row[0])
        if row[1] != user.id:
            existing_partner_ids.add(row[1])
    
    # Get clinicians from linked hospitals
    clinicians_result = await session.execute(
        select(Clinician, Hospital, User)
        .join(Hospital, Clinician.hospital_id == Hospital.id)
        .join(User, Clinician.user_id == User.id)
        .where(
            Clinician.hospital_id.in_(linked_hospital_ids),
            ~User.id.in_(existing_partner_ids) if existing_partner_ids else True
        )
        .order_by(Hospital.name, User.last_name)
    )
    
    clinicians = []
    for clinician, hospital, clinician_user in clinicians_result.all():
        full_name = f"{clinician_user.first_name or ''} {clinician_user.last_name or ''}".strip()
        if clinician.role_type and clinician.role_type.value == "doctor":
            full_name = f"Dr. {full_name}"
        
        clinicians.append(AvailableClinicianResponse(
            user_id=str(clinician_user.id),
            clinician_id=str(clinician.id),
            name=full_name,
            role=clinician.role_type.value if clinician.role_type else "clinician",
            specialty=clinician.specialty,
            avatar=_get_initials(full_name),
            hospital_name=hospital.name,
            hospital_id=str(hospital.id),
            is_online=clinician.status == "active" if hasattr(clinician, 'status') else False
        ))
    
    return AvailableCliniciansListResponse(
        clinicians=clinicians,
        total=len(clinicians)
    )


async def edit_message(
    session: AsyncSession,
    user: User,
    message_id: str,
    new_content: str
) -> "EditMessageResponse":
    """Edit a message (only sender can edit their own messages)."""
    from .schemas import EditMessageResponse
    
    msg_id = UUID(message_id)
    
    # Get message and verify ownership
    result = await session.execute(
        select(Message)
        .options(selectinload(Message.sender))
        .where(Message.id == msg_id, Message.sender_id == user.id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        return EditMessageResponse(success=False, message="Message not found or not authorized")
    
    # Update content
    message.content = new_content
    await session.commit()
    await session.refresh(message, ["sender"])
    
    return EditMessageResponse(
        success=True,
        message="Message updated",
        updated_message=_build_message_response(message, user.id)
    )


async def delete_message(
    session: AsyncSession,
    user: User,
    message_id: str
) -> "DeleteMessageResponse":
    """Delete a message (only sender can delete their own messages)."""
    from .schemas import DeleteMessageResponse
    
    msg_id = UUID(message_id)
    
    # Get message and verify ownership
    result = await session.execute(
        select(Message).where(Message.id == msg_id, Message.sender_id == user.id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        return DeleteMessageResponse(success=False, message="Message not found or not authorized")
    
    # Delete message
    await session.delete(message)
    await session.commit()
    
    return DeleteMessageResponse(success=True, message="Message deleted")


async def transcribe_message(
    session: AsyncSession,
    user: User,
    message_id: str,
    override_language: str = None,
    view_language: str = None
) -> dict:
    """
    Transcribe an audio message and translate to all languages.
    
    Flow:
    1. Get the message's original_language (from sender's preferred language)
    2. Override original_language if user specifies spoken language
    3. If not transcribed yet: transcribe using N-ATLaS ASR
    4. Translate to all 4 languages and cache them
    5. Return transcript in viewer's preferred language (or specified view_language)
    
    Args:
        session: Database session
        user: Current user (viewer)
        message_id: ID of the message to transcribe
        override_language: If provided, overrides original_language and re-transcribes
        view_language: Language to return (defaults to viewer's preferred language)
        
    Returns:
        Dict with text, language, original_language, cached, translated flags
    """
    from src.common.llm.transcription_service import transcribe_audio
    from src.common.llm.translation_service import translate_text
    
    msg_id = UUID(message_id)
    
    # Get the message
    result = await session.execute(
        select(Message).where(Message.id == msg_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        return {"error": "Message not found"}
    
    if not message.attachment_url:
        return {"error": "Message has no audio attachment"}
    
    # Determine viewer's preferred language
    if view_language:
        target_language = view_language.lower()
    else:
        # Get viewer's preferred language
        viewer_result = await session.execute(
            select(Patient).where(Patient.user_id == user.id)
        )
        viewer_patient = viewer_result.scalar_one_or_none()
        
        if viewer_patient and viewer_patient.preferred_language:
            target_language = viewer_patient.preferred_language.value
        else:
            # Default to English for clinicians or users without preference
            target_language = "english"
    
    transcripts = message.transcripts or {}
    
    # If just viewing existing transcript
    if not override_language and target_language in transcripts:
        return {
            "text": transcripts[target_language],
            "language": target_language,
            "original_language": message.original_language.value if message.original_language else None,
            "cached": True,
            "translated": target_language != (message.original_language.value if message.original_language else None)
        }
    
    # Determine spoken language for transcription
    if override_language:
        # User is specifying/correcting the spoken language
        spoken_lang = override_language.lower()
        # Convert string to enum
        try:
            message.original_language = PreferredLanguage(spoken_lang)
        except ValueError:
            message.original_language = PreferredLanguage.ENGLISH
        # Clear existing transcripts for re-transcription
        transcripts = {}
    elif message.original_language:
        spoken_lang = message.original_language.value
    else:
        # No original language set, default to English
        spoken_lang = "english"
        message.original_language = PreferredLanguage.ENGLISH
    
    # Transcribe in the original/spoken language
    transcription_result = await transcribe_audio(message.attachment_url, spoken_lang)
    
    if transcription_result.get("error"):
        return {"error": transcription_result["error"]}
    
    original_text = transcription_result.get("text", "")
    
    # Store original transcript
    transcripts[spoken_lang] = original_text
    
    # All supported languages
    all_languages = ["english", "yoruba", "hausa", "igbo"]
    
    # Translate to all other languages
    for lang in all_languages:
        if lang != spoken_lang and lang not in transcripts:
            translation = await translate_text(
                text=original_text,
                source_language=spoken_lang,
                target_language=lang
            )
            transcripts[lang] = translation.get("text", original_text)
    
    # Save to database
    message.transcripts = transcripts
    flag_modified(message, "transcripts")
    await session.commit()
    
    return {
        "text": transcripts.get(target_language, original_text),
        "language": target_language,
        "original_language": spoken_lang,
        "cached": False,
        "translated": target_language != spoken_lang
    }

