# Issue 010 — LLM provider layer + nightly profile builder

**Milestone:** M2 · **Depends on:** #006 · **Size:** L

## Why
Profiles are the product's crown jewel (PRD US3). Deterministic sections
always exist; the LLM turns them into demographics/psychographics/language
sections with quoted evidence and a disciplined update log. Budget-guarded
per PRD §3.

## Scope
- `llm/base.py`: `Provider` protocol, `NullProvider` (always "unavailable").
- `llm/anthropic_provider.py` (primary), `llm/openai_compat.py`
  (`OPENAI_BASE_URL` for Gemini/Kimi/local).
- `llm/budget.py`: cost ledger persisted in `settings`; jobs check budget
  before each call; exhausted → skip + note in output.
- `profile/stats_sections.py`: deterministic markdown — volume by hour,
  top 1–3 grams vs corpus baseline (distinctive phrases), most-engaged
  threads, tried-and-failed mentions ("tried X", "stopped using").
- `profile/builder.py`: nightly — render stats sections, then LLM pass that
  may only add: demographics (inferred, guesses marked), psychographics,
  tone notes, rules notes; every claim must quote source text with link.
  Diff against yesterday's snapshot; append dated line to update log
  describing what changed and why; store new snapshot.

## Tasks
1. Provider tests with stub transport; NullProvider path proves no-LLM run.
2. Prompt fixture test: builder refuses (raises) if LLM section lacks a
   quote+link per claim (schema-validated output).
3. Update-log semantics test: identical input day-over-day → log says
   "no material change", snapshot not duplicated.
4. Cost test: ledger decrements; job skips when zero.

## Acceptance criteria
- [ ] With key unset: profiles build from stats alone; UI hides LLM fields;
      nothing errors.
- [ ] With key set: profile contains ≥1 quoted phrase per LLM section, each
      linking to a stored permalink.
- [ ] Nightly run stays under $1 at default models (ledger asserted in test
      with recorded token counts).
- [ ] Update log gains ≤1 line/night/sub.

## Verification
```bash
./run.sh check && ./run.sh digest --rebuild-profile smallbusiness --dry-run
```
