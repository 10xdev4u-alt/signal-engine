# Contributing

This repo runs an agentic, issue-driven loop. Every change is one issue =
one branch = one PR. No exceptions, including maintainers.

## The loop

1. **Pick** the lowest-numbered open issue whose dependencies are merged
   (see `docs/issues/BACKLOG.md`). Never work outside an issue — if scope
   grows, stop and file a new issue.
2. **Research inside the issue** before coding: re-read its *Why*, the
   linked RESEARCH/PRD/ADR sections, and the code it touches. If reality
   contradicts the docs, fix the docs in the same PR and say so.
3. **Branch** off `main`: `issue/<NNN>-<slug>`.
4. **Implement** to the letter of the issue's Scope/Tasks. Type hints
   everywhere; comments only for constraints code can't show.
5. **Validate locally**: `./run.sh check` (ruff + pytest) must be green.
6. **Commit** with conventional commits. The subject after the type is
   EXACTLY SIX WORDS. Hyphenated terms count as one word.
7. **Push, open PR** with `Closes #NNN`, every acceptance criterion listed
   with evidence (paste command output), and any deviations justified.
8. **Review**: one approving review required (branch protection enforces
   this; CI `check` must be green).
9. **Merge** (`--merge`, no squash), delete the branch, `git remote prune
   origin`, update the BACKLOG row.

## Six-word commit subjects

```
feat: add run script for local validation
test: check version string and cli status
docs: add the initial architecture decision records
```

Count before you commit: `echo "<subject>" | sed 's/^[a-z]*: //' | wc -w`
must print `6`.

## Standing rules

- Never add Reddit posting/login/auth features (ADR-0001).
- No cloud-hosted fetching path (ADR-0002).
- LLM calls only via the Provider interface + budget ledger (ADR-0003).
- No live network in unit tests; fixtures and mocks only.
- Schema changes = new migration file; never edit applied migrations.
- Co-author trailer (`Co-authored-by:`) on every commit.
