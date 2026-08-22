# CI — PR quality gate workflow

**Milestone:** M0 · **Area:** infra · **Size:** S

## Why
Branch protection can only enforce what CI reports. Every PR needs a
machine-checked gate: ruff lint + pytest, on Python 3.12.

## Scope
- `.github/workflows/ci.yml`: trigger on PR + push to main; job `check`
  runs `ruff check .` then `pytest` after `pip install -e ".[dev]"`.
- Pin action versions (actions/checkout@v4, setup-python@v5 with cache).
- After merge: add `check` as a required status check in branch protection.

## Acceptance criteria
- [ ] Workflow runs green on its own PR.
- [ ] Deliberate lint failure turns the check red (verified once, then reverted).
- [ ] `check` added to branch-protection required checks post-merge.
