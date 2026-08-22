# Issue 009 — Full-text search page (FTS5)

**Milestone:** M1 · **Depends on:** #002 · **Size:** S

## Why
Hunches need receipts. When the operator wonders "does 'chargeback' come up
a lot here?", they need an answer across all history in under a second
(PRD US6).

## Scope
- `/search?q=&sub=&type=&from=&to=` — FTS5 `MATCH` with filters; snippet
  highlighting (`snippet()`), type badge, date, sub, permalink.
- Query sanitization: wrap user query into FTS-safe expression (quote
  tokens; support `"exact phrase"` passthrough).
- Empty/invalid query states; result cap 200 with count display.

## Tasks
1. Sanitizer unit tests (injection-ish inputs: `*`, `OR`, quotes, unicode).
2. Perf smoke: 100k-row fixture index → p95 query <200ms locally, recorded
   in PR body.

## Acceptance criteria
- [ ] Phrase, prefix, and filtered searches return expected fixture results.
- [ ] Malformed queries never 500.
- [ ] Results link out with permalinks; snippets show the matched context.

## Verification
```bash
./run.sh check && ./run.sh serve   # manual search pass in PR description
```
