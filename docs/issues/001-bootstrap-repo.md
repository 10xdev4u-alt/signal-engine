# Issue 001 — Bootstrap repo, packaging, tooling

**Milestone:** M0 · **Depends on:** — · **Size:** S

## Why
Every later issue assumes `pip install -e .`, a test runner, a linter, and
`./run.sh check` as the single verification gate (AGENTS contract).

## Scope
- `pyproject.toml`: project metadata, deps (`httpx`, `feedparser`,
  `beautifulsoup4`, `fastapi`, `uvicorn`, `jinja2`, `rich`);
  optional extra `[project.optional-dependencies] llm = ["anthropic"]`,
  `dev = ["pytest", "ruff"]`. Python ≥3.12.
- Package skeleton: empty modules per ARCHITECTURE layout, `__version__`.
- `run.sh`: `check` (ruff + pytest), `fetch|analyze|digest|serve|status`
  passthrough to CLI stub.
- `.gitignore`: `data/`, `.env`, `__pycache__`, `.venv`.
- `.env.example` documenting every config key incl. `ANTHROPIC_API_KEY`
  (optional) — no real keys ever committed.

## Tasks
1. CI-lite: `run.sh check` must exit non-zero on any lint/test failure.
2. Trivial smoke test asserting package imports and version string.

## Acceptance criteria
- [ ] Fresh venv: `pip install -e ".[dev]" && ./run.sh check` passes green.
- [ ] `./run.sh status` runs and prints "no database yet" gracefully.
- [ ] Repo contains no secrets; `.env` is ignored (test via
      `git check-ignore .env`).

## Verification
```bash
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && ./run.sh check
```

## Out of scope
Everything else. This PR ships plumbing only.
