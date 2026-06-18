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


_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://duckduckgo.com/",
}

# DuckDuckGo serves several no-API-key HTML front-ends; their markup differs and
# any one of them can rate-limit / block a given server IP, so we try them in
# order and parse with several patterns. The first endpoint that yields hits wins.
_DDG_ENDPOINTS = (
    "https://html.duckduckgo.com/html/",
    "https://lite.duckduckgo.com/lite/",
    "https://duckduckgo.com/html/",
)

# Multiple link patterns covering the html (result__a) and lite (result-link /
# bare anchor) layouts.
_RESULT_PATTERNS = (
    re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I),
    re.compile(r'<a[^>]*class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I),
    re.compile(r'<a[^>]+href="(//duckduckgo\.com/l/\?uddg=[^"]+)"[^>]*>(.*?)</a>', re.S | re.I),
)


def _parse_ddg(html: str, max_results: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for pattern in _RESULT_PATTERNS:
        for m in pattern.finditer(html):
            url = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if not url or url in seen:
                continue
            # skip DDG's own ad/redirect chrome that has no real title
            if not title:
                continue
            seen.add(url)
            results.append({"title": title, "url": url})
            if len(results) >= max_results:
                return results
        if results:
            break
    return results


async def search_web(query: str, max_results: int = 8) -> dict[str, Any]:
    """Free DuckDuckGo HTML search (multi-endpoint, multi-pattern, never raises).

    Returns ``{"results": [{title, url}, ...]}``. Tries each DDG front-end until
    one returns hits so a single blocked/rate-limited endpoint doesn't zero out
    web research."""
    if not query or not query.strip():
        return {"results": []}
    last_err: str | None = None
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        for endpoint in _DDG_ENDPOINTS:
            try:
                resp = await client.post(endpoint, data={"q": query}, headers=_BROWSER_HEADERS)
            except httpx.RequestError as exc:
                last_err = str(exc)
                continue
            if resp.status_code != 200:
                last_err = f"status_{resp.status_code}"
                continue
            results = _parse_ddg(resp.text, max_results)
            if results:
                return {"results": results}
    return {"error": "search_no_results", "detail": last_err, "results": []}


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
