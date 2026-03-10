# src/common/llm/base_provider.py
"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers (Gemini, N-ATLaS, etc.)."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """
        Generate a raw response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter

        Returns:
            Dict with 'response', 'usage', and 'model' keys
        """
        ...

    @abstractmethod
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
            language: Preferred language hint
            patient_context: Additional context like doctor notes, appointments
            conversation_history: Optional previous messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            The assistant's response text
        """
        ...

    @abstractmethod
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
            Dict with 'assessment', 'language', and 'timestamp'
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def get_tool_calls(self, response: str | dict) -> tuple[str, list[dict]]:
        """
        Extract tool calls from the LLM response.

        Each provider parses tool calls differently:
        - N-ATLaS: regex parsing of <TOOL_CALL> blocks from text
        - Gemini: native function_call objects from API response

        Args:
            response: The raw LLM response (string for N-ATLaS, dict for Gemini)

        Returns:
            Tuple of (cleaned_response_text, list_of_tool_call_dicts)
            Each tool call dict has: {"tool": "name", "parameters": {...}}
        """
        ...
