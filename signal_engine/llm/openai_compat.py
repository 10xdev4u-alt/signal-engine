"""OpenAI-compatible provider (Gemini, Kimi, local OpenLLM)."""

from __future__ import annotations

import time
from urllib.parse import urlparse


class OpenAICompatProvider:
    name = "openai-compat"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("openai_base_url must be http(s)")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("openai package not installed") from exc
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 600) -> str:
        client = self._client_lazy()
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                chat = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                )
                text = chat.choices[0].message.content or ""
                return text.strip() or "_(empty response)_"
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(2 ** attempt)
        return f"_(LLM error after 3 attempts: {last_exc})_"
