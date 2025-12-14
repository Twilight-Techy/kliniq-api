# src/common/llm/translation_service.py
"""Service for translating text between Nigerian languages using N-ATLaS LLM."""

import httpx
from typing import Optional
from src.common.config import settings


LANGUAGE_NAMES = {
    "english": "English",
    "yoruba": "Yoruba",
    "hausa": "Hausa",
    "igbo": "Igbo",
}


async def translate_text(
    text: str,
    source_language: str,
    target_language: str
) -> dict:
    """
    Translate text between Nigerian languages using N-ATLaS LLM.
    
    Args:
        text: The text to translate
        source_language: Source language (english, yoruba, hausa, igbo)
        target_language: Target language (english, yoruba, hausa, igbo)
        
    Returns:
        Dict with 'text' (translated text) and 'error' if any
    """
    # No translation needed if same language
    if source_language.lower() == target_language.lower():
        return {"text": text}
    
    llm_endpoint = settings.MODAL_ENDPOINT_URL
    
    if not llm_endpoint:
        return {
            "error": "LLM endpoint not configured",
            "text": text  # Return original if can't translate
        }
    
    source_name = LANGUAGE_NAMES.get(source_language.lower(), source_language)
    target_name = LANGUAGE_NAMES.get(target_language.lower(), target_language)
    
    # Build translation prompt
    messages = [
        {
            "role": "system",
            "content": f"You are a professional translator specializing in Nigerian languages. Translate the following text from {source_name} to {target_name}. Provide only the translation, no explanations."
        },
        {
            "role": "user", 
            "content": f"Translate this {source_name} text to {target_name}:\n\n{text}"
        }
    ]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                llm_endpoint,
                json={
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.3,  # Lower temp for more accurate translations
                }
            )
            response.raise_for_status()
            result = response.json()
            
            translated_text = result.get("response", "").strip()
            
            if not translated_text:
                return {"error": "Empty translation response", "text": text}
            
            return {"text": translated_text}
            
    except httpx.TimeoutException:
        return {
            "error": "Translation request timed out",
            "text": text
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Translation failed: {e.response.status_code}",
            "text": text
        }
    except Exception as e:
        return {
            "error": f"Translation error: {str(e)}",
            "text": text
        }
