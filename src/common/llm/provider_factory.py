# src/common/llm/provider_factory.py
"""Factory for creating LLM, STT, and TTS providers based on config."""

from src.common.config import settings

from .base_provider import BaseLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Create and return the configured LLM provider.

    Selection is based on the LLM_PROVIDER environment variable:
    - "gemini" (default): Uses Google Gemini 2.5 Flash with native function calling
    - "natlas": Uses the N-ATLaS model via Modal endpoint

    Returns:
        An instance of BaseLLMProvider
    """
    provider_name = getattr(settings, "LLM_PROVIDER", "gemini").lower()

    if provider_name == "gemini":
        from .gemini_provider import GeminiProvider

        api_key = getattr(settings, "GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required when LLM_PROVIDER=gemini. "
                "Set it in your .env file."
            )
        return GeminiProvider(api_key=api_key)

    elif provider_name == "natlas":
        from .natlas_provider import NATLaSProvider

        endpoint_url = getattr(settings, "MODAL_ENDPOINT_URL", "")
        return NATLaSProvider(endpoint_url=endpoint_url)

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider_name}'. "
            f"Supported values: 'gemini', 'natlas'"
        )


def get_stt_provider():
    """
    Create and return the configured STT (Speech-to-Text) provider.

    Selection is based on the LLM_PROVIDER environment variable:
    - "gemini" (default): Uses Google Cloud Speech-to-Text
    - "natlas": Uses N-ATLaS ASR via Modal endpoint
    """
    provider_name = getattr(settings, "LLM_PROVIDER", "gemini").lower()

    if provider_name == "gemini":
        from .stt_provider import GoogleSTTProvider

        api_key = getattr(settings, "GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for Google STT. "
                "Set it in your .env file."
            )
        return GoogleSTTProvider(api_key=api_key)

    elif provider_name == "natlas":
        from .stt_provider import NATLaSSTTProvider

        asr_url = getattr(settings, "MODAL_ASR_URL", "")
        return NATLaSSTTProvider(endpoint_url=asr_url)

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER for STT: '{provider_name}'. "
            f"Supported values: 'gemini', 'natlas'"
        )


def get_tts_provider():
    """
    Create and return the configured TTS (Text-to-Speech) provider.

    Currently only Google Cloud TTS is supported.
    """
    from .tts_provider import GoogleTTSProvider

    api_key = getattr(settings, "GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is required for Google TTS. "
            "Set it in your .env file."
        )
    return GoogleTTSProvider(api_key=api_key)
