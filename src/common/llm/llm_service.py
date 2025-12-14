# src/common/llm/llm_service.py
"""
LLM Service for calling the N-ATLaS Modal endpoint.

This service provides a simple interface for the backend to call
the deployed N-ATLaS model for multilingual AI features.
"""

import httpx
from typing import Optional
from datetime import datetime

from src.common.config import settings


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
- You MUST respond ONLY in the patient's preferred language OR English
- If the patient writes in their preferred language, respond in that language
- If the patient writes in English, respond in English
- NEVER use any other language besides the patient's preferred language or English
- When greeting, use culturally appropriate greetings for the patient's language

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
    """Service for interacting with the N-ATLaS LLM deployed on Modal."""
    
    def __init__(self, endpoint_url: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            endpoint_url: Modal endpoint URL. Defaults to settings.MODAL_ENDPOINT_URL
        """
        self.endpoint_url = endpoint_url or getattr(settings, 'MODAL_ENDPOINT_URL', None)
        self.timeout = 120.0  # 2 minute timeout for generation
        
    async def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            
        Returns:
            Dict with 'response', 'usage', and 'model' keys
        """
        if not self.endpoint_url:
            raise ValueError("Modal endpoint URL not configured. Set MODAL_ENDPOINT_URL in settings.")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoint_url,
                json={
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                }
            )
            response.raise_for_status()
            return response.json()
    
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
        """
        High-level chat interface with context-aware system prompts.
        
        Args:
            user_message: The user's message
            context: Context type (general, triage, appointment)
            language: Preferred language hint (english, hausa, igbo, yoruba)
            patient_context: Additional context like doctor notes, appointments
            conversation_history: Optional previous messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            The assistant's response text
        """
        # Get appropriate system prompt
        system_prompt = SYSTEM_PROMPTS.get(context, SYSTEM_PROMPTS["general"])
        
        # Inject patient context (doctor notes, appointments, etc.)
        context_section = ""
        if patient_context:
            context_section = f"\n## PATIENT INFORMATION:\n{patient_context}"
        system_prompt = system_prompt.replace("{context}", context_section)
        
        # Add language preference
        if language and language.lower() != "english":
            system_prompt += f"\n\n## PATIENT'S PREFERRED LANGUAGE: {language.title()}\nThe patient prefers {language.title()}. Respond in {language.title()} when they write in that language, or in English if they write in English. Do not respond in any other language besides those 2."
        else:
            system_prompt += "\n\n## PATIENT'S PREFERRED LANGUAGE: English\nRespond in English. Do not respond in any other language besides English."
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        result = await self.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return result.get("response", "")
    
    async def triage_symptoms(
        self,
        symptoms: str,
        language: str = "english",
        additional_info: Optional[str] = None,
    ) -> dict:
        """
        Perform AI-assisted symptom triage.
        
        Args:
            symptoms: Patient's described symptoms
            language: Patient's preferred language
            additional_info: Any additional context
            
        Returns:
            Dict with 'assessment', 'urgency', and 'recommendations'
        """
        prompt = f"Patient symptoms: {symptoms}"
        if additional_info:
            prompt += f"\nAdditional information: {additional_info}"
        prompt += "\n\nPlease provide: 1) Brief symptom assessment 2) Urgency level (low/medium/high) 3) Recommended next steps"
        
        response = await self.chat(
            user_message=prompt,
            context="triage",
            language=language,
            temperature=0.3,  # Lower temperature for more consistent assessments
        )
        
        return {
            "assessment": response,
            "language": language,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate text between supported languages.
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            
        Returns:
            Translated text
        """
        prompt = f"Translate the following from {source_language} to {target_language}:\n\n{text}"
        
        return await self.chat(
            user_message=prompt,
            context="translation",
            temperature=0.3,  # Lower temperature for accurate translation
            max_tokens=2048,
        )


# Convenience function for simple generation
async def generate_response(
    user_message: str,
    context: str = "general",
    language: str = "english",
    **kwargs
) -> str:
    """
    Convenience function for generating a response.
    
    Args:
        user_message: The user's message
        context: Context type (general, triage, translation, appointment)
        language: Preferred language
        **kwargs: Additional arguments passed to LLMService.chat()
        
    Returns:
        The assistant's response text
    """
    service = LLMService()
    return await service.chat(
        user_message=user_message,
        context=context,
        language=language,
        **kwargs
    )
