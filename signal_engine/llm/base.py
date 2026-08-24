"""LLM provider abstraction. The engine is fully useful with no key."""

from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    """Minimal chat-completion interface — three LLM roles, three methods."""

    name: str

    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 600,
    ) -> str: ...


class NullProvider:
    """No LLM available. Returns an explicit note so callers degrade visibly."""

    name = "null"

    def complete(self, system: str, user: str, max_tokens: int = 600) -> str:
        return "_(LLM disabled — no API key configured. Add one to enable.)_"


def make_provider(settings) -> Provider:
    """Return the right provider for the configured keys.

    Priority: Anthropic if key present, else any OpenAI-compatible endpoint
    with a key, else NullProvider.
    """
    if getattr(settings, "anthropic_api_key", ""):
        from signal_engine.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=getattr(settings, "model_writing", "claude-sonnet-5"),
        )
    if getattr(settings, "openai_api_key", "") and getattr(settings, "openai_base_url", ""):
        from signal_engine.llm.openai_compat import OpenAICompatProvider

        return OpenAICompatProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=getattr(settings, "model_scoring", "claude-haiku-4-5-20251001"),
        )
    return NullProvider()
