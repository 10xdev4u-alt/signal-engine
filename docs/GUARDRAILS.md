# Repository Guardrails — applied configuration

Recorded as required by issue #15. All settings verified live on 2026-08-23.

## Branch protection on `main`

| Rule | Value |
|------|-------|
| Required approvals | 1 (`required_pull_request_reviews`) |
| Dismiss stale reviews | yes |
| Required status checks | `check` (CI), strict freshness |
| Force pushes | blocked |
| Branch deletion | blocked |
| Conversation resolution | required |
| Admin bypass | enabled deliberately — owner can act alone if review accounts are unavailable |

## Repo settings

| Setting | Value |
|---------|-------|
| Delete head branches on merge | enabled |
| Secret scanning | enabled |
| Collaborators | `the-ai-developer` (write) — reviews and co-authoring |

## Proven

- PR #24/#25 merged only after second-account approval.
- PR #26 (deliberate lint break) went RED and was closed unmerged.
