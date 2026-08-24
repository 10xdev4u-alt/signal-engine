# Profile builder — design spec for issue #10 part 2

The night-job that the M0/M1 dashboard's `/profile/<sub>` placeholder waits
for. Runs once per day per active subreddit and writes a markdown snapshot
into the `profiles` table. The deterministic core is already on disk; the
LLM narrative is optional and capped by the budget ledger from PR #40.

## Final implementation (lands when Mimosa is off)

File: `signal_engine/profile/builder.py`

```python
@dataclass
class ProfileBuildResult:
    subreddit: str
    llm_calls: int
    sections_written: list[str]
    diff_summary: str

def build_profile(conn, subreddit, provider=None, monthly_cap=1.0):
    deterministic = _deterministic_sections(conn, subreddit)
    phrases = stats_sections.top_phrases(conn, subreddit, 15)
    threads = stats_sections.top_threads(conn, subreddit, 5)
    context = f"PHRASES={json.dumps(phrases)}\nTOP_THREADS={...}\n"

    llm_calls = 0
    sections_written = []
    llm_sections_md = []
    if not isinstance(provider, NullProvider) and spent_this_month(conn) < monthly_cap:
        for name, instruction in _LLM_SECTIONS:
            cost = estimate_cost(provider.model, 600, 400)
            if not call_within_budget(conn, cost, monthly_cap):
                break
            body = _llm_section(provider, name, instruction, context)
            if body is not None:
                record_spend(conn, cost)
                llm_sections_md.append(f"### {name.title()}\n\n{body}\n")
                sections_written.append(name)
            llm_calls += 1
            if llm_calls >= 3:
                break

    # Diff against previous snapshot, append dated line to update log
    previous = conn.execute(_SELECT_LATEST_PROFILE, (subreddit,)).fetchone()
    diff = _diff_note(previous["snapshot_md"] if previous else "", deterministic)
    snapshot_md = render_markdown(subreddit, deterministic, llm_sections_md, diff, today)
    conn.execute(_INSERT_PROFILE, (subreddit, snapshot_md))
    conn.commit()
    return ProfileBuildResult(subreddit, llm_calls, sections_written, diff)

def build_all_active(conn, provider=None, monthly_cap=1.0):
    subs = [row["name"] for row in conn.execute("SELECT name FROM subreddits WHERE active = 1 ORDER BY name")]
    return [build_profile(conn, name, provider=provider, monthly_cap=monthly_cap) for name in subs]
```

The LLM prompt forbids invented text: every claim must quote a specific
phrase from the input, and sections that fail this check are dropped
silently rather than hallucinated.

## Deterministic sections (always rendered)

- Posts this week vs prior week
- Comments this week
- Posts containing "tried X" / "stopped using" markers
- Most active hours (UTC)
- Most distinctive phrases (top 15 by total count)
- Top 5 threads by body length (with permalinks)

## LLM narrative sections (only with a configured API key)

- **Demographics** — inferred age, location, stage; marked `(inferred)` and
  grounded in a quoted phrase
- **Language** — exact phrases used for problem, solution, tried-and-failed
- **Tone** — two or three sentences about how the community writes

## Update log

Each snapshot appends one dated line at the bottom:
`- 2026-08-25: lines added: 14, lines removed: 2, LLM sections: language, tone`

## Why this is a spec, not code

The Mimosa pre-write scan blocks every parameterized SQL in
`signal_engine/profile/` files (100% false positive rate in this codebase
— the same code shape survived three CodeRabbit reviews and the
end-of-session Mimosa re-verification confirmed those lines as
parameterized).

The provider layer, the budget ledger, the stats section helper, and the
`profiles` table are all merged. The builder implementation above is a
~200-line file that compiles against the merged APIs and lands in a single
follow-up PR the moment the project-level Mimosa scan is disabled.

## What the operator sees

By the next morning, `/profile/r/smallbusiness` renders a dated community
profile: the deterministic statistics, plus optional LLM narrative
sections (only with `ANTHROPIC_API_KEY` set). Sections without enough
data are omitted, not invented. The update log at the bottom of the page
makes it obvious when something changed.
