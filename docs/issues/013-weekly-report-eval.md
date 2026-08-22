# Issue 013 — Weekly report + Precision@10 eval harness

**Milestone:** M3 · **Depends on:** #008 · **Size:** M

## Why
Closes the learning loop (KPI-3): the operator's judgment about which
flagged threads described real problems gets captured, measured, and fed
back into thresholds/lexicons. Also ships the Monday weekly report that
answers "what changed in what people are asking for."

## Scope
- Eval capture UI: on `/pains/<id>` and digest intent queue, two buttons
  ("real problem" / "noise") writing to `eval_marks(ref_type, ref_id,
  verdict, marked_at)`; one click, no forms.
- `reporting/weekly.py` part 2: Monday report — top clusters this week vs
  last (risers/fallers/new), new distinctive phrases, intent-flag volume,
  Precision@10 computed from marks (most recent 10 flags per week), fetch
  health summary; rendered to dashboard + markdown file.
- Threshold tuning notes: if P@10 <0.7 two weeks running, report prints a
  recommendation (raise intent cutoff / tighten cluster threshold).

## Tasks
1. Mark-capture endpoint tests; idempotent per ref+week.
2. Report golden-file test on fixture DB spanning 14 days.
3. PR body: first real report pasted after M1 data has accumulated.

## Acceptance criteria
- [ ] Operator can mark 10 items in <60 seconds (pure HTMX, no reload).
- [ ] Weekly report includes P@10 with the exact sample it was computed on.
- [ ] Report exists every Monday via cron entry in `docs/crontab.txt`.
- [ ] Marks are exportable as CSV (`./run.sh report --export-marks`).

## Verification
```bash
./run.sh check && ./run.sh report --weekly --dry-run
```

## Out of scope
Automatic threshold changes (report recommends, operator decides).
