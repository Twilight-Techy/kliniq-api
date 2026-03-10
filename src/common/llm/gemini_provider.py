# src/common/llm/gemini_provider.py
"""Gemini LLM provider using google-genai SDK."""

from typing import Optional
from datetime import datetime

from google import genai
from google.genai import types

from .base_provider import BaseLLMProvider
from .llm_service import SYSTEM_PROMPTS
from .tool_declarations import GEMINI_TOOL_DECLARATIONS

# Gemini-specific system prompts: same content but WITHOUT the
# inline AVAILABLE TOOLS section (tools are declared natively).
# We strip the tool documentation block from the general prompt.
TOOL_DOCS_START = "## AVAILABLE TOOLS:"
TOOL_DOCS_END = "{context}"


def _strip_tool_docs(prompt: str) -> str:
    """Remove inline tool documentation from system prompt."""
    start_idx = prompt.find(TOOL_DOCS_START)
    if start_idx == -1:
        return prompt
    end_idx = prompt.find(TOOL_DOCS_END, start_idx)
    if end_idx == -1:
        return prompt
    return prompt[:start_idx] + prompt[end_idx:]


class GeminiProvider(BaseLLMProvider):
    """LLM provider using Google Gemini API with native function calling."""

    MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Google API key for Gemini
        """
        self.client = genai.Client(api_key=api_key)

    def _build_system_prompt(
        self,
        context: str,
        language: Optional[str] = None,
        patient_context: Optional[str] = None,
    ) -> str:
        """Build system prompt with context injection."""
        system_prompt = SYSTEM_PROMPTS.get(context, SYSTEM_PROMPTS["general"])

        # Strip inline tool docs for Gemini (tools are declared natively)
        if context == "general":
            system_prompt = _strip_tool_docs(system_prompt)

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
        """Generate a response using Gemini API."""
        # Separate system message from the rest
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "assistant":
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=content)],
                    )
                )
            else:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        response = await self.client.aio.models.generate_content(
            model=self.MODEL,
            contents=contents,
            config=config,
        )

        response_text = response.text or ""

        return {
            "response": response_text,
            "usage": {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            },
            "model": self.MODEL,
        }

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
        """Chat with Gemini using native function calling for the general context."""
        system_prompt = self._build_system_prompt(context, language, patient_context)

        # Build contents
        contents = []

        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                gemini_role = "model" if role == "assistant" else "user"
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        # Use function calling for general/triage contexts
        tools = None
        if context in ("general", "triage"):
            tools = [GEMINI_TOOL_DECLARATIONS]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
        )

        response = await self.client.aio.models.generate_content(
            model=self.MODEL,
            contents=contents,
            config=config,
        )

        # Store the raw response for tool call extraction
        self._last_response = response

        return response.text or ""

    async def triage_symptoms(
        self,
        symptoms: str,
        language: str = "english",
        additional_info: Optional[str] = None,
    ) -> dict:
        """Perform AI-assisted symptom triage using Gemini."""
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
        """Translate text using Gemini."""
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
        Extract tool calls from Gemini's native function calling response.

        Gemini returns function calls as structured objects in the response,
        not as text blocks that need regex parsing.
        """
        tool_calls = []

        # Check the last stored response for function calls
        last_response = getattr(self, "_last_response", None)
        if last_response and last_response.candidates:
            for candidate in last_response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.function_call:
                            fc = part.function_call
                            tool_calls.append({
                                "tool": fc.name,
                                "parameters": dict(fc.args) if fc.args else {},
                            })

        # The text response is already clean (no TOOL_CALL blocks to strip)
        cleaned_text = response if isinstance(response, str) else str(response)

        return cleaned_text, tool_calls
