"""Abstract LLM provider interface + factory."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pain_radar.core.config import Settings


class LLMProvider(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Return text completion from the model."""
        ...

    async def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 8192,
    ) -> Any:
        """Return parsed JSON from the model.

        The system prompt should instruct the model to output valid JSON.
        """
        raw = await self.complete(system, messages, temperature, max_tokens)
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)


def create_provider(settings: Settings) -> LLMProvider:
    """Factory: create LLM provider from settings."""
    if settings.llm_provider == "claude":
        from pain_radar.llm.claude import ClaudeProvider
        return ClaudeProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )
    elif settings.llm_provider == "openai":
        from pain_radar.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
