"""Anthropic provider using the messages API."""

from __future__ import annotations

import time


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5") -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            try:
                import anthropic  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover - installable extra
                raise RuntimeError(
                    "anthropic package not installed; pip install signal-engine[llm]"
                ) from exc
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 600) -> str:
        client = self._client_lazy()
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=self.model,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    max_tokens=max_tokens,
                )
                parts = [
                    block.text
                    for block in response.content
                    if getattr(block, "type", "") == "text"
                ]
                return "".join(parts).strip() or "_(empty response)_"
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(2 ** attempt)
        return f"_(LLM error after 3 attempts: {last_exc})_"  # noqa: E501
