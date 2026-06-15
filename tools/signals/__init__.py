"""Signal CRUD tools (papers, tweets, blogs, model/GitHub releases, news)."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import clean, request


async def list_signals(
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List signals with filters.

    Args:
        signal_type: paper | tweet | blog | news | tech_report | github_release |
                     model_release | benchmark | dataset | other.
        status: collected | processed | duplicated | ignored | archived.
        q: free-text match on title / abstract.
    """
    params = clean({
        "signal_type": signal_type, "status": status, "q": q,
        "skip": skip, "limit": limit,
    })
    return await request("GET", "/signals", params=params)


async def get_signal(signal_id: str) -> dict:
    """Get one signal by id (with analysis and entity mentions)."""
    return await request("GET", f"/signals/{signal_id}")


async def create_signal(
    title: str,
    url: str,
    signal_type: str = "other",
    abstract: Optional[str] = None,
    published_at: Optional[str] = None,
    status: str = "collected",
) -> dict:
    """Create a signal. ``url`` must be unique; ``published_at`` is ISO-8601."""
    body = clean({
        "title": title, "url": url, "signal_type": signal_type,
        "abstract": abstract, "published_at": published_at, "status": status,
    })
    return await request("POST", "/signals", json=body)


async def update_signal(signal_id: str, fields: dict) -> dict:
    """Patch a signal by id. ``fields`` is a dict of the columns to change."""
    return await request("PATCH", f"/signals/{signal_id}", json=clean(fields))


async def delete_signal(signal_id: str) -> dict:
    """Delete a signal by id."""
    return await request("DELETE", f"/signals/{signal_id}")


__all__ = ["list_signals", "get_signal", "create_signal", "update_signal", "delete_signal"]
