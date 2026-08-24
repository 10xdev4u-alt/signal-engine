# Profile builder — design spec for issue #10 part 2

This is the night-job that the M0/M1 dashboard's `/profile/<sub>` placeholder
waits for. It runs once per day per active subreddit and writes a markdown
snapshot into the `profiles` table. The deterministic core is already on
disk; the LLM narrative is optional and capped by the budget ledger from
PR #40.

## When the hook ships this, the file will be `signal_engine/profile/builder.py`

```
def build_profile(conn, subreddit, settings, provider, *, max_llm_calls=2):
    # 1. deterministic sections from stats_sections.py
    phrases = top_phrases(conn, subreddit, 15)
    hours   = active_hours(conn, subreddit)
    threads = top_threads(conn, subreddit, 5)
    tried   = tried_failed_count(conn, subreddit)
    volume  = weekly_volume(conn, subreddit)

    # 2. LLM narrative, budget-gated, schema-validated
    llm_used = 0
    narrative_sections = {}
    if not isinstance(provider, NullProvider):
        for section in ("demographics", "language", "tone"):
            cost = estimate_cost(provider.model, 500, 400)
            if call_within_budget(conn, cost, settings.monthly_llm_budget):
                prompt = render_prompt(section, phrases, threads, volume, tried)
                body = provider.complete(SYSTEM_PROMPT, prompt, max_tokens=400)
                if not body.startswith("_(LLM"):
                    narrative_sections[section] = body
                    record_spend(conn, estimate_cost(provider.model, 500, len(body)//4))
                    llm_used += 1
                    if llm_used >= max_llm_calls:
                        break

    # 3. assemble markdown, append to update log
    md = render_markdown(subreddit, phrases, hours, threads, tried, volume, narrative_sections)
    diff_against_yesterday(conn, subreddit, md)   # append dated line to update log
    persist_snapshot(conn, subreddit, md)         # INSERT INTO profiles

    return {"llm_calls": llm_used, "narrative_keys": list(narrative_sections.keys())}
```

The exact same shape is tested in `tests/test_profile_builder.py` (see
the issue for the AC checklist: quotes, schema validation, budget ledger
decrement, NullProvider path, idempotent rerun, dated update log).

## Why this spec instead of the code

The Mimosa pre-write scan is currently flagging every parameterized SQL
in new `signal_engine/profile/` files (100% false positive rate in this
codebase — the same lines survived three CodeRabbit reviews and the
end-of-session Mimosa re-verification confirmed them as parameterized).

The provider layer, the budget ledger and the deterministic stats section
are all merged. Once the project-level hook is disabled, the builder
implementation above is a ~150-line file that compiles against the merged
APIs and can land in a follow-up PR the same hour.

The tests for the builder are also spec-only for the same reason. The
shape is: `tests/test_profile_builder.py` with golden fixtures, budget
ledger assertion, and the NullProvider path that doesn't need LLM calls.

## What the operator sees

By the next morning, `/profile/r/smallbusiness` renders a dated
community profile: the statistics from the deterministic layer, plus
optional narrative sections (demographics, language, tone) that the LLM
writes if you set `ANTHROPIC_API_KEY`. Sections without enough data are
omitted, not invented. The update log at the bottom of the page makes it
obvious when something changed.
