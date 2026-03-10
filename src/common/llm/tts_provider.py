# src/common/llm/tts_provider.py
"""Text-to-Speech providers for audio synthesis."""

from abc import ABC, abstractmethod

import httpx


# Language voice mapping for Google Cloud TTS
# Nigerian English has good support; local languages use best available
GOOGLE_TTS_VOICES = {
    "english": {"language_code": "en-NG", "name": "en-NG-Standard-A"},
    "yoruba": {"language_code": "en-NG", "name": "en-NG-Standard-A"},  # Fallback to en-NG
    "hausa": {"language_code": "en-NG", "name": "en-NG-Standard-A"},   # Fallback to en-NG
    "igbo": {"language_code": "en-NG", "name": "en-NG-Standard-A"},    # Fallback to en-NG
}


class BaseTTSProvider(ABC):
    """Abstract base for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "english",
    ) -> dict:
        """
        Synthesize speech from text.

        Args:
            text: Text to convert to speech
            language: Target language

        Returns:
            Dict with 'audio_content' (base64 encoded audio) and metadata
        """
        ...


class GoogleTTSProvider(BaseTTSProvider):
    """
    Text-to-Speech using Google Cloud TTS REST API.

    Currently supports Nigerian English voice. For Hausa, Yoruba, and Igbo,
    falls back to Nigerian English voice until native voices are available.
    """

    API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def synthesize(
        self,
        text: str,
        language: str = "english",
    ) -> dict:
        """Synthesize speech using Google Cloud TTS."""
        voice_config = GOOGLE_TTS_VOICES.get(language.lower(), GOOGLE_TTS_VOICES["english"])

        request_body = {
            "input": {"text": text},
            "voice": {
                "languageCode": voice_config["language_code"],
                "name": voice_config["name"],
                "ssmlGender": "FEMALE",
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,
                "pitch": 0.0,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_URL}?key={self.api_key}",
                    json=request_body,
                )
                response.raise_for_status()
                result = response.json()

            return {
                "audio_content": result.get("audioContent", ""),
                "language": language,
                "voice": voice_config["name"],
                "encoding": "MP3",
                "model": "google-cloud-tts",
            }

        except httpx.TimeoutException:
            return {"error": "TTS request timed out", "audio_content": ""}
        except httpx.HTTPStatusError as e:
            return {"error": f"TTS failed: {e.response.status_code}", "audio_content": ""}
        except Exception as e:
            return {"error": f"TTS error: {str(e)}", "audio_content": ""}
