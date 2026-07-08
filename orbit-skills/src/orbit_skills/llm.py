"""ORBIT Skills — Minimal LLM client for LM Studio (OpenAI-compatible API).

Not coupled to any specific model. Uses /v1/chat/completions.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from orbit_core.logging import get_logger

_log = get_logger("skills.llm")


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the LLM client."""

    endpoint: str = "http://localhost:1234/v1"
    model: str = "default"
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout_seconds: int = 120


@dataclass(frozen=True)
class LLMResponse:
    """Response from the LLM."""

    content: str
    tokens_sent: int = 0
    tokens_received: int = 0


class LLMClient:
    """Minimal OpenAI-compatible HTTP client for LM Studio.

    Sends synchronous requests to /v1/chat/completions.
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._config = config or LLMConfig()
        self._client = httpx.Client(timeout=self._config.timeout_seconds)

    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        """Send a completion request to the LLM."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        url = f"{self._config.endpoint}/chat/completions"
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }

        _log.info(f"Sending LLM request to {url} (model={self._config.model})")

        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                tokens_sent=usage.get("prompt_tokens", 0),
                tokens_received=usage.get("completion_tokens", 0),
            )
        except httpx.HTTPError as e:
            _log.error(f"LLM request failed: {e}")
            raise

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
