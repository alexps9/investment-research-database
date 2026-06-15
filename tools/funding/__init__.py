"""Investment / financing (funding) tools."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import clean, request


async def list_funding(
    sector: Optional[str] = None,
    round: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
) -> Any:
    """List investment/financing events. Filter by sector, round, or company (q)."""
    return await request("GET", "/funding", params=clean({
        "sector": sector, "round": round, "q": q, "limit": limit,
    }))


async def get_funding(funding_id: str) -> dict:
    """Get one funding event by id."""
    return await request("GET", f"/funding/{funding_id}")


async def funding_trends() -> dict:
    """Aggregated funding analytics: totals + breakdowns by month, round, sector."""
    return await request("GET", "/funding/trends")


async def create_funding(
    company_name: str,
    round: Optional[str] = None,
    amount_usd: Optional[float] = None,
    sector: Optional[str] = None,
    investors: Optional[list[str]] = None,
    announced_at: Optional[str] = None,
    source_url: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Create an investment/financing event. ``amount_usd`` is in USD millions."""
    body = clean({
        "company_name": company_name, "round": round, "amount_usd": amount_usd,
        "sector": sector, "investors": investors or [], "announced_at": announced_at,
        "source_url": source_url, "description": description, "extracted_by": "agent",
    })
    return await request("POST", "/funding", json=body)


async def update_funding(funding_id: str, fields: dict) -> dict:
    """Patch a funding event by id."""
    return await request("PATCH", f"/funding/{funding_id}", json=clean(fields))


async def delete_funding(funding_id: str) -> dict:
    """Delete a funding event by id."""
    return await request("DELETE", f"/funding/{funding_id}")


__all__ = [
    "list_funding", "get_funding", "funding_trends",
    "create_funding", "update_funding", "delete_funding",
]
