# RESEARCH.md — verified findings this product is built on

All findings verified live on **2026-08-22/23** unless noted. Every design
decision in the PRD traces back to a line here.

## 1. Reddit public RSS feeds — VERIFIED WORKING

- Appending `.rss` to subreddit / post / comment URLs returns valid **Atom**
  feeds with no API key and no login. Verified live against `r/news`.
- Post feed entry fields: title, thread permalink, id (`t3_…`), published +
  updated timestamps, author (`/u/name`), category (subreddit). Self-text
  posts include body HTML; link posts contain only Reddit's attribution footer.
- Comment feed (`.rss` on a post comments URL): first entry is the submission,
  then each comment with author, comment permalink, timestamp, and full
  comment body HTML.
- Authenticated/private feed params (`?feed=…&user=…`) are breaking as of
  July 2026 — we rely only on public feeds.

## 2. Rate limits & IP reputation — THE LOAD-BEARING CONSTRAINT

- Reddit publishes **no official unauthenticated per-IP rate limit**. Some
  developers sustain ~1 req/sec with `Retry-After` handling; others get 403s.
- Access is gated by **IP reputation**: datacenter/VPS/cloud egress
  (Railway, AWS, generic VPS) is widely reported blocked with 403 "Blocked"
  or 429 (Miniflux #1432, RSS-Bridge #4067/#4278, last30days-skill #899).
- **Consequence:** the fetcher runs on the user's residential connection,
  paced conservatively (default 1 request / 45–60 s), with exponential
  backoff on 429/403 and a full stop-breaker after repeated blocks.
  This kills the "host it on Railway" idea from the source guide — that
  guide's own hosting choice would get its reading side blocked.

## 3. Legal / policy posture — WHY WE ONLY READ, AND POLITELY

- Reddit User Agreement (eff. 2026-07-01): scraping without prior written
  consent is prohibited; conditional permission to crawl per robots.txt.
  Account selling/transfers prohibited without written approval.
- Public Content Policy (upd. 2024-05-10): non-commercial sharing welcomed;
  commercial use needs a license ("talk to us"). Reddit sued Anthropic
  (Jun 2025, unresolved) and Perplexity et al. (Oct 2025; motion to dismiss
  mostly rejected Jul 31 2026) over scraping.
- Sitewide Rules: Rule 2 bans spam/"content manipulation", Rule 5 requires
  authenticity. r/Entrepreneur explicitly bans AI-generated posts AND all
  self-promotion outside weekly threads; r/smallbusiness and r/sidehustle
  similar. Reddit is rolling out LLM moderation ("Rules Hub") in 2026 and
  cracking down on "AI marketing slop".
- **Consequence:** Signal Engine is a personal, non-commercial research
  instrument: polite RSS reads from a home IP, human reads the output,
  distribution happens through channels the user owns (site, newsletter,
  transparent participation). No posting automation, ever. If this ever
  scales commercially, switch ingestion to the official Data API free tier
  (legacy OAuth limit: 60 req/min; commercial tier ~$0.24/1k calls).

## 4. The source guide ("reddit sales system") — assessed 2026-08-22

- Author @everestchris6 (~24k followers) runs atonomi.ai, an AI automation
  agency; the guide is a lead-magnet funnel. No verified income claims.
- Technically accurate parts: RSS trick, model lineup (Claude Opus 5 real,
  released 2026-07-24; Sonnet 5 $2/$10 per MTok; Haiku 4.5 $1/$5; Gemini
  2.5 Flash-Lite $0.10/$0.40; Kimi K3 real, $3/$15), <$100/mo compute math.
- Broken parts: buying karma'd accounts (bannable), mass AI-drafted replies
  (astroturfing under Rules 2/5), cloud-hosted fetching (IP-blocked),
  "passive" framing (it's a part-time job), target subs already ban the tactic.
- Nous Research's Hermes Agent is real (MIT, self-hostable, Telegram gateway)
  but unnecessary here — we don't need an always-on chat agent, just cron jobs.

## 5. Market signal

- GummySearch — the leading SaaS Reddit audience-research tool ($29–199/mo,
  thousands of users) — **shut down 2025-11-30**. Demand existed; the gap is
  open for a lean self-hosted tool whose cost basis is ~$0.
- Whop seller economics (verified docs): 2.7% + $0.30 domestic card — viable
  checkout when the user later sells a product discovered via this engine.

## 6. Explicitly unverified / do-not-rely

- Any official unauthenticated rate-limit number (none exists).
- Post-2023 "100 QPM free API tier" figure (unconfirmed on official pages).
- 2026 developments in Reddit v. Anthropic (nothing found).
