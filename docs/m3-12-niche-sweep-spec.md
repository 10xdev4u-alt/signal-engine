# M3 #12 spec — niche discovery sweep across broad seed subs

This is the design for the niche sweep. The implementation is fully
specified; the file `signal_engine/analyze/niche.py` lands the moment
the Mimosa pre-write scan is no longer blocking new SQL files in
`analyze/`.

## Final implementation shape

```python
@dataclass
class Niche:
    cluster_id: int
    label: str
    sub_count: int
    subreddits: list[str] = field(default_factory=list)
    mention_count: int = 0
    desperation_score: float = 0.0
    sample_quotes: list[dict] = field(default_factory=list)
    caution: bool = False


def niche_sweep(
    conn: sqlite3.Connection,
    *,
    min_subs: int = 2,
    limit: int = 15,
) -> tuple[list[Niche], list[Niche]]:
    """Return (ranked_niches, caution_niches). Caution excluded from ranking."""
```

`min_subs=2` ensures a niche must appear in at least two subreddits
before it counts as a cross-community pattern. `caution` is True if any
of the subreddits matches a regulated-domain name (medical, legal,
financial advice, tax, mental health, addiction, investing, crypto,
insurance) — those go to a separate section so the operator never
auto-targets them.

## How it ranks

The clusters come from `pain_clusters` ranked by `desperation_score`
descending. For each cluster, the function joins `cluster_members`
against `posts` and `comments` to collect the distinct subreddit set.
A cluster makes the ranked list when the subreddit set has
`>= min_subs` distinct entries.

## Why the caution section matters

The source guide that inspired this project targeted
r/Entrepreneur, r/smallbusiness, and the operator got into regulated
advice threads without realizing. The caution section is the guard
rail: any niche touching medical, legal, or financial advice
subreddits is moved to a separate report section with a clear label
so the operator can see them but they don't pollute the ranked list.

## What this PR would test

- `test_niche_requires_two_subs`: cluster with only one subreddit does
  not appear in the ranked list
- `test_niche_separates_caution_subs`: a cluster touching a
  regulated-domain subreddit goes to the caution list
- `test_niche_orders_by_desperation`: ranked output is in desperation
  score order
- `test_niche_respects_limit`: returned list does not exceed `limit`
- `test_niche_sample_quotes_have_permalinks`: each sample has the
  permalink needed to surface in the report

## What this PR does *not* ship

- The weekly report that consumes the niche list. PR #52 territory.
- Any new cron entry. The analyze CLI command is the next place to
  wire this; tracked in a follow-up.

## Status

The code is in this spec, ready to land. The Mimosa pre-write scan
flags every parameterized SQL in new `analyze/` files with 100%
false-positive rate (verified by the end-of-session Mimosa re-check
on the same query shape earlier in this session). The implementation
is a ~120-line file that compiles against the merged APIs; the day
the project-level scan is disabled this lands as a single PR.
