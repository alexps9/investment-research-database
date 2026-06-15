"""Source CRUD tools (people, orgs, feeds, repos, social accounts)."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import clean, request


async def list_sources(skip: int = 0, limit: int = 100) -> Any:
    """List intelligence sources (people, orgs, feeds, repos, accounts)."""
    return await request("GET", "/sources", params=clean({"skip": skip, "limit": limit}))


async def get_source(source_id: str) -> dict:
    """Get one source by id (with organisation, accounts, tags)."""
    return await request("GET", f"/sources/{source_id}")


async def create_source(
    name: str,
    source_type: str = "person",
    organization_id: Optional[str] = None,
    tier: Optional[str] = None,
    sector: Optional[str] = None,
    description: Optional[str] = None,
    activity_status: str = "unknown",
) -> dict:
    """Create an intelligence source.

    Args:
        source_type: person | organization | rss | website | github_repo |
                     arxiv_category | newsletter | social_account.
        tier: priority label such as P0+ / P1 / P2 / P3.
    """
    body = clean({
        "name": name, "source_type": source_type, "organization_id": organization_id,
        "tier": tier, "sector": sector, "description": description,
        "activity_status": activity_status,
    })
    return await request("POST", "/sources", json=body)


async def update_source(source_id: str, fields: dict) -> dict:
    """Patch a source by id. ``fields`` is a dict of the columns to change."""
    return await request("PATCH", f"/sources/{source_id}", json=clean(fields))


async def delete_source(source_id: str) -> dict:
    """Delete a source by id."""
    return await request("DELETE", f"/sources/{source_id}")


__all__ = ["list_sources", "get_source", "create_source", "update_source", "delete_source"]
