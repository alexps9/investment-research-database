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


async def add_signal_analysis(
    signal_id: str,
    *,
    tldr: Optional[str] = None,
    summary: Optional[str] = None,
    why_it_matters: Optional[str] = None,
    technical_points: Optional[list[str]] = None,
    limitations: Optional[str] = None,
    topic_tags: Optional[list[str]] = None,
    entities: Optional[list[str]] = None,
    importance_score: float = 0.0,
    novelty_score: float = 0.0,
    relevance_score: float = 0.0,
    confidence_score: float = 0.0,
    reading_priority: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_version: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Persist structured analysis for a signal (POST /signals/{id}/analysis)."""
    body = clean({
        "tldr": tldr,
        "summary": summary,
        "why_it_matters": why_it_matters,
        "technical_points": technical_points or [],
        "limitations": limitations,
        "topic_tags": topic_tags or [],
        "entities": entities or [],
        "importance_score": importance_score,
        "novelty_score": novelty_score,
        "relevance_score": relevance_score,
        "confidence_score": confidence_score,
        "reading_priority": reading_priority,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "metadata": metadata or {},
    })
    return await request("POST", f"/signals/{signal_id}/analysis", json=body)


async def link_signal_entity(
    signal_id: str,
    entity_id: str,
    role: str,
    mention_text: Optional[str] = None,
    confidence: float = 1.0,
    extracted_by: str = "agent",
) -> dict:
    """Link a signal to a knowledge-graph entity (POST /signals/{id}/entities)."""
    body = clean({
        "entity_id": entity_id,
        "role": role,
        "mention_text": mention_text,
        "confidence": confidence,
        "extracted_by": extracted_by,
    })
    return await request("POST", f"/signals/{signal_id}/entities", json=body)


async def set_signal_status(signal_id: str, status: str) -> dict:
    """Update only the signal status (collected | processed | duplicated | ignored | archived)."""
    return await update_signal(signal_id, {"status": status})


__all__ = [
    "list_signals",
    "get_signal",
    "create_signal",
    "update_signal",
    "delete_signal",
    "add_signal_analysis",
    "link_signal_entity",
    "set_signal_status",
]
