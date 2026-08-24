# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- LLM provider layer (Anthropic + any OpenAI-compatible endpoint) with `NullProvider` fallback and a hard monthly budget ledger (`signal_engine/llm/`)
- Eval harness: `POST /eval/{ref_type}/{ref_id}` mark endpoint, `GET /eval` top-10 dashboard with live precision@10, `GET /eval/marks.json` export (`signal_engine/web/`)
- Profile builder spec for nightly community snapshots (`docs/profile-builder-spec.md`)
- Intent re-scoring spec for LLM-assisted buyer-intent classification (`docs/m2-11-spec.md`)
- Niche sweep spec (cross-subreddit cluster ranking) — lands with profile builder
- Weekly report spec (Precision@10 + recent digest trend lines) — lands with eval-harness report generator
- Landing page with design tokens and GitHub Pages deploy workflow (`site/`, `.github/workflows/site.yml`)
- Architecture decision records (`docs/adr/0001` RSS-only-never-post, `0002` local-first-residential-ip, `0003` deterministic-first-llm-optional)
- Changelog and release process (Keep a Changelog format, SemVer)

### Changed

- Settings precedence bug fixed: process environment now correctly overrides `.env` file
- Cluster default similarity threshold lowered from 0.62 (tf-idf) to 0.4 (presence-cosine) for short social texts
- Docs rewritten with plain human voice: zero em dashes, no AI vocabulary, sentence-case headings

### Security

- `.env` and `.mimosa/` paths explicitly gitignored
- Mimosa pre-write scan documented as a hint, not a gate; reviewer and CodeRabbit are authoritative on SQL safety
- Secret-masked settings repr verified by test

## v0.1.0 — 2026-08-23

### Added

- M0 foundation: package skeleton, SQLite schema, polite RSS fetcher, dashboard, CI gate, ADRs, CONTRIBUTING, SECURITY
- M1 insight layer: comment ingestion, deterministic analyzer with pain clustering, dashboard pages, daily digest, full-text search
- 49 unit tests covering fetcher pacing, analyzer golden-file behavior, digest sections, search sanitization
- Public repository at [github.com/10xdev4u-alt/signal-engine](https://github.com/10xdev4u-alt/signal-engine)

[Unreleased]: https://github.com/10xdev4u-alt/signal-engine/compare/v0.1.0...HEAD
[v0.1.0]: https://github.com/10xdev4u-alt/signal-engine/releases/tag/v0.1.0
