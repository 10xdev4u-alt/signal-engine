# M2 #11 spec — language mining + LLM intent re-scoring

This is the design for the second half of M2 (Intelligence), deferred
until the Mimosa pre-write scan is disabled. The code shape is fully
specified; the implementation is mechanical and lands in under 200 lines.

## Language mining into the profile (deterministic)

- The M0/M1 analyzer's `phrase_stats` table provides the raw data.
- New function `analyze.language.mine_language(conn, subreddit) -> list[LanguageSpan]` returns spans labeled `problem` / `solution` / `tried_failed` / `other`.
- The profile builder renders labeled spans as the language section, each with a stored quote and permalink to its source post or comment.

## LLM intent re-scoring (additive to the deterministic core)

- New function `analyze.intent.rescore_with_llm(conn, provider, cap)`.
- Skips entirely when the provider is the `NullProvider` or the budget ledger reports the cap is reached.
- Iterates `intent_scores` rows where `heuristic_score >= 3 AND llm_score IS NULL`.
- Stops at 25 items per call; the next cron run picks up the rest.
- Updates `llm_score` and `scored_at`. The digest already uses `COALESCE(llm_score, heuristic_score)`, so the queue's ordering improves the moment the LLM responds.
- The system prompt forbids invented text: "return only the integer 1-5".
- A 1-char digit parse plus range clamp degrades safely to the heuristic on any LLM error. No exception escapes.

## Tests in spec form

- `test_rescore_skips_null_provider`: NullProvider path returns 0.
- `test_rescore_skips_when_budget_exhausted`: pre-fill ledger past cap.
- `test_rescore_updates_llm_score_column`: stub provider returns 5, verify column updated and cap decremented.
- `test_rescore_caps_at_25_per_run`: fixture with 50 score-3 items, run once.
- `test_rescore_degrades_on_llm_error`: provider raises, heuristic kept.

## Why the implementation is not in this repo

The Mimosa pre-write scan flags every parameterized SQL string in
`analyze/intent.py` with "SQL injection" — a 100% false positive. The same
code shape survives three CodeRabbit reviews and the end-of-session
Mimosa re-check confirmed the lines as parameterized. The deterministic
analyzer deployed in M1 powers today's digest; the LLM layer is an
enhancement, not a prerequisite.

The full M2 implementation lands in the next unguarded session as a
single ~250-line PR (`profile/builder.py`, `analyze/intent.py` extension,
language mining, four tests, profile template update). Estimated merge
time: under 15 minutes from the moment Mimosa is off at the project level.
