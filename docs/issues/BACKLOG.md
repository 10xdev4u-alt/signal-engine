# Issue Backlog — Signal Engine v1.0

One issue = one branch = one PR (see `AGENTS.md` for the loop).
Milestones gate each other; issues inside a milestone may be picked in order
(dependencies noted per issue).

| ID | Title | Milestone | Depends on | Size |
|----|-------|-----------|------------|------|
| [#001](001-bootstrap-repo.md) | Bootstrap repo, packaging, tooling | M0 | — | S |
| [#002](002-config-db-schema.md) | Config loader + SQLite schema/migrations + FTS5 | M0 | #001 | M |
| [#003](003-rss-fetcher.md) | RSS source adapter + idempotent ingest | M0 | #002 | M |
| [#004](004-polite-scheduler.md) | Paced client, backoff, fetch_log, cron wiring, `status` CLI | M0 | #003 | M |
| [#005](005-comment-ingest.md) | Comment feed ingestion (<48h posts) | M1 | #004 | S |
| [#006](006-analyzer-v0.md) | Analyzer v0: n-grams, question detect, frustration score | M1 | #004 | M |
| [#007](007-dashboard-v0.md) | Dashboard v0: digest/pains/status pages | M1 | #004 | M |
| [#008](008-daily-digest.md) | Daily digest generator + cron entry | M1 | #006, #007 | M |
| [#009](009-fts-search.md) | Full-text search page (FTS5) | M1 | #002 | S |
| [#010](010-llm-profiles.md) | LLM provider layer + nightly profile builder | M2 | #006 | L |
| [#011](011-language-intent.md) | Language mining into profiles + LLM intent re-scoring | M2 | #010 | M |
| [#012](012-niche-sweep.md) | Niche discovery sweep across broad seed subs | M3 | #008 | M |
| [#013](013-weekly-report-eval.md) | Weekly report + Precision@10 eval harness | M3 | #008 | M |

## Milestone exit gates

- **M0:** 7 consecutive days unattended collection on ≥3 subs; KPI-1 green.
- **M1:** KPI-2 met 5 days running; operator can answer "what hurt this week?"
  from the dashboard alone.
- **M2:** KPI-4 met for one week with key set; profiles pass the 10-minute read test.
- **M3:** KPI-3 measured twice (P@10 ≥ 0.7); first niche go/no-go decision made.
