# Issue 011 — Language mining into profiles + LLM intent re-scoring

**Milestone:** M2 · **Depends on:** #010 · **Size:** M

## Why
Two upgrades that make outputs sound like the audience instead of a bot:
the profile's language section gets mined verbatim phrases (problem words,
solution words, tried-it words — quoted), and intent scores 3+ get an LLM
second opinion so the morning queue is trustworthy (PRD US4).

## Scope
- Language miner: from analyzer n-grams + question/tool-seek hits, extract
  candidate phrases WITH example quotes; LLM pass labels each as
  problem/solution/tried-and-failed/other; writes into profile's language
  section with quote links.
- `analyze/intent.py` extension: `LLMRescorer` re-scores heuristic 3+ items
  nightly in batches (cheap model default); stores both scores; UI shows
  final = max(heuristic, llm) with source badge.
- Batch size + budget checks via #010 ledger.

## Tasks
1. Label-schema validation tests (unknown label → rejected, retried once,
   then dropped to 'other').
2. Rescore idempotency: same item never rescored twice (ledger keyed by
   content hash of body).
3. Calibration sample: operator hand-scores 30 flagged items; PR body
   reports agreement %.

## Acceptance criteria
- [ ] Profile language section contains ≥10 quoted phrases after one week
      of data, each with link.
- [ ] Intent queue Precision@5 spot-check ≥0.7 on calibration sample.
- [ ] Rescoring a week of data costs <$2 at default models (ledger assert).
- [ ] No-LLM mode unchanged from #010 behavior.

## Verification
```bash
./run.sh check && ./run.sh analyze --rescore --dry-run
```
