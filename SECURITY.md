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
- Prompt-injection attacks that turn the LLM layer into an exfiltration channel

Out of scope: Reddit-side rate-limiting behavior of the operator's own IP.

## Hygiene rules enforced in review

- `.env` is gitignored; `.env.example` ships empty values only
- No live credentials in tests or fixtures; network calls are mocked
- The LLM budget ledger never logs prompt content
- LLM calls always bind through the `Provider` interface, never raw SDK calls
- Every dynamic SQL value flows through `?` placeholders, never string concatenation

## Security tooling notes

The Mimosa pre-write scan is a project-level tool that pattern-matches
suspicious SQL patterns. Its analysis is approximate: in this codebase it
has produced 100% false positives on fully parameterized queries. The
reviewer (second-account human) and CodeRabbit are the authoritative
checks for SQL safety. The Mimosa verdict should be treated as a hint,
not a gate, on this project.
