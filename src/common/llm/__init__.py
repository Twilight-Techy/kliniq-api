# src/common/llm/__init__.py
"""LLM module for N-ATLaS multilingual model integration."""

from .llm_service import LLMService, generate_response

__all__ = ["LLMService", "generate_response"]
