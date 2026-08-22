# CONTRIBUTING — encode the agentic PR loop

**Milestone:** M0 · **Area:** docs · **Size:** S

## Why
Any agent or human joining must follow the exact same religion: issue →
branch → implement → verify → PR → review → merge → clean.

## Scope
- `CONTRIBUTING.md` codifying: pick lowest open unblocked issue; branch
  `issue/<NN>-<slug>`; conventional commits with EXACTLY six words in the
  subject after the type (hyphenated terms = one word); co-author trailer
  required; `./run.sh check` green before push; PR description lists each
  acceptance criterion with evidence; one approval to merge; delete branches
  after merge and `git remote prune origin`.

## Acceptance criteria
- [ ] CONTRIBUTING.md merged, linked from README.
- [ ] Contains ≥3 concrete six-word commit examples.
