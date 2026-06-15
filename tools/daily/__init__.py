"""Daily Boost (daily digest) tools."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import clean, request


async def get_daily_digest(date: Optional[str] = None) -> dict:
    """Get the Daily Boost digest for a date (YYYY-MM-DD), or the latest if omitted."""
    if date:
        return await request("GET", f"/daily/{date}")
    return await request("GET", "/daily/latest")


async def list_daily_digests(limit: int = 30) -> Any:
    """List recent Daily Boost digests (most recent first)."""
    return await request("GET", "/daily", params={"limit": limit})


async def generate_daily_digest(
    date: Optional[str] = None,
    window_days: int = 1,
    limit: int = 8,
) -> dict:
    """Generate (or regenerate) the Daily Boost digest for a date (default today, UTC)."""
    params = clean({"digest_date": date, "window_days": window_days, "limit": limit})
    return await request("POST", "/daily/generate", params=params)


__all__ = ["get_daily_digest", "list_daily_digests", "generate_daily_digest"]
