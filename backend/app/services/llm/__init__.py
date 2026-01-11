"""
LLM services module.

Provides LLM client abstraction for both local (Ollama)
and cloud (Groq) inference, plus prompt engineering and response parsing.
"""

from app.services.llm.client import LLMClient, LLMMode, LLMResponse, get_llm_client
from app.services.llm.ollama_client import OllamaClient, OllamaResponse
from app.services.llm.parser import (
    ParseResult,
    clean_extracted_data,
    parse_llm_response,
    validate_extracted_fields,
)
from app.services.llm.prompts import (
    PromptTemplate,
    format_extraction_prompt,
    get_prompt_for_type,
)

__all__ = [
    # Client abstraction
    "LLMClient",
    "LLMMode",
    "LLMResponse",
    "get_llm_client",
    # Ollama direct
    "OllamaClient",
    "OllamaResponse",
    # Prompt engineering
    "PromptTemplate",
    "get_prompt_for_type",
    "format_extraction_prompt",
    # Response parsing
    "ParseResult",
    "parse_llm_response",
    "validate_extracted_fields",
    "clean_extracted_data",
]
