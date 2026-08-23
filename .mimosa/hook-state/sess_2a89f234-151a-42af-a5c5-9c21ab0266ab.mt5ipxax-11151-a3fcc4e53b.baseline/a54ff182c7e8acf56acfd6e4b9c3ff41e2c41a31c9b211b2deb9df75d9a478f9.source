# AGENTS.md — the agentic research → issue → PR development contract

This repo is built agent-first: every unit of work is a numbered issue in
`docs/issues/`, and every issue lands as exactly one PR-sized merge.
Any agent session (or human) follows this loop verbatim.

## The loop

1. **Pick** the lowest-numbered open issue whose dependencies are merged
   (see BACKLOG table). Never work outside an issue; if scope grows, stop
   and write a new issue instead.
2. **Research inside the issue** before coding: re-read the issue's *Why*,
   the linked RESEARCH/PRD sections, and the code it touches. If reality
   contradicts the docs, fix the docs in the same PR and say so.
3. **Branch**: `issue/<NN>-<slug>` off `main`.
4. **Implement** to the letter of the issue's Scope/Tasks. Match existing
   style; type hints everywhere; comments only for constraints code can't show.
5. **Verify** against every checkbox in *Acceptance criteria* using the
   issue's *Verification* commands plus `./run.sh check` (ruff + pytest).
   A criterion you cannot verify honestly = PR does not merge; document why.
6. **PR summary** (commit message body or PR description): what changed,
   which ACs pass with evidence (paste command output), any deviations +
   justification, follow-up issues created.
7. **Merge** to `main` with a linear history (`--no-ff` merge of the branch),
   update BACKLOG row status, delete the branch.

## Definition of done (every PR)

- All issue ACs checked with real evidence in the description.
- `./run.sh check` green locally: lint clean, all tests pass.
- No live network in unit tests (fixtures/mocks only); manual smoke steps
  documented in the PR if the issue requires them.
- Docs touched by the change are updated in the same PR.

## Standing rules

- **Never add Reddit posting/login/auth features.** The tool reads public
  feeds only (RESEARCH §3 is law). PRs violating this are rejected on sight.
- No cloud-hosted fetching path may be added (IP-reputation risk).
- LLM calls always route through `llm/base.py` Provider + budget ledger;
  no raw SDK calls elsewhere.
- New deps require justification in the PR body (what it replaces, size).
- Schema changes = new migration file, never edit applied migrations.

## Creating new issues

Copy an existing issue file as the template: Why / Scope / Tasks /
Acceptance criteria / Verification / Out of scope / Size. Add a BACKLOG row
with milestone + dependencies. Issues must stay PR-sized: if an estimate
exceeds ~400 lines of diff, split it.
