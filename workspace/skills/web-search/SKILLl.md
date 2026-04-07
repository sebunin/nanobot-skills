---
name: free-web-search
description: Use when the agent needs live web search and should prefer free or self-hosted options over paid APIs; especially for general web lookup, current information, source gathering, or when a paid search provider is unavailable or quota-limited.
---

# Free web search

## Goal

Find live web sources with zero or minimal cost, then answer with the best available evidence.

## Decision order

1. Use `SEARXNG_URL` if it is configured.
2. Use DuckDuckGo Instant Answer only for simple factual lookups, definitions, conversions, and other compact answers.
3. Use Google Programmable Search only if it is already enabled and the query fits the free quota.
4. Avoid paid search providers unless the user explicitly accepts the cost.
5. Do not scrape search-engine HTML as the primary method. Use it only as a last resort when no API or configured endpoint exists.

## Search workflow

1. Rewrite the user query into 2–3 search variants.
2. Search the most reliable source first:
   - official docs
   - vendor docs
   - standards
   - primary sources
   - recent coverage for news/current topics
3. Collect 3–5 strong results.
4. Prefer recent pages, authoritative domains, and direct evidence.
5. Remove duplicates and weakly relevant pages.
6. Answer with a short synthesis and include the source URLs or titles the agent used.

## SearXNG

Use SearXNG for general web search when available.

Example request:

```bash
curl 'https://searx.example.org/search?q=your+query&format=json&language=en&safesearch=1'
```

Recommended parameters:

- `q` — search query
- `format=json` — machine-readable output
- `language` — user language when useful
- `safesearch=1` — default safe mode
- `categories=general` — general web search
- `time_range=day|month|year` — when recency matters

If the instance does not support JSON, fall back to the instance’s available output formats or another configured endpoint.

## DuckDuckGo Instant Answer

Use this only when the question can be answered without full web search results.

Good fit:
- definitions
- conversions
- formulas
- compact factual lookups
- quick entity facts

Not a good fit:
- broad web search
- news monitoring
- multi-source research
- result-heavy queries

## Google Programmable Search

Use only when it is already configured and the free quota is acceptable.

Keep requests narrow and cache results when possible.

## Answering rules

- Be explicit when the search coverage is partial.
- Prefer exact dates over relative dates.
- Quote sparingly.
- Separate facts from inference.
- When sources disagree, say so.
- Return the top result set first, then a brief summary.

## Failure handling

If no usable results are found:
- say what was searched
- say what was missing
- suggest a narrower query or a different endpoint

## Notes for the agent

The best default for a free general-purpose search stack is SearXNG. DuckDuckGo is best kept as a lightweight fallback for narrow factual questions.
