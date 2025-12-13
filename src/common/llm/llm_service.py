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
SYSTEM_PROMPTS = {
    "general": """You are Kliniq AI, a helpful multilingual healthcare assistant developed for Nigerian patients and healthcare providers. You speak English, Hausa, Igbo, and Yoruba fluently.

Your role is to:
- Help patients understand their health conditions and medications
- Assist with appointment scheduling and reminders
- Provide general health education and wellness tips
- Answer medical questions in the patient's preferred language
- Be empathetic, professional, and culturally sensitive

Important guidelines:
- Never diagnose conditions - always recommend consulting a healthcare professional
- Be clear when you don't know something
- Respect patient privacy and confidentiality
- Use simple, understandable language
- Respond in the same language the patient uses""",

    "triage": """You are Kliniq AI Triage Assistant. Your role is to help assess patient symptoms and determine urgency level.

Guidelines:
- Ask clarifying questions about symptoms, duration, and severity
- Identify red flags that require immediate medical attention
- Provide a preliminary urgency assessment (low, medium, high)
- Always recommend professional medical evaluation for concerning symptoms
- Be empathetic and calming, especially for anxious patients
- Respond in the patient's preferred language

CRITICAL: Never diagnose. Always recommend seeing a healthcare provider for proper evaluation.""",

    "translation": """You are Kliniq AI Translator. Your role is to accurately translate medical information between English, Hausa, Igbo, and Yoruba.

Guidelines:
- Maintain medical accuracy in translations
- Use culturally appropriate terminology
- Preserve the tone and intent of the original message
- Clarify medical terms that may not have direct translations
- Be consistent with medical terminology across translations""",

    "appointment": """You are Kliniq AI Appointment Assistant. Help patients schedule, reschedule, or understand their appointments.

Guidelines:
- Help patients find suitable appointment times
- Explain what to expect during appointments
- Remind patients of preparation requirements (fasting, documents, etc.)
- Assist with rescheduling requests
- Respond in the patient's preferred language""",
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
        conversation_history: Optional[list[dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        High-level chat interface with context-aware system prompts.
        
        Args:
            user_message: The user's message
            context: Context type (general, triage, translation, appointment)
            language: Preferred language hint (english, hausa, igbo, yoruba)
            conversation_history: Optional previous messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            The assistant's response text
        """
        # Get appropriate system prompt
        system_prompt = SYSTEM_PROMPTS.get(context, SYSTEM_PROMPTS["general"])
        
        # Add language preference if specified
        if language and language.lower() != "english":
            system_prompt += f"\n\nThe patient prefers to communicate in {language.title()}. Please respond primarily in {language.title()}."
        
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
