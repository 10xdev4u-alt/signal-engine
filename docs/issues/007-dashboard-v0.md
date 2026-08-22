# Issue 007 — Dashboard v0: digest/pains/status pages

**Milestone:** M1 · **Depends on:** #004 · **Size:** M

## Why
The operator's morning surface. Server-rendered Jinja2 + HTMX from CDN;
localhost only; zero build step; plain and one-page-per-concern like the
original guide's dashboard idea — minus the astroturf queue.

## Scope
- `web/app.py` (FastAPI): routes `/` (redirect), `/digest`,
  `/pains`, `/pains/<id>` (quotes + permalinks + members),
  `/status`, `/profile/<sub>` placeholder until #010.
- Templates with minimal CSS (system font stack); every pain point shows:
  label, mention count, first/last seen, desperation score, top quotes as
  blockquotes linking to Reddit permalinks (`rel="noreferrer"`).
- `/status` renders `fetch_log` aggregates: success rate 7d, last errors,
  breaker events.
- `cli.py serve` → uvicorn on `127.0.0.1:<port>` only.

## Tasks
1. Route tests with FastAPI TestClient against an in-memory DB fixture.
2. Empty-state templates (fresh install must not look broken).
3. Binding check test: asserts host is loopback.

## Acceptance criteria
- [ ] All pages render 200 on empty DB and populated DB fixtures.
- [ ] Every quote links out to a correct-looking reddit permalink; none of
      the app's own links ever point at reddit except permalinks.
- [ ] Server refuses non-loopback bind.
- [ ] Page weight <200KB total; no JS framework beyond HTMX CDN.

## Verification
```bash
./run.sh check && ./run.sh serve &   # then curl each route for 200s
```
