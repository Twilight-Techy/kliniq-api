# src/common/llm/modal_asr.py
"""
Modal deployment for N-ATLaS ASR (Automatic Speech Recognition).

Deploy with:
    modal deploy src/common/llm/modal_asr.py

Supported languages:
- Nigerian English (default)
- Yoruba
- Hausa
- Igbo
"""

import modal

# Modal app for ASR
app = modal.App("natlas-asr")

# Model mapping
ASR_MODELS = {
    "english": "NCAIR1/NigerianAccentedEnglish",
    "yoruba": "NCAIR1/Yoruba-ASR",
    "hausa": "NCAIR1/Hausa-ASR",
    "igbo": "NCAIR1/Igbo-ASR",
}

# Default to Nigerian English
DEFAULT_MODEL = "NCAIR1/NigerianAccentedEnglish"

# Volume to cache models
model_volume = modal.Volume.from_name("natlas-asr-cache", create_if_missing=True)
MODEL_DIR = "/models"


def download_asr_models():
    """Download all ASR models during image build."""
    import os
    from huggingface_hub import snapshot_download
    
    hf_token = os.environ.get("HF_TOKEN")
    
    for lang, model_id in ASR_MODELS.items():
        print(f"Downloading {model_id}...")
        snapshot_download(
            model_id,
            local_dir=f"{MODEL_DIR}/{model_id}",
            token=hf_token,
        )


# Container image with ASR dependencies
asr_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")  # For audio processing
    .pip_install(
        "torch",
        "torchaudio", 
        "transformers",
        "librosa",
        "huggingface_hub",
        "fastapi",
        "soundfile",
        "httpx",
    )
    .run_function(
        download_asr_models,
        volumes={MODEL_DIR: model_volume},
        secrets=[modal.Secret.from_name("huggingface")],
    )
)


@app.cls(
    gpu="T4",  # T4 is sufficient for Whisper-small
    image=asr_image,
    volumes={MODEL_DIR: model_volume},
    scaledown_window=300,
    timeout=120,
)
class NATLaSASR:
    """N-ATLaS ASR for Nigerian languages."""
    
    @modal.enter()
    def load_models(self):
        """Load default model on startup."""
        from transformers import pipeline
        
        # Load Nigerian English as default
        self.pipelines = {}
        self.pipelines["english"] = pipeline(
            "automatic-speech-recognition",
            model=f"{MODEL_DIR}/{DEFAULT_MODEL}",
            device="cuda",
        )
    
    def _get_pipeline(self, language: str):
        """Get or load pipeline for a language."""
        from transformers import pipeline
        
        lang = language.lower()
        if lang not in ASR_MODELS:
            lang = "english"
        
        if lang not in self.pipelines:
            model_path = f"{MODEL_DIR}/{ASR_MODELS[lang]}"
            self.pipelines[lang] = pipeline(
                "automatic-speech-recognition",
                model=model_path,
                device="cuda",
            )
        
        return self.pipelines[lang]
    
    @modal.method()
    def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "english",
    ) -> dict:
        """
        Transcribe audio to text.
        
        Args:
            audio_bytes: Raw audio bytes (wav, mp3, webm, etc.)
            language: Target language (english, yoruba, hausa, igbo)
            
        Returns:
            Dict with transcription and metadata
        """
        import librosa
        import io
        import soundfile as sf
        import numpy as np
        import subprocess
        import tempfile
        import os
        
        # First try to read directly with soundfile (works for wav, flac, ogg)
        try:
            audio, sr = sf.read(io.BytesIO(audio_bytes))
        except Exception:
            # If direct read fails, use ffmpeg to convert to wav
            try:
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
                    input_file.write(audio_bytes)
                    input_path = input_file.name
                
                output_path = input_path.replace(".webm", ".wav")
                
                # Use ffmpeg to convert to wav
                result = subprocess.run([
                    "ffmpeg", "-y", "-i", input_path,
                    "-ar", "16000",  # Resample to 16kHz
                    "-ac", "1",      # Mono
                    "-f", "wav",
                    output_path
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    os.unlink(input_path)
                    return {"error": f"FFmpeg conversion failed: {result.stderr}", "text": ""}
                
                # Read the converted wav file
                audio, sr = sf.read(output_path)
                
                # Cleanup temp files
                os.unlink(input_path)
                os.unlink(output_path)
                
            except Exception as e:
                return {"error": f"Failed to load audio: {str(e)}", "text": ""}
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Resample to 16kHz if needed
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        
        # Get pipeline for language
        pipe = self._get_pipeline(language)
        
        # Transcribe
        result = pipe(audio)
        
        return {
            "text": result["text"].strip(),
            "language": language,
            "model": ASR_MODELS.get(language.lower(), DEFAULT_MODEL),
        }
    
    @modal.method()
    def health_check(self) -> dict:
        """Health check."""
        return {
            "status": "healthy",
            "models": list(ASR_MODELS.keys()),
        }


# HTTP endpoint for transcription
@app.function(
    image=asr_image,
    timeout=120,
)
@modal.fastapi_endpoint(method="POST", docs=True)
async def transcribe_endpoint(request: dict) -> dict:
    """
    HTTP endpoint for audio transcription.
    
    Request body:
    {
        "audio_url": "https://...",  // URL to audio file
        "language": "english"  // optional: english, yoruba, hausa, igbo
    }
    """
    import httpx
    
    audio_url = request.get("audio_url")
    language = request.get("language", "english")
    
    if not audio_url:
        return {"error": "No audio_url provided", "text": ""}
    
    # Fetch audio from URL
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url, timeout=30.0)
            response.raise_for_status()
            audio_bytes = response.content
    except Exception as e:
        return {"error": f"Failed to fetch audio: {str(e)}", "text": ""}
    
    # Transcribe
    asr = NATLaSASR()
    result = asr.transcribe.remote(audio_bytes=audio_bytes, language=language)
    
    return result


# Health check
@app.function(image=modal.Image.debian_slim().pip_install("fastapi"))
@modal.fastapi_endpoint(method="GET")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "models": list(ASR_MODELS.keys())}


# Local testing
@app.local_entrypoint()
def main():
    """Test ASR locally."""
    print("N-ATLaS ASR is ready!")
    print("Available models:", list(ASR_MODELS.keys()))
