# ADR folder — architecture decision records

**Milestone:** M0 · **Area:** docs · **Size:** S

## Why
Our two hardest-won research lessons must outlive every contributor's memory.

## Scope
- `docs/adr/0001-rss-only-never-post.md`: read-only public feeds; posting,
  login, or draft-for-paste features rejected on principle (RESEARCH §3).
- `docs/adr/0002-local-first-residential-ip.md`: fetcher runs on operator's
  machine; cloud-hosted fetching rejected due to IP-reputation blocking
  (RESEARCH §2); official-API fallback pre-designed behind FeedSource.
- `docs/adr/0003-deterministic-first-llm-optional.md`: analyzer core is pure
  code; LLM layers additive, budget-capped, removable without control-flow change.
- `docs/adr/template.md` for future records.

## Acceptance criteria
- [ ] Three ADRs + template merged; each cites RESEARCH sections.
- [ ] PRD/ARCHITECTURE link the ADRs where decisions are referenced.
