"""Atomic tools for the HH-Research knowledge base.

Each function is a thin async wrapper over one backend REST endpoint. They are
written to be used directly as agent tools (AutoGen / MCP / custom): clear type
hints + docstrings so the model can build accurate tool schemas, and they always
return JSON-serialisable Python values (never raise on HTTP errors — a structured
``{"error": ...}`` dict is returned instead, so the agent can reason about it).

The backend (FastAPI) remains the single source of truth and the only component
touching PostgreSQL; these tools never connect to the database directly.

Configuration (env):
    KB_API_BASE_URL   backend base URL (default: http://localhost:8000)
    KB_API_TIMEOUT    per-request timeout in seconds (default: 30)
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

API_BASE_URL = os.getenv("KB_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = "/api"
TIMEOUT = float(os.getenv("KB_API_TIMEOUT", "30"))

VALID_RELATION_TYPES = [
    "WORKS_AT", "AFFILIATED_WITH", "PUBLISHED", "AUTHORED", "RELEASED",
    "PROPOSES", "USES", "EVALUATES_ON", "BUILT_ON", "MENTIONS", "ABOUT",
    "FOCUSES_ON", "RELATED_TO", "COMPETES_WITH", "IMPROVES", "INTRODUCES",
]


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    """Call the backend and return parsed JSON, or a structured error dict."""
    url = f"{API_BASE_URL}{API_PREFIX}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        return {"error": "backend_unreachable", "detail": str(exc), "url": url}

    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {"error": f"http_{resp.status_code}", "detail": detail, "url": url}

    if resp.status_code == 204 or not resp.content:
        return {"ok": True}
    return resp.json()


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop None values so we don't send empty query params / body fields."""
    return {k: v for k, v in params.items() if v is not None}


# ── Read / overview ───────────────────────────────────────────────────────────

async def dashboard_stats() -> dict:
    """Return aggregate counts: total sources, signals, entities, relations."""
    return await _request("GET", "/dashboard/stats")


async def search_knowledge(q: str) -> dict:
    """Keyword search across entities, signals and sources.

    Args:
        q: free-text query matched on names / titles / abstracts.
    Returns ``{entities: [...], signals: [...], sources: [...]}``.
    """
    return await _request("GET", "/search", params={"q": q})


# ── Sources (CRUD) ──────────────────────────────────────────────────────────--

async def list_sources(skip: int = 0, limit: int = 100) -> Any:
    """List intelligence sources (people, orgs, feeds, repos, accounts)."""
    return await _request("GET", "/sources", params=_clean({"skip": skip, "limit": limit}))


async def get_source(source_id: str) -> dict:
    """Get one source by id (with organisation, accounts, tags)."""
    return await _request("GET", f"/sources/{source_id}")


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
    body = _clean({
        "name": name, "source_type": source_type, "organization_id": organization_id,
        "tier": tier, "sector": sector, "description": description,
        "activity_status": activity_status,
    })
    return await _request("POST", "/sources", json=body)


async def update_source(source_id: str, fields: dict) -> dict:
    """Patch a source by id. ``fields`` is a dict of the columns to change."""
    return await _request("PATCH", f"/sources/{source_id}", json=_clean(fields))


async def delete_source(source_id: str) -> dict:
    """Delete a source by id."""
    return await _request("DELETE", f"/sources/{source_id}")


# ── Signals (CRUD) ────────────────────────────────────────────────────────────

async def list_signals(
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List signals (papers, tweets, blogs, model releases, ...) with filters.

    Args:
        signal_type: paper | tweet | blog | news | tech_report | github_release |
                     model_release | benchmark | dataset | other.
        status: collected | processed | duplicated | ignored | archived.
        q: free-text match on title / abstract.
    """
    params = _clean({
        "signal_type": signal_type, "status": status, "q": q,
        "skip": skip, "limit": limit,
    })
    return await _request("GET", "/signals", params=params)


async def get_signal(signal_id: str) -> dict:
    """Get one signal by id (with analysis and entity mentions)."""
    return await _request("GET", f"/signals/{signal_id}")


async def create_signal(
    title: str,
    url: str,
    signal_type: str = "other",
    abstract: Optional[str] = None,
    published_at: Optional[str] = None,
    status: str = "collected",
) -> dict:
    """Create a signal. ``url`` must be unique; ``published_at`` is ISO-8601."""
    body = _clean({
        "title": title, "url": url, "signal_type": signal_type,
        "abstract": abstract, "published_at": published_at, "status": status,
    })
    return await _request("POST", "/signals", json=body)


async def update_signal(signal_id: str, fields: dict) -> dict:
    """Patch a signal by id. ``fields`` is a dict of the columns to change."""
    return await _request("PATCH", f"/signals/{signal_id}", json=_clean(fields))


async def delete_signal(signal_id: str) -> dict:
    """Delete a signal by id."""
    return await _request("DELETE", f"/signals/{signal_id}")


# ── Entities & graph ────────────────────────────────────────────────────────--

async def list_entities(
    entity_type: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List knowledge-graph entities.

    Args:
        entity_type: person | organization | paper | model | method | dataset |
                     benchmark | topic | project | system | event.
    """
    params = _clean({"entity_type": entity_type, "q": q, "skip": skip, "limit": limit})
    return await _request("GET", "/entities", params=params)


async def get_entity(entity_id: str) -> dict:
    """Get one entity by id (with aliases)."""
    return await _request("GET", f"/entities/{entity_id}")


async def get_entity_wiki(entity_id: str) -> dict:
    """Get the full Wiki profile of an entity (aliases, relations, signals)."""
    return await _request("GET", f"/wiki/entities/{entity_id}")


async def add_entity_relation(
    subject_entity_id: str,
    relation_type: str,
    object_entity_id: str,
    source_signal_id: Optional[str] = None,
    confidence: float = 1.0,
) -> dict:
    """Create a directed relation between two entities.

    ``relation_type`` MUST be one of ``VALID_RELATION_TYPES``.
    """
    if relation_type not in VALID_RELATION_TYPES:
        return {"error": "invalid_relation_type", "valid": VALID_RELATION_TYPES}
    body = _clean({
        "subject_entity_id": subject_entity_id, "relation_type": relation_type,
        "object_entity_id": object_entity_id, "source_signal_id": source_signal_id,
        "confidence": confidence, "extracted_by": "agent",
    })
    return await _request("POST", f"/entities/{subject_entity_id}/relations", json=body)


# ── Semantic search & RAG ───────────────────────────────────────────────────--

async def ai_status() -> dict:
    """Report whether embeddings (vector search) and chat (RAG) are configured."""
    return await _request("GET", "/ai/status")


async def semantic_search(q: str, types: Optional[str] = None, limit: int = 10) -> Any:
    """Vector (embedding) similarity search across the knowledge base.

    Args:
        q: natural-language query.
        types: comma-separated subset of entity,source,signal (default all).
    Returns ranked ``{object_type, object_id, name, description, score}`` hits.
    """
    return await _request("GET", "/ai/search", params=_clean({"q": q, "types": types, "limit": limit}))


async def ask(question: str, top_k: int = 8) -> dict:
    """RAG question answering grounded in the knowledge base. Returns {answer, sources}."""
    return await _request("POST", "/ai/ask", json={"question": question, "top_k": top_k})


async def reindex_embeddings(object_types: Optional[list[str]] = None) -> dict:
    """(Re)build the vector index for semantic_search / ask."""
    return await _request("POST", "/ai/reindex", json=_clean({"object_types": object_types}))


# ── Funding (investment / financing) ──────────────────────────────────────────

async def list_funding(
    sector: Optional[str] = None,
    round: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
) -> Any:
    """List investment/financing events. Filter by sector, round, or company (q)."""
    return await _request("GET", "/funding", params=_clean({
        "sector": sector, "round": round, "q": q, "limit": limit,
    }))


async def get_funding(funding_id: str) -> dict:
    """Get one funding event by id."""
    return await _request("GET", f"/funding/{funding_id}")


async def funding_trends() -> dict:
    """Aggregated funding analytics: totals + breakdowns by month, round, sector."""
    return await _request("GET", "/funding/trends")


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
    body = _clean({
        "company_name": company_name, "round": round, "amount_usd": amount_usd,
        "sector": sector, "investors": investors or [], "announced_at": announced_at,
        "source_url": source_url, "description": description, "extracted_by": "agent",
    })
    return await _request("POST", "/funding", json=body)


async def update_funding(funding_id: str, fields: dict) -> dict:
    """Patch a funding event by id."""
    return await _request("PATCH", f"/funding/{funding_id}", json=_clean(fields))


async def delete_funding(funding_id: str) -> dict:
    """Delete a funding event by id."""
    return await _request("DELETE", f"/funding/{funding_id}")


# ── Daily Boost ───────────────────────────────────────────────────────────────

async def get_daily_digest(date: Optional[str] = None) -> dict:
    """Get the Daily Boost digest for a date (YYYY-MM-DD), or the latest if omitted."""
    if date:
        return await _request("GET", f"/daily/{date}")
    return await _request("GET", "/daily/latest")


async def list_daily_digests(limit: int = 30) -> Any:
    """List recent Daily Boost digests (most recent first)."""
    return await _request("GET", "/daily", params={"limit": limit})


async def generate_daily_digest(
    date: Optional[str] = None,
    window_days: int = 1,
    limit: int = 8,
) -> dict:
    """Generate (or regenerate) the Daily Boost digest for a date (default today, UTC)."""
    params = _clean({"digest_date": date, "window_days": window_days, "limit": limit})
    return await _request("POST", "/daily/generate", params=params)
