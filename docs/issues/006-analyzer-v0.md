# Issue 006 — Analyzer v0: n-grams, question detect, frustration score

**Milestone:** M1 · **Depends on:** #004 · **Size:** M

## Why
The deterministic core that makes the engine useful with zero API keys:
turn raw posts/comments into ranked signals (PRD US2/US5 feed off this).
LLM layers in M2 are additive to this, never replacements.

## Scope
- `analyze/ngrams.py`: 1–3 gram frequency per subreddit per day; stopword
  list checked into repo; output table `phrase_stats(sub, phrase, day,
  count)`; distinctive-phrase score = freq_in_sub / freq_across_corpus.
- `analyze/questions.py`: ask-pattern detection — ends with "?", starts
  "how do i / what should i / anyone know / recommendations / best way",
  tool-seek ("app/tool/service/site for"), money-seek ("worth paying",
  "would you pay"). Emits typed spans with offsets for quoting.
- `analyze/frustration.py`: lexicon scoring 0–3 ("burned", "wasted months",
  "scam", "about to give up" …), lexicon as editable data file.
- `analyze/cluster.py`: tf-idf vectors over post title+selftext and comment
  bodies (per sub); incremental clustering — new item joins cluster at
  cosine ≥0.62 else seeds a new one; `pain_clusters` +
  `cluster_members` rows maintained; desperation placeholder =
  mention_count × max frustration in cluster.

## Tasks
1. Golden-file tests: fixture corpus → exact phrase counts and clusters.
2. Threshold tests: near-duplicate joins existing cluster; distinct topic
   seeds new one.
3. Performance smoke on synthetic 50k rows <60s locally (recorded in PR).

## Acceptance criteria
- [ ] Running `./run.sh analyze` after a fetch produces populated stats and
      cluster tables; rerun is idempotent per content hash.
- [ ] Every cluster exposes ≥3 stored quotes with permalinks (test asserts).
- [ ] All scoring is pure-Python + SQLite — runs with no LLM key and no
      network.
- [ ] Lexicons/phrases live in data files, not code constants.

## Verification
```bash
./run.sh check && ./run.sh analyze --subreddits smallbusiness --verbose
```

## Out of scope
LLM anything (#010/#011); cross-sub sweep (#012).
