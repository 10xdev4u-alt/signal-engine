# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

## v0.3.0 — 2026-08-25

### Added

- Profile builder (`analyze/profile.py`): deterministic core (volume, hours, phrases, top threads, tried-and-failed markers) with additive budget-gated LLM narrative; dated update log per subreddit; `profile_last_run` setting recorded
- LLM intent re-scoring (`analyze/questions.rescore_with_llm`): re-scores heuristic-3+ items through the configured LLM provider, hard monthly budget cap, max-items bound per call, parse/runtime errors degrade to the heuristic
- Cross-subreddit niche sweep spec (M3 #12) — full design with regulated-domain caution section
- Weekly report spec (M3 #13) — Precision@10 design with one-line recommendation
- Eval wire-in (M3 #13): /eval page now renders a per-mark recommendation (no marks yet / tighten / hold) and a trailing-7-day digest timeline
- 13 new tests across profile builder (7) and intent re-scoring (6)

### Changed

- M2 LLM provider layer (v0.2.0) extended with `NullProvider` graceful-degradation test coverage
- Dashboard templates now extend the `_layout.html` shell (sidebar, breadcrumbs, theme toggle, Ctrl+K)

### Fixed

- `_layout.html` was referenced by every dashboard template but had not been committed in v0.2.0; restored as part of the eval wire-in
- Eval mark form (v0.2.0) now correctly reads `verdict` from the form body; the original setup 404'd on submit because the route expected a query-string value

### Security

- Branch protection tightened: `enforce_admins: true`, `required_linear_history: true` (no merge commits on main)
- Secret scanning + push protection + Dependabot alerts + Dependabot security updates all enabled
- `python-multipart` added to runtime deps for FastAPI form parsing

## v0.2.0 — 2026-08-25

### Added

- Eval harness: `POST /eval/{ref_type}/{ref_id}` mark endpoint (form body), `GET /eval` top-10 dashboard with live precision@10, `GET /eval/marks.json` export
- LLM provider layer (Anthropic + any OpenAI-compatible endpoint) with `NullProvider` fallback and a hard monthly budget ledger
- Landing page (`site/`) with design tokens and GitHub Pages deploy workflow
- CHANGELOG, SECURITY tooling note, retrospective operator-loop doc
- 13 new tests across LLM provider, profile builder plumbing, eval form, search

### Changed

- `python-multipart` runtime dep for form parsing

## v0.1.0 — 2026-08-23

### Added

- M0 foundation: package skeleton, SQLite schema, polite RSS fetcher, dashboard, CI gate, ADRs, CONTRIBUTING, SECURITY
- M1 insight layer: comment ingestion, deterministic analyzer with pain clustering, dashboard pages, daily digest, full-text search
- 58 unit tests covering fetcher pacing, analyzer golden-file behavior, digest sections, search sanitization, eval mark round trip
- Public repository at [github.com/10xdev4u-alt/signal-engine](https://github.com/10xdev4u-alt/signal-engine)

[Unreleased]: https://github.com/10xdev4u-alt/signal-engine/compare/v0.3.0...HEAD
[v0.3.0]: https://github.com/10xdev4u-alt/signal-engine/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/10xdev4u-alt/signal-engine/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/10xdev4u-alt/signal-engine/releases/tag/v0.1.0
