"""Typed settings loaded from defaults, .env file, then environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path

_SECRET_FIELDS = {"anthropic_api_key", "openai_api_key"}
_INT_FIELDS = {"fetch_window_min", "comment_max_age_h", "port"}
_FLOAT_FIELDS = {"pace_seconds", "monthly_llm_budget"}


@dataclass(frozen=True)
class Settings:
    db_path: str = "data/engine.db"
    data_dir: str = "data"
    pace_seconds: float = 45.0
    fetch_window_min: int = 30
    comment_max_age_h: int = 48
    monthly_llm_budget: float = 25.0
    port: int = 7788
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""
    model_scoring: str = "claude-haiku-4-5-20251001"
    model_writing: str = "claude-sonnet-5"

    def __repr__(self) -> str:  # secrets must never reach logs
        parts = []
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in _SECRET_FIELDS and value:
                value = "***"
            parts.append(f"{f.name}={value!r}")
        return f"Settings({', '.join(parts)})"

    __str__ = __repr__

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key or self.openai_api_key)


_ENV_ALIASES = {
    "DB_PATH": "db_path",
    "DATA_DIR": "data_dir",
    "PACE_SECONDS": "pace_seconds",
    "FETCH_WINDOW_MIN": "fetch_window_min",
    "COMMENT_MAX_AGE_H": "comment_max_age_h",
    "MONTHLY_LLM_BUDGET": "monthly_llm_budget",
    "PORT": "port",
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "OPENAI_API_KEY": "openai_api_key",
    "OPENAI_BASE_URL": "openai_base_url",
}


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        key = key.strip()
        raw = raw.strip().strip('"').strip("'")
        if key in _ENV_ALIASES and raw:
            values[_ENV_ALIASES[key]] = raw
    return values


def load_settings(dotenv_path: str | Path = ".env", environ: dict | None = None) -> Settings:
    """Precedence: defaults < .env file < process environment."""
    source: dict[str, str] = dict(_parse_dotenv(Path(dotenv_path)))
    env = dict(os.environ if environ is None else environ)
    for alias, field_name in _ENV_ALIASES.items():
        if alias in env:
            source[field_name] = env[alias]
    kwargs: dict = {}
    for field_name in {f.name for f in fields(Settings)} & set(source):
        raw = source[field_name]
        if field_name in _INT_FIELDS:
            kwargs[field_name] = int(raw)
        elif field_name in _FLOAT_FIELDS:
            kwargs[field_name] = float(raw)
        else:
            kwargs[field_name] = raw
    return Settings(**kwargs)
