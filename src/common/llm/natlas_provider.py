# src/common/llm/natlas_provider.py
"""N-ATLaS LLM provider using Modal endpoint."""

import httpx
from typing import Optional
from datetime import datetime

from .base_provider import BaseLLMProvider
from .llm_service import SYSTEM_PROMPTS
from .tool_executor import parse_tool_calls


class NATLaSProvider(BaseLLMProvider):
    """LLM provider using the N-ATLaS model deployed on Modal with vLLM."""

    def __init__(self, endpoint_url: str):
        """
        Initialize the N-ATLaS provider.

        Args:
            endpoint_url: Modal endpoint URL for the N-ATLaS model
        """
        if not endpoint_url:
            raise ValueError(
                "Modal endpoint URL not configured. "
                "Set MODAL_ENDPOINT_URL in settings when using LLM_PROVIDER=natlas."
            )
        self.endpoint_url = endpoint_url
        self.timeout = 120.0

    def _build_system_prompt(
        self,
        context: str,
        language: Optional[str] = None,
        patient_context: Optional[str] = None,
    ) -> str:
        """Build system prompt with context injection (keeps inline tool docs)."""
        system_prompt = SYSTEM_PROMPTS.get(context, SYSTEM_PROMPTS["general"])

        # Inject patient context
        context_section = ""
        if patient_context:
            context_section = f"\n## PATIENT INFORMATION:\n{patient_context}"
        system_prompt = system_prompt.replace("{context}", context_section)

        # Add language preference
        if language and language.lower() != "english":
            system_prompt += (
                f"\n\n## PATIENT'S PREFERRED LANGUAGE: {language.title()}\n"
                f"The patient prefers {language.title()}. Respond in {language.title()} "
                f"when they write in that language, or in English if they write in English. "
                f"Do not respond in any other language besides those 2."
            )
        else:
            system_prompt += (
                "\n\n## PATIENT'S PREFERRED LANGUAGE: English\n"
                "Respond in English. Do not respond in any other language besides English."
            )

        return system_prompt

    async def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """Generate a response from the N-ATLaS Modal endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoint_url,
                json={
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                },
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
        """Chat with N-ATLaS via Modal endpoint."""
        system_prompt = self._build_system_prompt(context, language, patient_context)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

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
        """Perform AI-assisted symptom triage using N-ATLaS."""
        prompt = f"Patient symptoms: {symptoms}"
        if additional_info:
            prompt += f"\nAdditional information: {additional_info}"
        prompt += "\n\nPlease provide: 1) Brief symptom assessment 2) Urgency level (low/medium/high) 3) Recommended next steps"

        response = await self.chat(
            user_message=prompt,
            context="triage",
            language=language,
            temperature=0.3,
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
        """Translate text using N-ATLaS."""
        if source_language.lower() == target_language.lower():
            return text

        prompt = (
            f"Translate the following from {source_language} to {target_language}. "
            f"Provide only the translation, no explanations:\n\n{text}"
        )

        return await self.chat(
            user_message=prompt,
            context="translation",
            temperature=0.3,
            max_tokens=2048,
        )

    def get_tool_calls(self, response: str | dict) -> tuple[str, list[dict]]:
        """
        Extract tool calls from N-ATLaS's <TOOL_CALL> blocks via regex.

        N-ATLaS relies on text-based tool calling with XML-like delimiters.
        """
        text = response if isinstance(response, str) else str(response)
        return parse_tool_calls(text)
