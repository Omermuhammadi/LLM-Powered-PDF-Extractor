"""
LLM services module.

Provides LLM client abstraction for both local (Ollama)
and cloud (Groq) inference.
"""

from app.services.llm.client import LLMClient, LLMMode, LLMResponse, get_llm_client
from app.services.llm.ollama_client import OllamaClient, OllamaResponse

__all__ = [
    # Client abstraction
    "LLMClient",
    "LLMMode",
    "LLMResponse",
    "get_llm_client",
    # Ollama direct
    "OllamaClient",
    "OllamaResponse",
]
