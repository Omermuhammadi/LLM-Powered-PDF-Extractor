"""
LLM client abstraction layer.

Provides a unified interface for both local (Ollama) and
cloud (Groq) LLM inference, with automatic fallback support.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core import (
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
    logger,
)
from app.core.config import get_settings


class LLMMode(str, Enum):
    """LLM inference mode."""

    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""

    content: str
    model: str
    provider: str
    duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "duration_ms": round(self.duration_ms, 2),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate text completion."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        pass

    @abstractmethod
    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Synchronous text generation."""
        pass


class LocalLLMClient(BaseLLMClient):
    """Local LLM client using Ollama."""

    def __init__(self):
        """Initialize local LLM client."""
        from app.services.llm.ollama_client import OllamaClient

        self._client = OllamaClient()
        self.provider = "ollama"

    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        return await self._client.health_check()

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate using Ollama."""
        response = await self._client.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

        return LLMResponse(
            content=response.content,
            model=response.model,
            provider=self.provider,
            duration_ms=response.total_duration_ms,
            prompt_tokens=response.prompt_eval_count,
            completion_tokens=response.eval_count,
            total_tokens=response.prompt_eval_count + response.eval_count,
        )

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Synchronous generation using Ollama."""
        response = self._client.generate_sync(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

        return LLMResponse(
            content=response.content,
            model=response.model,
            provider=self.provider,
            duration_ms=response.total_duration_ms,
            prompt_tokens=response.prompt_eval_count,
            completion_tokens=response.eval_count,
            total_tokens=response.prompt_eval_count + response.eval_count,
        )


class CloudLLMClient(BaseLLMClient):
    """Cloud LLM client using Groq API."""

    def __init__(self):
        """Initialize Groq client."""
        settings = get_settings()

        if not settings.groq_api_key:
            raise LLMError("Groq API key not configured")

        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.timeout = settings.llm_timeout
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.provider = "groq"

        logger.debug(f"CloudLLMClient initialized: model={self.model}")

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate using Groq API."""
        import httpx

        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

        except httpx.ConnectError as e:
            raise LLMConnectionError("api.groq.com", str(e))
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            raise LLMTimeoutError("groq", self.timeout, elapsed)
        except httpx.HTTPStatusError as e:
            # Preserve HTTP status (e.g., 400 vs 429) so retry logic can make
            # an informed decision.
            body = None
            try:
                body = e.response.text
            except Exception:
                body = None
            raise LLMResponseError(f"HTTP {e.response.status_code}", body)
        except Exception as e:
            raise LLMResponseError(str(e))

        elapsed_ms = (time.time() - start_time) * 1000

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            provider=self.provider,
            duration_ms=elapsed_ms,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Synchronous generation using Groq API."""
        import httpx

        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

        except httpx.ConnectError as e:
            raise LLMConnectionError("api.groq.com", str(e))
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            raise LLMTimeoutError("groq", self.timeout, elapsed)
        except httpx.HTTPStatusError as e:
            body = None
            try:
                body = e.response.text
            except Exception:
                body = None
            raise LLMResponseError(f"HTTP {e.response.status_code}", body)
        except Exception as e:
            raise LLMResponseError(str(e))

        elapsed_ms = (time.time() - start_time) * 1000

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            provider=self.provider,
            duration_ms=elapsed_ms,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )


class LLMClient:
    """
    Unified LLM client with automatic mode selection.

    Supports both local (Ollama) and cloud (Groq) inference
    with configurable fallback behavior.
    """

    def __init__(
        self,
        mode: str | LLMMode | None = None,
        fallback_enabled: bool = True,
    ):
        """
        Initialize LLM client.

        Args:
            mode: "local" for Ollama, "cloud" for Groq (default from settings)
            fallback_enabled: If True, fall back to other mode on failure
        """
        settings = get_settings()

        if mode is None:
            mode = settings.llm_mode

        self.mode = LLMMode(mode)
        self.fallback_enabled = fallback_enabled
        self._max_retries = settings.llm_max_retries

        # Initialize primary client
        self._primary: BaseLLMClient | None = None
        self._fallback: BaseLLMClient | None = None

        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize primary and fallback clients."""
        settings = get_settings()

        if self.mode == LLMMode.LOCAL:
            self._primary = LocalLLMClient()
            logger.info(f"LLM mode: LOCAL (Ollama + {settings.ollama_model})")

            if self.fallback_enabled and settings.groq_api_key:
                try:
                    self._fallback = CloudLLMClient()
                    logger.debug("Fallback configured: Groq API")
                except LLMError:
                    pass

        else:  # CLOUD mode
            try:
                self._primary = CloudLLMClient()
                logger.info(f"LLM mode: CLOUD (Groq + {settings.groq_model})")
            except LLMError as e:
                logger.warning(f"Cloud client init failed: {e}")
                # Fall back to local if cloud fails
                if self.fallback_enabled:
                    self._primary = LocalLLMClient()
                    logger.info("Falling back to LOCAL mode")
                else:
                    raise

            if self.fallback_enabled:
                self._fallback = LocalLLMClient()
                logger.debug("Fallback configured: Ollama")

    @property
    def current_mode(self) -> str:
        """Get current LLM mode."""
        return self.mode.value

    @property
    def provider(self) -> str:
        """Get current provider name."""
        return self._primary.provider if self._primary else "unknown"

    async def health_check(self) -> dict[str, Any]:
        """
        Check health of LLM services.

        Returns:
            Dict with health status for primary and fallback
        """
        result = {
            "mode": self.mode.value,
            "primary": {
                "provider": self._primary.provider if self._primary else None,
                "available": False,
            },
            "fallback": {
                "provider": self._fallback.provider if self._fallback else None,
                "available": False,
            },
        }

        if self._primary:
            result["primary"]["available"] = await self._primary.health_check()

        if self._fallback:
            result["fallback"]["available"] = await self._fallback.health_check()

        return result

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate text completion.

        Attempts primary client first, then fallback if enabled.

        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            json_mode: Request JSON output format

        Returns:
            LLMResponse with generated content

        Raises:
            LLMError: If generation fails on all clients
        """
        if not self._primary:
            raise LLMError("No LLM client available")

        last_error: Exception | None = None

        def _is_retryable_error(err: LLMError) -> bool:
            if err.code in {"LLM_TIMEOUT", "LLM_CONNECTION_FAILED"}:
                return True

            if err.code == "LLM_INVALID_RESPONSE":
                reason = (err.details or {}).get("reason", "")
                # Don't retry client/input errors.
                if isinstance(reason, str) and reason.startswith("HTTP "):
                    try:
                        status = int(reason.split(" ", 1)[1])
                    except Exception:
                        return True
                    return status in {408, 429, 500, 502, 503, 504}
                return True

            # Default: retry unknown LLMError types.
            return True

        # Try primary client with retries
        for attempt in range(self._max_retries):
            try:
                return await self._primary.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except LLMError as e:
                last_error = e
                retries = self._max_retries
                logger.warning(
                    f"Primary LLM failed (attempt {attempt + 1}/{retries}): {e}"
                )

                # If we're rate-limited, waiting is the only useful retry.
                if e.code == "LLM_INVALID_RESPONSE":
                    reason = (e.details or {}).get("reason", "")
                    if isinstance(reason, str) and reason.startswith("HTTP "):
                        try:
                            status = int(reason.split(" ", 1)[1])
                        except Exception:
                            status = None
                        if status == 429 and attempt < self._max_retries - 1:
                            wait_s = min(2**attempt, 10)
                            logger.warning(
                                f"Rate limited by provider (HTTP 429). Waiting {wait_s}s before retry..."
                            )
                            await asyncio.sleep(wait_s)

                if not _is_retryable_error(e):
                    break

                if attempt < self._max_retries - 1:
                    continue

        # Try fallback if available
        if self._fallback and self.fallback_enabled:
            logger.info("Attempting fallback LLM...")
            try:
                return await self._fallback.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except LLMError as e:
                logger.error(f"Fallback LLM also failed: {e}")

        # All attempts failed
        raise last_error or LLMError("LLM generation failed")

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Synchronous text generation.

        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            json_mode: Request JSON format

        Returns:
            LLMResponse with generated content
        """
        if not self._primary:
            raise LLMError("No LLM client available")

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                return self._primary.generate_sync(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except LLMError as e:
                last_error = e
                retries = self._max_retries
                logger.warning(
                    f"Primary LLM failed (attempt {attempt + 1}/{retries}): {e}"
                )

                # Back off a bit on rate limits instead of hammering the API.
                if e.code == "LLM_INVALID_RESPONSE":
                    reason = (e.details or {}).get("reason", "")
                    if isinstance(reason, str) and reason.startswith("HTTP "):
                        try:
                            status = int(reason.split(" ", 1)[1])
                        except Exception:
                            status = None
                        if status == 429 and attempt < self._max_retries - 1:
                            wait_s = min(2**attempt, 10)
                            logger.warning(
                                f"Rate limited by provider (HTTP 429). Waiting {wait_s}s before retry..."
                            )
                            time.sleep(wait_s)

                # Same retry rules as async path.
                if e.code == "LLM_INVALID_RESPONSE":
                    reason = (e.details or {}).get("reason", "")
                    if isinstance(reason, str) and reason.startswith("HTTP "):
                        try:
                            status = int(reason.split(" ", 1)[1])
                        except Exception:
                            status = None
                        if status is not None and status in {400, 401, 403, 404}:
                            break

                if attempt < self._max_retries - 1:
                    continue

        if self._fallback and self.fallback_enabled:
            logger.info("Attempting fallback LLM...")
            try:
                return self._fallback.generate_sync(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except LLMError as e:
                logger.error(f"Fallback LLM also failed: {e}")

        raise last_error or LLMError("LLM generation failed")


# Singleton instance for convenience
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create the LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
