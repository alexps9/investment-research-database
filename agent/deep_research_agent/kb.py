"""Knowledge-base retrieval for the deep-research agent.

Deep research is *database-first*: before (and instead of) hitting the open web,
each sub-topic is grounded in the project's own knowledge base via the backend's
semantic search (`GET /api/ai/search`). Entity hits carry a wiki link
(`/wiki/entities/{id}`) so the final report can cite internal sources that jump
straight to their wiki entry.

Everything degrades gracefully: if embeddings aren't configured or the backend
is unreachable, calls return an empty list and the pipeline falls back to web
search — so a missing KB never sinks a run.
"""
from __future__ import annotations

import os

import httpx

KB_BASE = os.getenv("KB_API_BASE_URL", "http://backend:8000").rstrip("/")
KB_PREFIX = "/api"
KB_TIMEOUT = float(os.getenv("KB_API_TIMEOUT", "20"))


def wiki_url(object_type: str, object_id: str) -> str | None:
    """Relative wiki link for a KB hit, when one exists (entities have pages)."""
    if object_type == "entity" and object_id:
        return f"/wiki/entities/{object_id}"
    return None


async def kb_search(query: str, *, types: str = "entity,signal,source", limit: int = 8) -> list[dict]:
    """Vector search over the knowledge base. Returns ranked hits, or [] on any
    failure (embeddings off / backend down / 4xx). Each hit:
    ``{object_type, object_id, name, description, score, wiki_url}``."""
    if not query or not query.strip():
        return []
    url = f"{KB_BASE}{KB_PREFIX}/ai/search"
    try:
        async with httpx.AsyncClient(timeout=KB_TIMEOUT, trust_env=False) as client:
            resp = await client.get(url, params={"q": query.strip(), "types": types, "limit": limit})
    except Exception:
        return []
    if resp.status_code >= 400:
        return []
    try:
        hits = resp.json()
    except Exception:
        return []
    out: list[dict] = []
    for h in hits if isinstance(hits, list) else []:
        out.append({
            "object_type": h.get("object_type"),
            "object_id": h.get("object_id"),
            "name": h.get("name") or "",
            "description": h.get("description") or "",
            "score": h.get("score"),
            "wiki_url": wiki_url(h.get("object_type", ""), h.get("object_id", "")),
        })
    return out
