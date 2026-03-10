# src/common/llm/transcription_service.py
"""Service for transcribing audio — routes through the configured STT provider."""

from typing import Optional


async def transcribe_audio(
    audio_url: str,
    language: str = "english"
) -> dict:
    """
    Transcribe audio from a URL using the configured STT provider.

    Automatically selects Google Cloud STT or N-ATLaS ASR based on
    the LLM_PROVIDER setting.

    Args:
        audio_url: URL to the audio file (e.g., Vercel Blob URL)
        language: Target language (english, yoruba, hausa, igbo)

    Returns:
        Dict with 'text' (transcription) and 'error' if any
    """
    from .provider_factory import get_stt_provider

    try:
        provider = get_stt_provider()
        return await provider.transcribe_url(audio_url, language)
    except Exception as e:
        return {
            "error": f"Transcription error: {str(e)}",
            "text": ""
        }
