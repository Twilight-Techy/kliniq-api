# src/common/llm/__init__.py
"""LLM module — multi-provider architecture for Kliniq AI features."""

from .llm_service import LLMService, generate_response
from .provider_factory import get_llm_provider

__all__ = ["LLMService", "generate_response", "get_llm_provider"]
