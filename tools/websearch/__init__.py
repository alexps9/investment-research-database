"""Lightweight web-search tools (no API key required).

Used for cross-verification: given a short claim/summary, find candidate
*primary* source links (official blogs / tier-1 press) so an agent can confirm
an event and attach the original report. The agent decides which candidate (if
any) actually matches — these tools only fetch + deterministically pre-filter.

Ported from the alert pipeline's ``verifier.py``; the Bedrock "pick the right
source" step is intentionally dropped so the LLM judgement lives in the agent.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

TIMEOUT = 10.0

# Authoritative first-hand / tier-1 press domains worth surfacing as "primary".
PRIMARY_DOMAINS = [
    "about.fb.com", "blog.google", "openai.com", "anthropic.com",
    "nvidia.com", "microsoft.com", "apple.com", "amazon.com",
    "reuters.com", "bloomberg.com", "theinformation.com", "wsj.com",
    "ft.com", "techcrunch.com", "theverge.com", "arstechnica.com",
    "cnbc.com", "nytimes.com", "semafor.com", "wired.com",
    "ec.europa.eu", "gov.uk", "whitehouse.gov",
]

# "据路透社报道" → reuters.com, so we can prefer the explicitly-cited outlet.
CITED_SOURCE_MAP = {
    "路透社": "reuters.com", "路透": "reuters.com", "Reuters": "reuters.com",
    "彭博": "bloomberg.com", "彭博社": "bloomberg.com", "Bloomberg": "bloomberg.com",
    "华尔街日报": "wsj.com", "WSJ": "wsj.com",
    "金融时报": "ft.com", "FT": "ft.com",
    "The Information": "theinformation.com", "CNBC": "cnbc.com",
    "纽约时报": "nytimes.com", "TechCrunch": "techcrunch.com", "The Verge": "theverge.com",
}


async def search_web(query: str, max_results: int = 8) -> dict[str, Any]:
    """Free DuckDuckGo HTML search. Returns ``{"results": [{title, url}, ...]}``."""
    if not query or not query.strip():
        return {"results": []}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            )
    except httpx.RequestError as exc:
        return {"error": "search_unreachable", "detail": str(exc), "results": []}

    results: list[dict[str, str]] = []
    for m in re.finditer(
        r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>',
        resp.text,
    ):
        title = re.sub(r"<[^>]+>", "", m.group(2))
        results.append({"title": title, "url": m.group(1)})
        if len(results) >= max_results:
            break
    return {"results": results}


def _is_primary(url: str) -> bool:
    if not any(d in url for d in PRIMARY_DOMAINS):
        return False
    path = re.sub(r"https?://[^/]+", "", url).rstrip("/")
    return bool(path) and path not in ("/", "/en-us", "/en")


def _cited_domain(text: str) -> str | None:
    m = re.search(r"据([^报]{1,20}?)报道|according to ([A-Za-z\s]+)", text)
    if not m:
        return None
    cited = (m.group(1) or m.group(2) or "").strip()
    return CITED_SOURCE_MAP.get(cited)


async def find_primary_source(summary: str, max_candidates: int = 5) -> dict[str, Any]:
    """Search for candidate primary sources that may have reported ``summary``.

    Returns ``{"candidates": [{title, url, domain}, ...]}`` (already filtered to
    authoritative domains). The caller/agent decides which one truly matches the
    event — an empty list means no primary source was found.
    """
    results = (await search_web(summary)).get("results", [])
    cited = _cited_domain(summary)
    candidates: list[dict[str, str]] = []
    for r in results:
        url = r.get("url", "")
        if not _is_primary(url):
            continue
        if cited and cited not in url:
            continue
        domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
        candidates.append({
            "title": r.get("title", ""),
            "url": url,
            "domain": domain.group(1) if domain else "",
        })
        if len(candidates) >= max_candidates:
            break
    return {"candidates": candidates}


__all__ = ["search_web", "find_primary_source"]
