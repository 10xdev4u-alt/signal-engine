# PRD — Signal Engine v1.0

## 1. Executive Summary

**Problem statement.** Solo builders have no systematic way to find audiences
with urgent, repeated, money-adjacent problems, or to learn the exact language
those audiences use — the SaaS tools that did this shut down or push users
toward rule-breaking automation that gets accounts banned.

**Proposed solution.** A local-first engine that politely monitors public
subreddit RSS feeds on a schedule, accumulates searchable history, ranks
recurring pain points with real quotes and permalinks, maintains living
per-subreddit profiles updated nightly, and renders a daily digest dashboard.

**Success criteria (measurable).**

| # | KPI | Target |
|---|-----|--------|
| 1 | Fetch reliability over 30 days at default pacing (1 req/45s) | ≥99% successful fetches; 0 IP blocks lasting >1h |
| 2 | Daily digest ready by 08:00 local | ≥95% of days; always contains ≥3 ranked pain points with quotes + permalinks |
| 3 | Pain-point flag quality (operator manual eval, weekly) | Precision@10 ≥ 0.7 ("this thread describes a real problem") |
| 4 | Nightly profile updates | Dated changelog entry appended ≥6 nights/7 per active subreddit |
| 5 | Monthly operating cost | $0 without LLM key; ≤$25/month with Claude key enabled |

## 2. User Experience & Functionality

### Personas

- **Operator (primary, only):** the user. Technical, runs Arch Linux,
  checks the dashboard once every morning, makes all build/sell decisions.
- **Future reader (indirect):** visitors of the operator's own channels,
  who eventually receive products/content derived from mined pains. Not
  served by this software directly in v1.0.

### User Stories & Acceptance Criteria

**US1 — Scheduled listening.**
As an operator, I want subreddits fetched automatically so history
accumulates while I sleep.
- AC: `signal-engine add-subreddit <name>` registers a sub; cron-driven
  `signal-engine fetch` pulls new posts every 30 min and comments for posts
  <48h old, paced at ≥45 s between requests.
- AC: Every request logged in `fetch_log` (url, status, bytes, ts); a 429/403
  triggers exponential backoff (×2 up to 8h) recorded with reason.
- AC: Re-fetching an already-stored post/comment is idempotent (no dupes).
- AC: `signal-engine status` prints per-sub last-success, counts, error rate.

**US2 — Morning digest.**
As an operator, I want a one-page digest each morning so I decide in 10 minutes.
- AC: Generated daily at 08:00 local (cron), also rendered at `/digest`.
- AC: Sections: top rising pains (ranked by frequency + frustration +
  recency), new phrases not seen in prior 14 days, intent-flagged threads
  (score 4–5) sorted newest-first, profile changelog since yesterday.
- AC: Every pain point shows ≥3 verbatim quotes, each linking to its
  comment/post permalink, plus first-seen / last-seen dates and mention count.

**US3 — Living community profiles.**
As an operator, I want auto-maintained profiles per subreddit so I understand
each audience deeply before acting on it.
- AC: Markdown file per sub under `profiles/<sub>.md`: demographics,
  psychographics, exact language (quoted), tried-and-failed solutions,
  what gets upvoted/buried, rules summary, tone notes, dated update log.
- AC: Nightly job updates from the day's data; changes only when contradicted
  or added-to; every change appended to the update log with date + reason.
- AC: Without LLM key, the profile still renders stats-derived sections
  (top phrases, active hours, top threads); LLM sections appear when key set.

**US4 — Buying-intent detection.**
As an operator, I want "actively looking for a solution" flagged separately
from venting so I never waste time on complaints.
- AC: Each post/comment scored 1–5 intent. Heuristic scorer always runs
  (question forms: "what should I do", "any recommendations", "tool for…",
  "how do I fix"); LLM re-scores 3+ when key present.
- AC: Digest lists only 4–5 as actionable; 1–3 stored for trends.

**US5 — Niche discovery sweep.**
As an operator without a niche, I want broad-domain subreddits swept so
recurring cross-community pains reveal where desperate buyers cluster.
- AC: A curated seed list (~15 subs across money/health/productivity/
  relationships/hobbies, stored in config) can be enabled as a group.
- AC: Weekly report ranks pain clusters across subs by desperation score =
  frequency × frustration × monetization signals ("worth it", "pay for",
  "spent $"), naming the subs where each cluster appears.
- AC: Report explicitly lists clusters in regulated/credential domains
  (medical, legal, financial advice) under a caution section, excluded from
  ranking.

**US6 — Full-history search.**
As an operator, I want full-text search over everything collected so I can
investigate any hunch.
- AC: SQLite FTS5 across titles + bodies + comments; results page filters by
  sub, date range, type (post/comment), min score; permalinks included.

**US7 — Graceful degradation.**
As an operator, I want the system fully useful with zero API keys.
- AC: No key → deterministic pipeline only; UI hides LLM-dependent fields;
  nothing errors. Key set → profiling/intent enrichment activates.

### Non-goals (v1.0)

- No posting, replying, DM, or account management of any kind. Ever.
- No login/authenticated Reddit access; public feeds/API free tier only.
- No multi-user/SaaS mode; single-operator localhost tool.
- No product-builder or checkout integration (v2 decision).
- No VPN/proxy rotation — IP-reputation evasion is out on principle.

## 3. AI System Requirements

- **Tools/providers:** Anthropic Messages API via `anthropic` SDK behind a
  `Provider` interface (`complete(system, user, max_tokens) -> str`);
  Anthropic first-class; any OpenAI-compatible endpoint configurable.
- **Usage sites:** nightly profile builder; intent re-scoring (score ≥3);
  weekly report narrative. All optional.
- **Cost controls:** hard monthly token budget in settings (default $25);
  budget meter persisted; jobs skip LLM steps when exhausted and say so in
  output. Model defaults: Haiku-class for scoring, Sonnet-class for profiles.
- **Evaluation strategy:** weekly Precision@10 capture on digest flags
  (operator marks relevant/not in dashboard; stored to `eval_marks`);
  profile diff review (yesterday vs today rendered side-by-side at
  `/profile/<sub>?diff=1`). Target: P@10 ≥ 0.7 (KPI 3).

## 4. Technical Specifications

### Architecture overview

```
cron ──▶ signal-engine fetch        (every 30 min, residential IP)
             │ feedparser + httpx, pace ≥45 s, backoff on 429/403
             ▼
         SQLite (posts, comments, fetch_log, FTS5)
             │
cron ──▶ signal-engine analyze      (after each fetch)
             │ n-grams, question detect, frustration lexicon,
             │ TF-IDF-ish pain clustering, heuristic intent score
cron ──▶ signal-engine digest       (08:00 daily)
             │ (+ optional LLM enrich) ──▶ digests table + markdown
             ▼
FastAPI dashboard (localhost:7788): /digest /pains /profile/<sub> /search /status
```

Components are separate CLI invocations sharing one DB — crash-safe, testable,
no long-running daemon required.

### Integration points

- reddit.com `.rss` endpoints (read-only, unauthenticated).
- Optional: Anthropic API (egress to api.anthropic.com).
- OS cron for scheduling (entries documented in issues #004/#008/#013).

### Data model (core tables)

- `subreddits(id, name UNIQUE, group_name, active, added_at)`
- `fetch_log(id, url, kind[post_feed|comment_feed], http_status, bytes, ts)`
- `posts(id TEXT PK=t3_id, subreddit, title, author, selftext, permalink,
   created_utc, fetched_at)`
- `comments(id TEXT PK=t1_id, post_id, author, body, permalink, created_utc,
   fetched_at)`
- `pain_clusters(id, label, first_seen, last_seen, mention_count,
   desperation_score, caution_flag)`
- `cluster_members(cluster_id, ref_type[post|comment], ref_id, quote, score)`
- `intent_scores(ref_type, ref_id, heuristic_score, llm_score NULL, scored_at)`
- `profiles(subreddit, snapshot_md, generated_at)` — append-only history
- `digests(id, date, md, json)`
- `settings(key, value)` — pacing, budgets, model names, seed lists
- FTS5 virtual table `search(posts/comments)` kept in sync on insert.

### Security & privacy

- Runs and stores everything on the operator's machine; no telemetry.
- Reddit credentials: none exist. LLM key lives in `.env` (gitignored).
- Collected content stays local; prompts sent to Anthropic contain quoted
  third-party text — documented risk, accepted for personal research scale;
  provider can be swapped/self-hosted via OpenAI-compatible interface.

## 5. Risks & Roadmap

### Phased rollout

- **M0 — Foundation (issues #001–#004):** repo/tooling, schema, fetcher,
  scheduler. Exit: 7 days unattended collection on 3 subs, KPI 1 green.
- **M1 — Insight (issues #005–#009):** comments ingestion, analyzer,
  dashboard, digest, search. Exit: KPI 2 met for 5 consecutive days.
- **M2 — Intelligence (#010–#011):** LLM adapter, profiles, language mining,
  LLM intent. Exit: KPI 4 met one week with key set.
- **M3 — Discovery & proof (#012–#013):** niche sweep, weekly report,
  eval harness. Exit: KPI 3 measured twice; first go/no-go decision on a
  discovered niche.

### Technical risks

| Risk | Mitigation |
|------|-----------|
| Reddit breaks/changes `.rss` | Feed adapter isolated behind `FeedSource` protocol; official-API fallback pre-designed |
| IP blocked despite pacing | Backoff + circuit breaker + alert line in digest; fetcher runs locally, never cloud |
| LLM cost overrun | Token budget meter, hard caps, cheap-model defaults, graceful skip |
| Pain clustering noise (false merges) | Conservative similarity threshold; operator can merge/split clusters in UI (v1.1) |
| Legal posture drift | Personal research use only; commercial scale-out requires Data API switch (documented in RESEARCH §3) |
