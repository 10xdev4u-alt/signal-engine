# Issue 008 — Daily digest generator + cron entry

**Milestone:** M1 · **Depends on:** #006, #007 · **Size:** M

## Why
KPI-2 lives here: by 08:00 local, one page answering "what hurt yesterday,
who's asking right now, what changed in the profiles."

## Scope
- `digest/daily.py`: builds yesterday-window sections per PRD US2 —
  rising pains (score = Δmentions × frustration × recency decay), new
  phrases (not present in trailing 14d), intent-flagged 4–5 sorted newest
  first, profile changelog since previous digest, breaker/error notices.
- Persists to `digests(date, md, json)`; `/digest` serves latest; also
  writes `data/digests/YYYY-MM-DD.md`.
- Cron line documented + committed to `docs/crontab.txt`.
- Idempotent per date: regenerating overwrites same date row.

## Tasks
1. Digest builder unit-tested on fixture DB with known deltas (counts
   asserted exactly).
2. New-phrase detection test: phrase present 15 days ago but not in window
   counts as new; present yesterday AND last week doesn't.
3. Manual PR-body check: run against real week-one data, paste rendered md.

## Acceptance criteria
- [ ] Digest exists by 08:00 after cron install (operator verifies day 1).
- [ ] Always contains ≥3 ranked pain points or an explicit "nothing rose
      today" line (never silently empty).
- [ ] Every claim in the digest is backed by a stored quote + link.
- [ ] Re-running for the same date is safe (single row per date).

## Verification
```bash
./run.sh check && ./run.sh digest --date yesterday
```
