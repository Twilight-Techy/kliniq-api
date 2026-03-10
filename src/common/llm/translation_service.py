# src/common/llm/translation_service.py
"""Service for translating text — routes through the configured LLM provider."""


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
    Translate text between Nigerian languages using the configured LLM provider.

    Automatically selects Gemini or N-ATLaS based on the LLM_PROVIDER setting.

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

    from .provider_factory import get_llm_provider

    source_name = LANGUAGE_NAMES.get(source_language.lower(), source_language)
    target_name = LANGUAGE_NAMES.get(target_language.lower(), target_language)

    try:
        provider = get_llm_provider()
        translated = await provider.translate(
            text=text,
            source_language=source_name,
            target_language=target_name,
        )

        if not translated:
            return {"error": "Empty translation response", "text": text}

        return {"text": translated}

    except Exception as e:
        return {
            "error": f"Translation error: {str(e)}",
            "text": text  # Return original if can't translate
        }
