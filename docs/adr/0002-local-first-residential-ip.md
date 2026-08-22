# ADR-0002: Local-first fetching on residential IP; cloud rejected

Status: accepted · Date: 2026-08-22

## Context

Reddit gates unauthenticated access by IP reputation. Developer reports
(docs/RESEARCH.md §2) show consistent 403 "Blocked" / 429 responses from
datacenter egress — VPS hosts, RSS-Bridge instances, Miniflux servers. The
source guide's own plan (agent hosted on Railway) would have its reading
side blocked by Reddit regardless of pacing discipline.

## Decision

The fetcher runs on the operator's machine over a residential connection,
paced at ≥45 s between requests with exponential backoff, `Retry-After`
honoring, and a circuit breaker. No VPN or proxy rotation exists in this
codebase — IP-reputation evasion is out on principle, not just risk math.
All Reddit-format knowledge lives behind the `FeedSource` protocol
(`signal_engine/sources/`), so a sanctioned official-Data-API source can
replace RSS without touching callers.

## Consequences

- Zero hosting cost; data stays local (privacy default).
- Collection stops when the operator's machine sleeps — acceptable for a
  research instrument; the digest notes collection gaps rather than hiding them.
- Adding any cloud-fetch deployment target requires revisiting this ADR first.
