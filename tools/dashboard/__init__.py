"""Dashboard / overview tools."""
from __future__ import annotations

from tools._client import request


async def dashboard_stats() -> dict:
    """Return aggregate counts: total sources, signals, entities, relations."""
    return await request("GET", "/dashboard/stats")


async def search_knowledge(q: str) -> dict:
    """Keyword search across entities, signals and sources.

    Args:
        q: free-text query matched on names / titles / abstracts.
    Returns ``{entities: [...], signals: [...], sources: [...]}``.
    """
    return await request("GET", "/search", params={"q": q})


__all__ = ["dashboard_stats", "search_knowledge"]
