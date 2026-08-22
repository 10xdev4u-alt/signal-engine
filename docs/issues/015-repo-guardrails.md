# Repository guardrails configuration record

**Milestone:** M0 · **Area:** infra · **Size:** S

## Why
The protections that make our workflow enforceable should themselves be
documented as a reviewed unit of work.

## Scope (applied at repo bootstrap; this issue records + verifies it)
- `main` branch protection: 1 approval required, stale reviews dismissed,
  force-push and deletion blocked, conversations must resolve.
- `delete_branch_on_merge` enabled; secret scanning enabled.
- Collaborator `the-ai-developer` granted write for reviews/co-authoring.

## Acceptance criteria
- [ ] Protection config matches above (API output pasted in PR).
- [ ] A trial PR proves merge is impossible without approval.
