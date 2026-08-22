# Issue 004 — Paced client, backoff, fetch_log, cron wiring, `status` CLI

**Milestone:** M0 · **Depends on:** #003 · **Size:** M

## Why
IP reputation is the existential risk (RESEARCH §2). The fetcher must be
polite by construction: min interval between requests, `Retry-After` honored,
exponential backoff, circuit breaker — plus visibility into every request.

## Scope
- `sources/polite.py`: `PacedClient` wrapping httpx with injectable
  `sleep` and `now`; enforces `pace_seconds`; on 429/403 backs off
  (45s ×2 up to 8h); after 5 consecutive blocks trips breaker (skip remaining
  feeds this run, log loudly).
- `ingest/fetch.py`: for each active sub → pull new-post feed → store;
  record every attempt in `fetch_log(url, kind, http_status, bytes, ts)`.
- `cli.py add-subreddit <name>` and `fetch` subcommands wired end-to-end.
- `cli.py status`: table per sub — last success age, stored counts, 7-day
  error rate, breaker state.
- README cron example updated; `docs/crontab.txt` snippet committed.

## Tasks
1. `PacedClient` tests with fake clock: pacing enforced, backoff doubles,
   Retry-After respected, breaker trips at threshold.
2. End-to-end test with mocked transport (httpx `MockTransport`): fetch →
   rows present → second fetch adds nothing.
3. Manual smoke on real Reddit (documented in PR description, not automated):
   one pull of `r/smallbusiness`, paste status output.

## Acceptance criteria
- [ ] Two sequential requests never happen closer than `pace_seconds`.
- [ ] A 429 response results in a delayed retry recorded in `fetch_log`,
      not an exception escaping the run.
- [ ] Breaker stops the whole run after repeated blocks and prints a line
      that will later surface in the digest.
- [ ] `signal-engine status` shows truthful numbers after the manual smoke.
- [ ] Zero requests fired when there is nothing new since last cursor.

## Verification
```bash
./run.sh check && ./run.sh fetch --subreddits smallbusiness && ./run.sh status
```

## Out of scope
Comment feeds (#005); any analysis.
