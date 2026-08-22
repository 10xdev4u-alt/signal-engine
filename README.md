# Signal Engine

A local-first Reddit audience-research system. It listens to public subreddit
RSS feeds, builds history, mines recurring pain points and the exact language
people use, maintains living community profiles, and serves a daily digest
dashboard — so you can find desperate audiences and build legitimate products
for channels you own.

**Design law:** this tool only *reads*. It never logs into Reddit, never posts,
never drafts content for you to paste into threads. Listening is research;
astroturfing is how accounts die (see `docs/RESEARCH.md` for the receipts).

## Status

Planning complete, implementation starting. See:

- [`docs/PRD.md`](docs/PRD.md) — product requirements (strict schema)
- [`docs/RESEARCH.md`](docs/RESEARCH.md) — verified platform facts behind every design decision
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — modules, data model, runtime topology
- [`docs/issues/BACKLOG.md`](docs/issues/BACKLOG.md) — issue index across 5 milestones
- [`docs/GUARDRAILS.md`](docs/GUARDRAILS.md) — enforced repo protections
- [`docs/adr/`](docs/adr/) — architecture decision records (RSS-only, local-first, LLM-optional)
- [`AGENTS.md`](AGENTS.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) — the agentic research → issue → PR loop

## Quickstart (once M0 lands)

```bash
pip install -e ".[dev]"
signal-engine add-subreddit smallbusiness
signal-engine fetch          # one polite pull
signal-engine serve          # dashboard at http://localhost:7788
crontab -l                   # 30-min fetch + 08:00 digest entries documented in issue #004/#008
```

## Stack (decided)

Python 3.12+, SQLite (+FTS5), FastAPI + Jinja2 + HTMX, httpx + feedparser.
LLM layer is optional and pluggable: no key = deterministic stats only;
`ANTHROPIC_API_KEY` set = Claude-assisted profiling and intent scoring.
