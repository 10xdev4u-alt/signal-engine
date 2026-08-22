# SECURITY policy + secret hygiene

**Milestone:** M0 · **Area:** docs · **Size:** S

## Scope
- `SECURITY.md`: private vulnerability reporting via GitHub Security
  Advisories; scope (this tool stores data locally; report anything that
  exfiltrates or posts).
- Confirm `.env` gitignored, secret scanning enabled, no keys ever in
  fixtures/tests.

## Acceptance criteria
- [ ] SECURITY.md merged.
- [ ] `git check-ignore .env` passes; repo history contains no token patterns
      (spot-checked).
