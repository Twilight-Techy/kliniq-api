# src/common/llm/tool_executor.py
"""
Tool executor for processing LLM tool calls.

Parses TOOL_CALL blocks from LLM responses and executes the corresponding actions.
"""

import re
import json
from typing import Optional, Tuple, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import (
    User, Patient, PatientHospital, AppointmentRequest,
    AppointmentType as DBAppointmentType,
    UrgencyLevel as DBUrgencyLevel,
    RequestStatus as DBRequestStatus,
    TriageChat, PreferredLanguage
)
from sqlalchemy import select


# Regex to find TOOL_CALL blocks
TOOL_CALL_PATTERN = re.compile(r'<TOOL_CALL>\s*(\{.*?\})\s*</TOOL_CALL>', re.DOTALL)


def parse_tool_calls(response: str) -> Tuple[str, List[dict]]:
    """
    Parse LLM response for tool calls.
    
    Returns:
        Tuple of (cleaned_response, list_of_tool_calls)
    """
    tool_calls = []
    
    # Find all TOOL_CALL blocks
    matches = TOOL_CALL_PATTERN.findall(response)
    
    for match in matches:
        try:
            tool_call = json.loads(match)
            if "tool" in tool_call:
                tool_calls.append(tool_call)
        except json.JSONDecodeError:
            # Invalid JSON, skip
            continue
    
    # Remove TOOL_CALL blocks from response
    cleaned_response = TOOL_CALL_PATTERN.sub('', response).strip()
    
    return cleaned_response, tool_calls


async def execute_tool_calls(
    session: AsyncSession,
    user: User,
    patient: Patient,
    tool_calls: List[dict]
) -> List[dict]:
    """
    Execute parsed tool calls and return results.
    
    Args:
        session: Database session
        user: Current user
        patient: Patient model
        tool_calls: List of parsed tool calls
        
    Returns:
        List of tool execution results
    """
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("tool")
        params = tool_call.get("parameters", {})
        
        if tool_name == "request_appointment":
            result = await execute_request_appointment(session, patient, params)
            results.append({"tool": tool_name, "result": result})
            
        elif tool_name == "create_triage":
            result = await execute_create_triage(session, patient, params)
            results.append({"tool": tool_name, "result": result})
            
        else:
            results.append({"tool": tool_name, "result": {"error": f"Unknown tool: {tool_name}"}})
    
    return results


async def execute_request_appointment(
    session: AsyncSession,
    patient: Patient,
    params: dict
) -> dict:
    """
    Execute appointment request tool.
    
    Required params:
        - reason: str
        - urgency: str (low, normal, urgent)
    Optional:
        - department: str
    """
    reason = params.get("reason")
    urgency = params.get("urgency", "normal")
    department = params.get("department", "General Practice")
    
    if not reason:
        return {"success": False, "message": "Reason is required for appointment request"}
    
    # Get patient's first linked hospital
    hospital_result = await session.execute(
        select(PatientHospital)
        .where(PatientHospital.patient_id == patient.id)
        .limit(1)
    )
    patient_hospital = hospital_result.scalar_one_or_none()
    
    if not patient_hospital:
        return {
            "success": False, 
            "message": "Patient must be linked to a hospital to request appointments"
        }
    
    # Map urgency
    urgency_map = {
        "low": DBUrgencyLevel.LOW,
        "normal": DBUrgencyLevel.NORMAL,
        "urgent": DBUrgencyLevel.URGENT,
    }
    db_urgency = urgency_map.get(urgency.lower(), DBUrgencyLevel.NORMAL)
    
    # Create appointment request
    apt_request = AppointmentRequest(
        patient_id=patient.id,
        hospital_id=patient_hospital.hospital_id,
        department=department,
        reason=reason,
        preferred_type=DBAppointmentType.IN_PERSON,
        urgency=db_urgency,
        status=DBRequestStatus.PENDING
    )
    session.add(apt_request)
    await session.flush()
    
    return {
        "success": True,
        "message": f"Appointment request submitted successfully",
        "request_id": str(apt_request.id),
        "urgency": urgency,
        "department": department
    }


async def execute_create_triage(
    session: AsyncSession,
    patient: Patient,
    params: dict
) -> dict:
    """
    Execute create triage case tool.
    
    Required params:
        - symptoms: str
        - urgency_level: str (low, medium, high)
    Optional:
        - notes: str
    """
    symptoms = params.get("symptoms")
    urgency_level = params.get("urgency_level", "medium")
    notes = params.get("notes", "")
    
    if not symptoms:
        return {"success": False, "message": "Symptoms description is required"}
    
    # Check if there's an active triage chat already
    existing_result = await session.execute(
        select(TriageChat)
        .where(TriageChat.patient_id == patient.id)
        .where(TriageChat.is_active == True)
    )
    existing_chat = existing_result.scalar_one_or_none()
    
    if existing_chat:
        # Update existing triage with new symptoms
        triage_data = existing_chat.triage_data or {}
        triage_data["symptoms"] = symptoms
        triage_data["urgency_level"] = urgency_level
        triage_data["notes"] = notes
        existing_chat.triage_data = triage_data
        
        return {
            "success": True,
            "message": "Triage case updated with new symptoms",
            "triage_id": str(existing_chat.id),
            "urgency_level": urgency_level
        }
    
    # Create new triage chat with triage data
    preferred_lang = patient.preferred_language if patient.preferred_language else PreferredLanguage.ENGLISH
    
    triage_chat = TriageChat(
        patient_id=patient.id,
        language=preferred_lang,
        messages=[],
        is_active=True,
        triage_data={
            "symptoms": symptoms,
            "urgency_level": urgency_level,
            "notes": notes
        }
    )
    session.add(triage_chat)
    await session.flush()
    
    return {
        "success": True,
        "message": "Triage case created successfully",
        "triage_id": str(triage_chat.id),
        "urgency_level": urgency_level
    }
