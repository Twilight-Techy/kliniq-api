# src/common/llm/stt_provider.py
"""Speech-to-Text providers for audio transcription."""

from abc import ABC, abstractmethod
from typing import Optional

import httpx


# Language locale mapping for Google Cloud Speech-to-Text
GOOGLE_STT_LOCALES = {
    "english": "en-NG",  # Nigerian English
    "yoruba": "yo-NG",
    "hausa": "ha-NG",
    "igbo": "ig-NG",
}


class BaseSTTProvider(ABC):
    """Abstract base for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe_url(
        self,
        audio_url: str,
        language: str = "english",
    ) -> dict:
        """
        Transcribe audio from a URL.

        Args:
            audio_url: URL to the audio file
            language: Target language (english, yoruba, hausa, igbo)

        Returns:
            Dict with 'text' (transcription) and 'error' if any
        """
        ...

    @abstractmethod
    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "english",
    ) -> dict:
        """
        Transcribe audio from raw bytes.

        Args:
            audio_bytes: Raw audio data
            language: Target language

        Returns:
            Dict with 'text' (transcription) and 'error' if any
        """
        ...


class GoogleSTTProvider(BaseSTTProvider):
    """
    Speech-to-Text using Google Cloud Speech-to-Text REST API.

    Supports Nigerian languages: English (en-NG), Hausa (ha-NG),
    Yoruba (yo-NG), Igbo (ig-NG).
    """

    API_URL = "https://speech.googleapis.com/v1/speech:recognize"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def transcribe_url(
        self,
        audio_url: str,
        language: str = "english",
    ) -> dict:
        """Transcribe audio from a URL using Google STT."""
        try:
            # First download the audio
            async with httpx.AsyncClient(timeout=30.0) as client:
                audio_response = await client.get(audio_url)
                audio_response.raise_for_status()
                audio_bytes = audio_response.content

            return await self.transcribe_bytes(audio_bytes, language)

        except httpx.TimeoutException:
            return {"error": "Audio download timed out", "text": ""}
        except httpx.HTTPStatusError as e:
            return {"error": f"Audio download failed: {e.response.status_code}", "text": ""}
        except Exception as e:
            return {"error": f"Transcription error: {str(e)}", "text": ""}

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "english",
    ) -> dict:
        """Transcribe audio bytes using Google Cloud Speech-to-Text REST API."""
        import base64

        locale = GOOGLE_STT_LOCALES.get(language.lower(), "en-NG")

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        request_body = {
            "config": {
                "encoding": "WEBM_OPUS",  # Common format from browser recordings
                "sampleRateHertz": 48000,
                "languageCode": locale,
                "enableAutomaticPunctuation": True,
                "model": "latest_long",
                # Alternative languages for code-switching (common in Nigeria)
                "alternativeLanguageCodes": [
                    lc for lc in GOOGLE_STT_LOCALES.values() if lc != locale
                ],
            },
            "audio": {
                "content": audio_b64,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.API_URL}?key={self.api_key}",
                    json=request_body,
                )
                response.raise_for_status()
                result = response.json()

            # Extract transcription
            results = result.get("results", [])
            if not results:
                return {"text": "", "language": language}

            transcript = " ".join(
                alt["transcript"]
                for r in results
                for alt in r.get("alternatives", [])[:1]
            ).strip()

            return {
                "text": transcript,
                "language": language,
                "model": "google-speech-to-text",
            }

        except httpx.TimeoutException:
            return {"error": "Transcription request timed out", "text": ""}
        except httpx.HTTPStatusError as e:
            return {"error": f"Transcription failed: {e.response.status_code}", "text": ""}
        except Exception as e:
            return {"error": f"Transcription error: {str(e)}", "text": ""}


class NATLaSSTTProvider(BaseSTTProvider):
    """Speech-to-Text using N-ATLaS ASR deployed on Modal."""

    def __init__(self, endpoint_url: str):
        if not endpoint_url:
            raise ValueError(
                "MODAL_ASR_URL not configured. "
                "Set it in settings when using LLM_PROVIDER=natlas."
            )
        self.endpoint_url = endpoint_url

    async def transcribe_url(
        self,
        audio_url: str,
        language: str = "english",
    ) -> dict:
        """Transcribe audio from URL using N-ATLaS Modal ASR."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint_url,
                    json={
                        "audio_url": audio_url,
                        "language": language,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            return {"error": "Transcription request timed out", "text": ""}
        except httpx.HTTPStatusError as e:
            return {"error": f"Transcription failed: {e.response.status_code}", "text": ""}
        except Exception as e:
            return {"error": f"Transcription error: {str(e)}", "text": ""}

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "english",
    ) -> dict:
        """
        N-ATLaS ASR currently only supports URL-based transcription.
        This method returns an error for direct byte input.
        """
        return {
            "error": "N-ATLaS ASR only supports URL-based transcription. "
                     "Upload the audio first and provide a URL.",
            "text": "",
        }
