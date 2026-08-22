# Security Policy

## Reporting

Use GitHub **Private Vulnerability Reporting** on this repository — do not
open public issues for security reports.

## Scope

Signal Engine is a single-operator, localhost tool. In scope:

- Anything that exfiltrates collected data off the machine
- Any code path that authenticates to or writes to Reddit
- Secret leakage (API keys reaching logs, DB, fixtures, or git history)
- SQL injection through user-supplied search queries into FTS5

Out of scope: Reddit-side rate-limiting behavior of the operator's own IP.

## Hygiene rules enforced in review

- `.env` is gitignored; `.env.example` ships empty values only
- No live credentials in tests or fixtures; network calls are mocked
- The LLM budget ledger never logs prompt content
