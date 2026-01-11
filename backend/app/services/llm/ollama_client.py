"""
Ollama client for local LLM inference.

Provides direct integration with Ollama API for running
Phi-3 Mini and other local models.
"""

import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core import LLMConnectionError, LLMResponseError, LLMTimeoutError, logger
from app.core.config import get_settings


@dataclass
class OllamaResponse:
    """Response from Ollama API."""

    content: str
    model: str
    total_duration_ms: float
    prompt_eval_count: int
    eval_count: int
    tokens_per_second: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "prompt_eval_count": self.prompt_eval_count,
            "eval_count": self.eval_count,
            "tokens_per_second": round(self.tokens_per_second, 2),
        }


class OllamaClient:
    """
    Client for Ollama local LLM inference.

    Handles communication with Ollama API for text generation
    using models like Phi-3 Mini.
    """

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        """
        Initialize Ollama client.

        Args:
            host: Ollama API host URL (default from settings)
            model: Model name to use (default from settings)
            timeout: Request timeout in seconds (default from settings)
        """
        settings = get_settings()

        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout

        # API endpoints
        self.generate_url = f"{self.host}/api/generate"
        self.tags_url = f"{self.host}/api/tags"

        logger.debug(f"OllamaClient initialized: host={self.host}, model={self.model}")

    async def health_check(self) -> bool:
        """
        Check if Ollama service is available.

        Returns:
            True if Ollama is running and accessible
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.tags_url)
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except httpx.ConnectError:
            raise LLMConnectionError("ollama", self.host)
        except Exception as e:
            raise LLMResponseError("ollama", f"Failed to list models: {e}")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stop: list[str] | None = None,
        json_mode: bool = False,
    ) -> OllamaResponse:
        """
        Generate text completion using Ollama.

        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0, lower = more focused)
            max_tokens: Maximum tokens to generate
            stop: Stop sequences to halt generation
            json_mode: If True, request JSON output format

        Returns:
            OllamaResponse with generated content and metrics

        Raises:
            LLMConnectionError: If cannot connect to Ollama
            LLMTimeoutError: If request times out
            LLMResponseError: If response is invalid
        """
        logger.step(1, 3, f"Sending prompt to {self.model}")

        # Build request payload
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        if stop:
            payload["options"]["stop"] = stop

        if json_mode:
            payload["format"] = "json"

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.step(2, 3, "Waiting for LLM response...")

                response = await client.post(
                    self.generate_url,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()

        except httpx.ConnectError:
            raise LLMConnectionError("ollama", self.host)
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            raise LLMTimeoutError("ollama", self.timeout, elapsed)
        except httpx.HTTPStatusError as e:
            raise LLMResponseError("ollama", f"HTTP {e.response.status_code}")
        except Exception as e:
            raise LLMResponseError("ollama", str(e))

        logger.step(3, 3, "Processing response")

        # Parse response
        content = data.get("response", "").strip()

        if not content:
            raise LLMResponseError("ollama", "Empty response from model")

        # Extract metrics (Ollama returns durations in nanoseconds)
        total_duration_ns = data.get("total_duration", 0)
        total_duration_ms = total_duration_ns / 1_000_000

        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        # Calculate tokens per second
        eval_duration_ns = data.get("eval_duration", 1)
        tokens_per_second = (eval_count / eval_duration_ns) * 1_000_000_000

        result = OllamaResponse(
            content=content,
            model=data.get("model", self.model),
            total_duration_ms=total_duration_ms,
            prompt_eval_count=prompt_eval_count,
            eval_count=eval_count,
            tokens_per_second=tokens_per_second,
        )

        logger.success(
            f"Generated {eval_count} tokens in {total_duration_ms:.0f}ms "
            f"({tokens_per_second:.1f} tok/s)"
        )

        return result

    async def generate_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> OllamaResponse:
        """
        Generate JSON-formatted response.

        Convenience method that enables JSON mode for structured output.

        Args:
            prompt: The prompt (should request JSON output)
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            OllamaResponse with JSON content
        """
        return await self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        stop: list[str] | None = None,
        json_mode: bool = False,
    ) -> OllamaResponse:
        """
        Synchronous version of generate() for non-async contexts.

        Args:
            prompt: The prompt to send
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            stop: Stop sequences
            json_mode: Request JSON output

        Returns:
            OllamaResponse with generated content
        """
        logger.step(1, 3, f"Sending prompt to {self.model} (sync)")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        if stop:
            payload["options"]["stop"] = stop

        if json_mode:
            payload["format"] = "json"

        start_time = time.time()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                logger.step(2, 3, "Waiting for LLM response...")

                response = client.post(
                    self.generate_url,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()

        except httpx.ConnectError:
            raise LLMConnectionError("ollama", self.host)
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            raise LLMTimeoutError("ollama", self.timeout, elapsed)
        except httpx.HTTPStatusError as e:
            raise LLMResponseError("ollama", f"HTTP {e.response.status_code}")
        except Exception as e:
            raise LLMResponseError("ollama", str(e))

        logger.step(3, 3, "Processing response")

        content = data.get("response", "").strip()

        if not content:
            raise LLMResponseError("ollama", "Empty response from model")

        total_duration_ns = data.get("total_duration", 0)
        total_duration_ms = total_duration_ns / 1_000_000

        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        eval_duration_ns = data.get("eval_duration", 1)
        tokens_per_second = (eval_count / eval_duration_ns) * 1_000_000_000

        result = OllamaResponse(
            content=content,
            model=data.get("model", self.model),
            total_duration_ms=total_duration_ms,
            prompt_eval_count=prompt_eval_count,
            eval_count=eval_count,
            tokens_per_second=tokens_per_second,
        )

        logger.success(
            f"Generated {eval_count} tokens in {total_duration_ms:.0f}ms "
            f"({tokens_per_second:.1f} tok/s)"
        )

        return result
