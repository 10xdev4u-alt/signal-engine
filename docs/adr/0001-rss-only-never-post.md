# ADR-0001: RSS-only ingestion; the engine never posts

Status: accepted · Date: 2026-08-22

## Context

The source guide that inspired this project ("reddit sales system") uses its
agent to draft replies and posts that a human pastes into Reddit to funnel
traffic. Our research (docs/RESEARCH.md §3) shows where that road ends:
Reddit Rules 2 and 5 prohibit spam/content manipulation and require
authenticity; r/Entrepreneur explicitly bans AI-generated posts and all
self-promotion outside weekly threads; Reddit ships LLM moderation ("Rules
Hub") against AI marketing slop in 2026 and bans networks for coordinated
inauthenticity.

## Decision

Signal Engine reads public `.rss` feeds and nothing else. It has no login,
no credentials for Reddit, no posting path, and no feature that drafts
content intended to be pasted into Reddit threads. Distribution belongs to
channels the operator owns.

## Consequences

- The codebase cannot grow an astroturfing feature without violating this
  ADR; such PRs are rejected on sight (AGENTS.md standing rules).
- We stay inside Reddit's Public Content Policy posture for personal,
  non-commercial research at polite pacing.
- If usage ever becomes commercial-scale reading, the sanctioned path is the
  official Data API (ADR-0002's adapter boundary makes that swap cheap).
