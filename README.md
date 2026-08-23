# Signal Engine

A local-first Reddit audience-research system. It listens to public
subreddit RSS feeds, stores what it sees, ranks the problems that keep
coming up, maintains a written profile of each community, and serves a
digest every morning. You read the digest, then decide what to build.

The tool only reads. It never logs into Reddit, never posts, and never
drafts content for anyone to paste into threads. Reading public forums is
research. Impersonating customers is how accounts die. Our research notes
have the receipts: see `docs/RESEARCH.md`.

## Status

Planning and milestone M0 are done. M1 added comments ingestion, the
analyzer, the dashboard, the daily digest and search. See:

- `docs/PRD.md`, the product requirements with measurable targets
- `docs/RESEARCH.md`, verified platform facts behind every design decision
- `docs/ARCHITECTURE.md`, modules, data model, runtime topology
- `docs/issues/BACKLOG.md`, the issue index across five milestones
- `docs/GUARDRAILS.md`, enforced repo protections
- `docs/adr/`, architecture decision records
- `AGENTS.md` and `CONTRIBUTING.md`, the development loop contract

## Quickstart

```bash
pip install -e ".[dev]"       # add ,llm to enable Claude-assisted profiling
signal-engine add-subreddit smallbusiness
signal-engine fetch          # one polite pull
signal-engine serve          # dashboard at http://localhost:7788
crontab -l                   # entries live in docs/crontab.txt
```

## Stack

Python 3.12+, SQLite with FTS5, FastAPI with Jinja2 templates. Data lives
on your machine. The LLM layer is optional: with no API key the engine runs
on deterministic statistics alone, and setting `ANTHROPIC_API_KEY` turns on
Claude-assisted profiling and intent scoring under a hard monthly budget.
