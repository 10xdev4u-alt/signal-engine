# ARCHITECTURE.md

## Repository layout

```
signal-engine/
├── pyproject.toml            # deps: httpx, feedparser, fastapi, uvicorn,
│                             # jinja2, rich, anthropic (optional extra)
├── signal_engine/
│   ├── __init__.py           # __version__
│   ├── cli.py                # typer/rich CLI: add-subreddit, fetch, analyze,
│   │                         # digest, serve, status, report, sweep
│   ├── config.py             # dataclass settings; .env loader; defaults:
│   │                         #   pace_seconds=45, fetch_window_min=30,
│   │                         #   comment_max_age_h=48, monthly_llm_budget=25.0,
│   │                         #   port=7788, db_path=./data/engine.db
│   ├── db.py                 # sqlite3 connection factory, migrations runner,
│   │                         # FTS5 sync triggers
│   ├── migrations/           # 001_init.sql, 002_fts.sql, ... (numbered)
│   ├── sources/
│   │   ├── base.py           # FeedSource protocol: iter_entries() -> Entry
│   │   ├── rss.py            # RedditRssSource (adapter — ONLY place that
│   │                         #   knows Atom field layout)
│   │   └── polite.py         # PacedClient: httpx wrapper, min-interval,
│   │                         #   Retry-After honoring, backoff, breaker
│   ├── ingest/
│   │   ├── store.py          # upsert posts/comments (idempotent by t3_/t1_ id)
│   │   └── fetch.py          # orchestration: which feeds, which order
│   ├── analyze/
│   │   ├── ngrams.py         # 1–3 gram freq per sub/day, stopword list
│   │   ├── questions.py      # question & ask-pattern detection regexes
│   │   ├── frustration.py    # lexicon scoring ("burned", "wasted", "scam", …)
│   │   ├── cluster.py        # presence-cosine over stemmed token sets, default 0.4
│   │   │                     # incremental assign-or-new-cluster
│   │   └── intent.py         # heuristic 1–5; LLMRescorer if provider set
│   ├── llm/
│   │   ├── base.py           # Provider protocol + NullProvider
│   │   ├── anthropic_provider.py
│   │   ├── openai_compat.py  # any OPENAI_BASE_URL endpoint (Gemini/Kimi/local)
│   │   └── budget.py         # token/cost ledger in settings table
│   ├── profile/
│   │   ├── stats_sections.py # deterministic sections (always available)
│   │   └── builder.py        # nightly merge w/ LLM sections, update-log append
│   ├── digest/
│   │   └── daily.py          # build digest rows + markdown render
│   ├── web/
│   │   ├── app.py            # FastAPI, Jinja2 templates, HTMX CDN
│   │   └── templates/        # base.html, digest.html, pains.html,
│   │                         # profile.html, search.html, status.html
│   └── reporting/
│       └── weekly.py         # cross-sub niche sweep + weekly report
├── tests/
│   ├── fixtures/             # frozen .rss XML snapshots (NO live network in tests)
│   ├── test_rss_parse.py
│   ├── test_store_idempotent.py
│   ├── test_polite_pacing.py # uses injected clock, never sleeps for real
│   ├── test_cluster.py
│   ├── test_intent.py
│   └── test_digest.py
├── data/                     # gitignored: engine.db, profiles/, digests/
├── docs/                     # PRD, RESEARCH, ARCHITECTURE, issues/
└── AGENTS.md                 # agentic dev loop contract
```

## Runtime topology (production)

Three crontab entries, all invoking installed CLI:

```cron
*/30 * * * *  cd ~/signal-engine && ./run.sh fetch analyze   >> data/cron.log 2>&1
0 8 * * *     cd ~/signal-engine && ./run.sh digest          >> data/cron.log 2>&1
0 7 * * 1     cd ~/signal-engine && ./run.sh report --weekly >> data/cron.log 2>&1
```

Dashboard is launched manually (`signal-engine serve`) or as a systemd user
unit; it only reads the DB.

## Key invariants

1. **Single writer per process; SQLite WAL mode** — cron jobs may overlap,
   WAL + busy_timeout=30s keeps them safe.
2. **Idempotency everywhere** — every ingest step keyed on Reddit's native
   ids; reruns are free.
3. **Network isolation in tests** — parsers/analyzer consume frozen fixtures;
   `PacedClient` takes an injectable clock/sleeper.
4. **LLM is an additive layer** — removing the key must never change control
   flow beyond hiding enriched fields.
5. **The RSS adapter is the only Reddit-format-aware code** — if Reddit
   changes fields or we swap to the official API, one module changes.
