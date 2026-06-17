"""Search + page-fetch utilities for the deep-research agent.

Reuses the repo's free DuckDuckGo `tools/websearch` (no API key) and adds a
lightweight HTML→text page fetcher so researchers can read primary content, not
just snippets. Everything degrades gracefully (never raises) so a single bad URL
can't sink a research run.
"""
from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from tools.websearch import search_web

FETCH_TIMEOUT = 12.0
MAX_PAGE_CHARS = 6000
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Global throttle on concurrent search+fetch bundles across ALL research runs —
# DuckDuckGo + page fetches share one overseas proxy node, so cap total load to
# avoid getting rate-limited / blocked under concurrency.
_SEARCH_MAX_CONCURRENCY = int(os.getenv("SEARCH_MAX_CONCURRENCY", "6"))
_search_sem: asyncio.Semaphore | None = None


def _search_semaphore() -> asyncio.Semaphore:
    global _search_sem
    if _search_sem is None:
        _search_sem = asyncio.Semaphore(_SEARCH_MAX_CONCURRENCY)
    return _search_sem

_TAG_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
_ANGLE_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_NL_RE = re.compile(r"\n{3,}")


def _html_to_text(html: str) -> str:
    html = _TAG_RE.sub(" ", html)
    text = _ANGLE_RE.sub(" ", html)
    text = (
        text.replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return text.strip()


def _normalize_url(url: str) -> str:
    """DuckDuckGo HTML wraps links as //duckduckgo.com/l/?uddg=<encoded>. Unwrap them."""
    if not url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [])
        if target:
            return unquote(target[0])
    return url


async def fetch_page(url: str) -> str:
    """Fetch a URL and return readable text (truncated). Empty string on error."""
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": _UA})
        ctype = resp.headers.get("content-type", "")
        if resp.status_code != 200 or "html" not in ctype and "text" not in ctype:
            return ""
        # HTML→text is CPU-bound regex work; run it off the event loop so it
        # doesn't stall other concurrent runs' coroutines (progress/polling).
        text = await asyncio.to_thread(_html_to_text, resp.text)
        return text[:MAX_PAGE_CHARS]
    except Exception:
        return ""


async def search_and_read(query: str, *, max_results: int = 5, read_top: int = 3) -> dict[str, Any]:
    """Run a web search, then fetch the top results' content concurrently.

    Returns ``{"query", "results": [{title, url, content}], "sources": [{title, url}]}``.
    Gated by a global semaphore so concurrent runs don't overload the shared proxy.
    """
    async with _search_semaphore():
        return await _search_and_read(query, max_results=max_results, read_top=read_top)


async def _search_and_read(query: str, *, max_results: int, read_top: int) -> dict[str, Any]:
    hits = (await search_web(query, max_results=max_results)).get("results", [])
    for h in hits:
        h["url"] = _normalize_url(h.get("url", ""))
    top = hits[:read_top]
    pages = await asyncio.gather(*[fetch_page(h["url"]) for h in top], return_exceptions=True)

    results: list[dict[str, str]] = []
    for h, page in zip(top, pages):
        content = page if isinstance(page, str) else ""
        results.append({"title": h.get("title", ""), "url": h.get("url", ""), "content": content})
    # remaining hits (snippet-only) still count as sources
    sources = [{"title": h.get("title", ""), "url": h.get("url", "")} for h in hits]
    return {"query": query, "results": results, "sources": sources}
