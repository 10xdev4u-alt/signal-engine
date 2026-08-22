# Issue 005 — Comment feed ingestion (<48h posts)

**Milestone:** M1 · **Depends on:** #004 · **Size:** S

## Why
Comments are where the language lives ("this is what they'd tell a friend")
and where buying-intent shows up most nakedly. Comment feeds are public RSS
(RESEARCH §1) but cost one request per post — so we cap spend: only posts
younger than `comment_max_age_h`.

## Scope
- Extend `ingest/fetch.py`: after storing new posts, select posts <48h old
  without complete comment pulls, fetch their comment feeds oldest-first,
  paced through the same `PacedClient`.
- Track completion per post (settings/flag column `comments_done_at`) so a
  post is pulled at most ~2 times ever.
- Config knob surfaced in `.env.example`.

## Tasks
1. Selection query + ordering test (oldest first, limit per run to stay
   within pace budget: ≤ floor(window/pace) − post-feed requests).
2. Fixture test: comment-feed XML → rows with permalinks + parent post id.
3. Budget arithmetic documented in module docstring.

## Acceptance criteria
- [ ] A run never issues more requests than the pace budget allows.
- [ ] Comments carry working permalinks (fixture asserts URL shape).
- [ ] Re-running doesn't re-pull completed posts (request count assertion
      with mock transport).
- [ ] Posts older than cutoff are never fetched.

## Verification
```bash
./run.sh check && ./run.sh fetch --verbose
```
