# Issue 002 — Config loader + SQLite schema/migrations + FTS5

**Milestone:** M0 · **Depends on:** #001 · **Size:** M

## Why
All components share one SQLite DB and one config object. Getting the schema
right first prevents migration pain later (see ARCHITECTURE data model).

## Scope
- `config.py`: frozen dataclass `Settings` loaded from defaults ← `.env` ← CLI
  overrides. Keys: `db_path`, `data_dir`, `pace_seconds=45`,
  `fetch_window_min=30`, `comment_max_age_h=48`, `port=7788`,
  `monthly_llm_budget=25.0`, `anthropic_api_key` (env only), `model_scoring`,
  `model_writing`.
- `migrations/001_init.sql`: all tables from PRD §4 (`subreddits`,
  `fetch_log`, `posts`, `comments`, `pain_clusters`, `cluster_members`,
  `intent_scores`, `profiles`, `digests`, `settings`) with indices on
  `(subreddit, created_utc)` etc.
- `migrations/002_fts.sql`: FTS5 virtual table + triggers keeping post title/
  selftext and comment body searchable.
- `db.py`: `connect(settings)` (WAL, busy_timeout=30s, foreign_keys=ON),
  `migrate(conn)` applying unapplied migrations tracked in `_migrations` table.
- `subreddits` management helpers: add/list/deactivate.

## Tasks
1. SQL migrations as files; runner applies in lexicographic order in a txn.
2. Unit tests against tmp-path DB: migrate fresh, re-run idempotent,
   FTS trigger inserts searchable rows.

## Acceptance criteria
- [ ] `python -c "from signal_engine.db import connect, migrate"` works and
      creates full schema at `Settings().db_path`.
- [ ] Running migrate twice changes nothing (row counts identical).
- [ ] Inserting a post makes it findable via FTS5 `MATCH`.
- [ ] No API key ever lands in DB or logs (test asserts key absent from repr).

## Verification
```bash
./run.sh check   # includes new tests
```

## Out of scope
Anything that performs HTTP; analyzer tables beyond DDL.
