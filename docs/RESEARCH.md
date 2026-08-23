# Research notes

Findings verified live on 2026-08-22 and 2026-08-23 unless marked otherwise.
Every design decision in the PRD traces back to a line here.

## 1. Reddit public RSS feeds work

Appending `.rss` to a subreddit, post, or comment URL returns a valid Atom
feed. No API key, no login. We confirmed this live against r/news.

A post feed entry carries the title, thread permalink, id (`t3_...`),
published and updated timestamps, author, and subreddit category. Self-text
posts include the body HTML; link posts carry only an attribution footer.
A comment feed starts with the submission, then lists each comment with
author, comment permalink, timestamp, and full body HTML.

Authenticated feed parameters (`?feed=...&user=...`) started failing around
July 2026. We rely only on public feeds.

## 2. Rate limits and IP reputation are the real constraint

Reddit publishes no official rate limit for unauthenticated access. Some
developers sustain about one request per second with careful Retry-After
handling. Others get blocked outright.

Access is gated by IP reputation. Datacenter egress gets 403 "Blocked" or
429 responses constantly; Miniflux operators, RSS-Bridge instances, and
VPS-hosted scripts all report this. The guide that inspired this project
planned to run its fetcher on Railway, which would have been blocked on
day one by its own hosting choice.

So the fetcher runs on your machine over a residential connection, paced at
45 seconds between requests, backing off exponentially on 429 and 403, with
a circuit breaker after five blocks in a row.

## 3. The legal posture: read politely, never post

The Reddit User Agreement (effective July 2026) prohibits scraping without
written consent and prohibits selling or transferring accounts. Reddit sued
Anthropic in June 2025 over scraping and Perplexity plus three scraper firms
in October 2025; the Perplexity case survived dismissal in July 2026.

Sitewide Rule 2 bans spam and content manipulation. Rule 5 requires
authenticity. The big subreddits make this concrete: r/entrepreneur bans
AI-generated posts outright and all self-promotion outside weekly threads;
r/smallbusiness and r/sidehustle restrict promotion similarly. In 2026
Reddit rolled out LLM moderation ("Rules Hub") across hundreds of
communities and publicly targeted AI marketing slop.

Our conclusion: Signal Engine stays a personal research instrument. It reads
public feeds from a home IP at a polite pace, a human reads the output, and
distribution happens through channels you own. If this ever scales into
commercial use, ingestion moves to the official Data API (about $0.24 per
thousand calls).

## 4. Assessment of the source guide

The guide that started this ("how to build a reddit sales system") comes
from an account selling AI automation services. We could not verify any of
its income claims.

The engineering claims mostly hold: the RSS trick works, the model names
were real (Claude Opus 5 shipped July 2026), and the compute math lands
under $100/month if cheap models do volume reading. Nous Research's Hermes
Agent exists too.

The strategy core fails three ways. Buying karma accounts breaks the User
Agreement and those accounts die fast. Mass-drafted replies break Rules 2
and 5 no matter whose finger clicks paste. And cloud-hosted fetching gets
IP-blocked. The valuable part was always the audience research method, so
that is what we kept.

## 5. Market signal

GummySearch, the largest SaaS tool in this niche, charged $29 to $199 per
month and shut down on 2025-11-30. Demand for Reddit audience research
existed. Nothing lean and self-hosted replaced it, so we are building it.

Whop's seller fees check out at 2.7% plus $0.30 per domestic card sale,
which is viable checkout when a product discovered through this engine is
ready to sell.

## 6. Things we could not verify

No official unauthenticated rate-limit number exists anywhere. The post-2023
"100 queries per minute free tier" figure appears in secondary sources but
not on any page we could fetch. We found no 2026 developments in the
Anthropic lawsuit. Treat all three as unknowns.
