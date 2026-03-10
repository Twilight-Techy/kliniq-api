# src/common/llm/llm_service.py
"""
LLM Service — backward-compatible wrapper around the provider system.

This module retains the original LLMService class interface so that
existing imports (`from src.common.llm import LLMService`) continue
to work. Internally, it delegates to the configured provider
(Gemini or N-ATLaS) via the provider factory.
"""

from typing import Optional
from datetime import datetime


# Kliniq-specific system prompts for different contexts
# Use {context} placeholder for dynamic injection of doctor notes, appointments, etc.

SYSTEM_PROMPTS = {
    "general": """You are Kliniq AI, a compassionate and knowledgeable healthcare assistant for Nigerian patients. You help patients navigate their healthcare journey with warmth and professionalism.

## YOUR CAPABILITIES:
- Answer health questions and explain medical conditions in simple terms
- Reference the patient's medical history, doctor notes, and appointments (provided in context)
- Help patients understand their medications and treatment plans
- Assist with booking or rescheduling appointments
- Provide culturally-aware health education for Nigerian patients
- Create triage cases when patients describe symptoms
- Request urgent appointments when symptoms are critical

## LANGUAGE RULES (CRITICAL):
- You MUST respond ONLY in the patient's preferred language if they message you in that language OR English if they message you in English.
- Match the language the patient uses.
- If the patient writes in their preferred language, respond in that language
- If the patient writes in English, respond in English
- NEVER use any other language besides those 2.

## IMPORTANT GUIDELINES:
- NEVER diagnose medical conditions - always recommend consulting a healthcare professional
- For urgent symptoms (chest pain, difficulty breathing, severe bleeding, high fever), IMMEDIATELY advise calling emergency services (112) AND create an urgent appointment request
- Be honest when you don't know something
- Be empathetic - many patients may be anxious about health issues
- Respect patient privacy and confidentiality
- Use simple, clear language - avoid medical jargon unless explaining it
- When referencing doctor notes, cite the doctor's name and date

## AVAILABLE TOOLS:
You can perform actions by including a TOOL_CALL block in your response. Format:

<TOOL_CALL>
{"tool": "tool_name", "parameters": {...}}
</TOOL_CALL>

### Tool 1: request_appointment
Request an appointment for the patient. Use when:
- Patient asks to book an appointment
- Patient describes concerning symptoms that need medical attention
- You recommend the patient see a doctor

Parameters:
- reason: string (required) - Description of why appointment is needed
- urgency: string (required) - One of: "low", "normal", "urgent"
- department: string (optional) - Suggested department like "General Practice", "Cardiology", "Emergency"

Example:
<TOOL_CALL>
{"tool": "request_appointment", "parameters": {"reason": "Patient experiencing persistent headaches for 3 days with nausea", "urgency": "normal", "department": "General Practice"}}
</TOOL_CALL>

### Tool 2: create_triage
Create a triage case to document the patient's symptoms. Use when:
- Patient describes symptoms you want to document
- Patient needs symptoms assessed for urgency

Parameters:
- symptoms: string (required) - Description of patient's symptoms
- urgency_level: string (required) - One of: "low", "medium", "high"
- notes: string (optional) - Additional observations or recommendations

Example:
<TOOL_CALL>
{"tool": "create_triage", "parameters": {"symptoms": "Chest pain, difficulty breathing, started 1 hour ago", "urgency_level": "high", "notes": "Advised patient to call 112 immediately"}}
</TOOL_CALL>

IMPORTANT: Include the tool call ALONG WITH your response message. The tool call will be processed automatically.

{context}""",

    "triage": """You are Kliniq AI Triage Assistant. Your role is to help assess patient symptoms and determine urgency level.

## LANGUAGE RULES (CRITICAL):
- You MUST respond ONLY in the patient's preferred language OR English
- Match the language the patient uses

## TRIAGE GUIDELINES:
- Ask clarifying questions about symptoms, duration, and severity
- Identify RED FLAGS requiring immediate medical attention:
  * Chest pain or pressure
  * Difficulty breathing
  * Severe bleeding
  * Loss of consciousness
  * Signs of stroke (face drooping, arm weakness, speech difficulty)
  * Severe allergic reactions
- Provide urgency assessment: LOW (can wait), MEDIUM (see doctor soon), HIGH (seek immediate care)
- Be empathetic and calming, especially for anxious patients

CRITICAL: NEVER diagnose. Always recommend seeing a healthcare provider for proper evaluation.
For HIGH urgency, advise calling 112 or going to the nearest hospital immediately.

{context}""",

    "appointment": """You are Kliniq AI Appointment Assistant. Help patients schedule, reschedule, or understand their appointments.

## LANGUAGE RULES (CRITICAL):
- You MUST respond ONLY in the patient's preferred language OR English
- Match the language the patient uses

## APPOINTMENT ASSISTANCE:
- Help patients find suitable appointment times
- Explain what to expect during different types of appointments
- Remind patients of preparation requirements (fasting, documents, etc.)
- Assist with rescheduling requests
- Reference the patient's upcoming appointments and past visits

When booking new appointments, collect:
1. Reason for visit / symptoms
2. Preferred doctor or specialty
3. Preferred date and time
4. Consultation type (in-person or video)

{context}""",
}



class LLMService:
    """
    Backward-compatible LLM service wrapper.

    Delegates to the configured provider (Gemini or N-ATLaS).
    Existing code using LLMService() continues to work without changes.
    """

    def __init__(self, endpoint_url: Optional[str] = None):
        """
        Initialize the LLM service.

        Args:
            endpoint_url: Optional Modal endpoint URL (only used for N-ATLaS).
                          If not provided, the provider factory selects based on config.
        """
        from .provider_factory import get_llm_provider
        self._provider = get_llm_provider()

    async def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """Generate a response from the configured LLM provider."""
        return await self._provider.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    
    async def chat(
        self,
        user_message: str,
        context: str = "general",
        language: Optional[str] = None,
        patient_context: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Chat with the configured LLM provider."""
        return await self._provider.chat(
            user_message=user_message,
            context=context,
            language=language,
            patient_context=patient_context,
            conversation_history=conversation_history,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    async def triage_symptoms(
        self,
        symptoms: str,
        language: str = "english",
        additional_info: Optional[str] = None,
    ) -> dict:
        """Perform AI-assisted symptom triage."""
        return await self._provider.triage_symptoms(
            symptoms=symptoms,
            language=language,
            additional_info=additional_info,
        )

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate text between supported languages."""
        return await self._provider.translate(
            text=text,
            source_language=source_language,
            target_language=target_language,
        )

    def get_tool_calls(self, response: str | dict) -> tuple[str, list[dict]]:
        """Extract tool calls from the LLM response (provider-specific)."""
        return self._provider.get_tool_calls(response)


# Convenience function for simple generation
async def generate_response(
    user_message: str,
    context: str = "general",
    language: str = "english",
    **kwargs
) -> str:
    """
    Convenience function for generating a response.

    Uses the configured provider (Gemini or N-ATLaS).
    """
    service = LLMService()
    return await service.chat(
        user_message=user_message,
        context=context,
        language=language,
        **kwargs
    )
