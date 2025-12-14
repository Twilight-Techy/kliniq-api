# src/common/llm/transcription_service.py
"""Service for transcribing audio using N-ATLaS ASR."""

import httpx
from typing import Optional
from src.common.config import settings


async def transcribe_audio(
    audio_url: str,
    language: str = "english"
) -> dict:
    """
    Transcribe audio from a URL using N-ATLaS ASR.
    
    Args:
        audio_url: URL to the audio file (e.g., Vercel Blob URL)
        language: Target language (english, yoruba, hausa, igbo)
        
    Returns:
        Dict with 'text' (transcription) and 'error' if any
    """
    asr_endpoint = settings.MODAL_ASR_URL
    
    if not asr_endpoint:
        return {
            "error": "ASR endpoint not configured",
            "text": ""
        }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                asr_endpoint,
                json={
                    "audio_url": audio_url,
                    "language": language
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {
            "error": "Transcription request timed out",
            "text": ""
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Transcription failed: {e.response.status_code}",
            "text": ""
        }
    except Exception as e:
        return {
            "error": f"Transcription error: {str(e)}",
            "text": ""
        }
