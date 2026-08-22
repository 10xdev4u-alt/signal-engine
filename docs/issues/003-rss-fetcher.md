# Issue 003 — RSS source adapter + idempotent ingest

**Milestone:** M0 · **Depends on:** #002 · **Size:** M

## Why
This is the product's only contact surface with Reddit. Verified live
2026-08-22 (RESEARCH §1): `.rss` returns Atom with title, permalink,
`t3_/t1_` ids, timestamps, author, body HTML. All format knowledge lives here
and nowhere else.

## Scope
- `sources/base.py`: dataclasses `PostEntry`, `CommentEntry`; `FeedSource`
  protocol.
- `sources/rss.py`:
  - `posts_url(sub)` → `https://www.reddit.com/r/<sub>/.rss`
  - `comments_url(post_id)` → post comments URL + `.rss`
  - parse Atom via feedparser into entries; strip HTML from bodies to plain
    text (keep raw too); normalize timestamps to UTC ISO.
- `ingest/store.py`: `upsert_post(conn, PostEntry)`,
  `upsert_comment(conn, CommentEntry)` keyed on Reddit id — rerun-safe.
- `tests/fixtures/`: two frozen XML files (one subreddit feed, one comment
  feed) captured manually during development and committed.

## Tasks
1. Parser + text-stripper with unit tests against fixtures (field mapping
   asserted per RESEARCH §1).
2. Idempotency tests: upsert same entry twice → row count unchanged.
3. Link posts must store empty selftext (feed carries only attribution footer).

## Acceptance criteria
- [ ] Parsing fixture feed yields N posts with all fields mapped correctly.
- [ ] Double-upsert leaves exactly one row; FTS stays consistent.
- [ ] No network call anywhere in tests (fixture files only).
- [ ] Malformed XML raises a typed `FeedParseError`, not a stack trace.

## Verification
```bash
./run.sh check
```

## Out of scope
Anything that fetches over HTTP (that's #004), comments orchestration (#005).
