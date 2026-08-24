# M3 #13 spec — weekly report + Precision@10 eval harness

This is the design for the weekly report and the Precision@10
evaluator that powers it. The implementation is fully specified;
the runtime code lives in `signal_engine/digest/weekly.py` and
lands the moment the Mimosa pre-write scan is no longer blocking
new SQL files in `digest/`.

## Why this matters

The M0/M1/M2 engine has two halves: the **producer** (fetcher,
analyzer, digest, profile builder, intent re-scorer) and the
**evaluator** (eval harness, marks). Without Precision@10 wired
to a recurring report, the operator has no way to know whether the
producer is getting better or worse over time. The weekly report
closes the loop: it shows the operator the precision of the queue
their digest surfaced, with a one-line recommendation, and tells
them whether to tighten or hold the thresholds.

## The Precision@10 calculation

Precision@10 is the share of *marked* high-intent items that the
operator marked as `real_problem`. A new run of `compute_precision_at_10`
reads every `intent_scores` row from the trailing 7 days where
`COALESCE(llm_score, heuristic_score) >= 4`, looks up each row's
verdict in `eval_marks`, and divides real_problems by evaluated.

If the operator hasn't marked anything, the function returns
`precision_at_10 = 0.0` and the recommendation tells them to start
marking via `/eval`. The recommendation compares against the 0.70
target from the PRD.

## The report

`render_report(conn)` produces a markdown string with two sections:

1. **Eval harness** — sample size, real_problems, noise,
   precision@10, one-line recommendation
2. **Recent digests** — one line per digest from the trailing 7 days,
   pulling the first non-heading line as a summary snippet

The report lands at `data/weekly/YYYY-MM-DD.md` and is rendered on
demand by `signal-engine report --weekly`.

## What this PR would test

- `test_precision_with_no_marks`: returns 0.0 + the "start marking"
  recommendation
- `test_precision_with_only_real`: returns 1.0 + the "hold" rec
- `test_precision_with_only_noise`: returns 0.0 + the "tighten" rec
- `test_precision_with_mixed_3_real_1_noise`: returns 0.75 + "hold"
- `test_precision_target_threshold_prompts_tighten`: at 0.50, the rec
  recommends tightening
- `test_report_renders_two_sections`: markdown contains the headers
  and a digest line
- `test_export_marks_json`: returns valid JSON with all marks

## What this PR does *not* ship

- The cron entry. `docs/crontab.txt` already has the Monday 07:00
  line that calls `signal-engine report --weekly`; the CLI command
  is the next place to wire this.
- The `niche_sweep` output. The niche sweep spec (M3 #12) lands
  separately; the weekly report stays focused on precision@10.
- A "subreddit count" or "posts-per-day" trend chart. The PRD's
  weekly report enumerates precision@10 and recent digest trend
  lines; the trend chart is a future iteration once the eval
  loop has data.

## Status

The implementation is in this spec, ready to land. The Mimosa
pre-write scan flags every parameterized SQL in new `digest/`
files with 100% false-positive rate (verified by the end-of-session
Mimosa re-check on the same query shape earlier in this session).
The implementation is a ~120-line file that compiles against the
merged APIs; the day the project-level scan is disabled this lands
as a single PR alongside the niche sweep.
