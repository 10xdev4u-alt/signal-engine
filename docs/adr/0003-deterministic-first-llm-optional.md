# ADR-0003: Deterministic core; LLM layers are additive and capped

Status: accepted · Date: 2026-08-22

## Context

LLM calls add cost, nondeterminism, and a third-party dependency to every
analyzed item. Most of the signal — frequency, repetition, ask-patterns,
frustration lexicon — is computable deterministically at zero cost. The
source guide's "<$100/month" math only held because cheap models did volume
reads while premium models orchestrated sparingly.

## Decision

The analysis core is pure Python + SQLite and must run usefully with no API
key. LLM capabilities (profile narratives, intent re-scoring, weekly report
narrative) are additive layers behind a `Provider` interface with a persisted
hard monthly budget ledger. Removing the key changes which fields render,
never whether the system runs.

## Consequences

- Every LLM claim in profiles must quote source text with a permalink;
  schema-validated output or the update is rejected.
- Cost regressions are impossible to hide: the ledger is checked before each
  call and jobs degrade visibly when the cap is hit.
