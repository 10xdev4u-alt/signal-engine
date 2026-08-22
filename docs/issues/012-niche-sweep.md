# Issue 012 — Niche discovery sweep across broad seed subs

**Milestone:** M3 · **Depends on:** #008 · **Size:** M

## Why
The operator has no niche yet (PRD mission #1). This is "agent one" rebuilt
legitimately: find where desperate, already-spending people cluster — then
aim the whole engine there.

## Scope
- Seed list (~15 subs) in config under group `discovery`: e.g. smallbusiness,
  Entrepreneur (read-only observation is fine), sidehustle, productivity,
  adhd_anonymous-adjacent health subs chosen at implementation time,
  personalfinance, sales, freelance, teachers, nurses, sysadmin, dogs,
  running, diy, wedding planning — final list justified in PR body.
- Fetching respects pace budget globally: discovery subs get a slower lane
  (e.g. every 2h) so core subs keep priority.
- `reporting/weekly.py` part 1: cluster pains ACROSS subs (same clustering
  code, cross-corpus); desperation score = frequency × frustration ×
  monetization signals regex ("pay", "spent $", "worth it", "hire someone");
  rank clusters; annotate source subs; regulated-domain classifier flags
  medical/legal/financial-advice clusters into a separate caution section,
  excluded from ranking (PRD US5).

## Tasks
1. Cross-sub cluster merge tests on synthetic multi-sub fixtures.
2. Caution-classifier tests (keyword+context rules; conservative = over-flag).
3. Manual PR-body run on real week-one data; top-10 table pasted.

## Acceptance criteria
- [ ] Weekly ranking table exists with ≥5 clusters, each showing quotes
      from ≥2 different subs or an explicit single-sub label.
- [ ] Regulated clusters appear ONLY in caution section.
- [ ] Discovery fetch lane provably can't starve core subs (pace budget
      unit test).
- [ ] Output names concrete next step per top cluster ("point engine here:
      add these 3 niche subs").

## Verification
```bash
./run.sh check && ./run.sh sweep --dry-run
```
