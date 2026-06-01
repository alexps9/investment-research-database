"""
MCP server for the AI Intelligence Knowledge Base.

Exposes the knowledge base (sources, signals, entities, relations, wiki, search)
as MCP tools and resources so other agents can query and contribute to it.

Data access strategy: this server is a thin MCP wrapper that calls the existing
FastAPI backend over HTTP. PostgreSQL remains the single source of truth and the
backend stays the only component touching the database.

Transports:
- stdio (default)        — for local clients like Claude Desktop / Cursor
- streamable-http        — for remote / multi-agent access

Configuration via environment variables:
- KB_API_BASE_URL   backend base URL          (default: http://localhost:8000)
- MCP_TRANSPORT     stdio | streamable-http    (default: stdio)
- MCP_HOST          host for http transport    (default: 0.0.0.0)
- MCP_PORT          port for http transport    (default: 8765)
"""
import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.getenv("KB_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = "/api"

# Mirror of backend app.models.VALID_RELATION_TYPES — kept here so agents can
# discover valid values without a round-trip.
VALID_RELATION_TYPES = [
    "WORKS_AT", "AFFILIATED_WITH", "PUBLISHED", "AUTHORED", "RELEASED",
    "PROPOSES", "USES", "EVALUATES_ON", "BUILT_ON", "MENTIONS", "ABOUT",
    "FOCUSES_ON", "RELATED_TO", "COMPETES_WITH", "IMPROVES", "INTRODUCES",
]

mcp = FastMCP("ai-knowledge-base", json_response=True)


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    """Call the backend and return parsed JSON, or a structured error dict."""
    url = f"{API_BASE_URL}{API_PREFIX}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        return {"error": "backend_unreachable", "detail": str(exc), "url": url}

    if resp.status_code >= 400:
        detail: Any
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


# ── Read tools ────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_knowledge(q: str) -> dict:
    """Global search across entities, signals, and sources.

    Args:
        q: Free-text query (matched against names, titles, abstracts).
    Returns grouped results: {entities: [...], signals: [...], sources: [...]}.
    """
    return await _request("GET", "/search", params={"q": q})


@mcp.tool()
async def get_dashboard_stats() -> dict:
    """Return aggregate counts: total sources, signals, entities, relations."""
    return await _request("GET", "/dashboard/stats")


@mcp.tool()
async def list_sources(skip: int = 0, limit: int = 100) -> Any:
    """List intelligence sources (people, orgs, feeds, repos, accounts)."""
    return await _request("GET", "/sources", params=_clean({"skip": skip, "limit": limit}))


@mcp.tool()
async def get_source(source_id: str) -> dict:
    """Get one source by id, including its accounts and tags."""
    return await _request("GET", f"/sources/{source_id}")


@mcp.tool()
async def list_signals(
    signal_type: Optional[str] = None,
    source_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    published_from: Optional[str] = None,
    published_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List signals (papers, tweets, blogs, model releases, etc.) with filters.

    Args:
        signal_type: paper | tweet | blog | news | tech_report | github_release |
                     model_release | benchmark | dataset | other
        source_id / organization_id: filter by owning source or org
        status: collected | processed | duplicated | ignored | archived
        q: free-text match on title/abstract
        published_from / published_to: ISO-8601 date bounds
    """
    params = _clean({
        "signal_type": signal_type, "source_id": source_id,
        "organization_id": organization_id, "status": status, "q": q,
        "published_from": published_from, "published_to": published_to,
        "skip": skip, "limit": limit,
    })
    return await _request("GET", "/signals", params=params)


@mcp.tool()
async def get_signal(signal_id: str) -> dict:
    """Get one signal by id, including its analysis and entity mentions."""
    return await _request("GET", f"/signals/{signal_id}")


@mcp.tool()
async def get_related_signals(signal_id: str) -> Any:
    """Return signals related to the given one (sharing linked entities)."""
    return await _request("GET", f"/signals/{signal_id}/related")


@mcp.tool()
async def list_entities(
    entity_type: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List canonical knowledge entities with optional filters.

    Args:
        entity_type: person | organization | paper | model | method | dataset |
                     benchmark | topic | project | system | event
        q: free-text match on name / canonical_name
    """
    params = _clean({"entity_type": entity_type, "q": q, "skip": skip, "limit": limit})
    return await _request("GET", "/entities", params=params)


@mcp.tool()
async def get_entity_wiki(entity_id: str) -> dict:
    """Get the full Wiki profile of an entity.

    Includes: entity fields, aliases, related signals, outgoing relations,
    incoming relations, and related entities. Best single call to understand
    everything the knowledge base knows about an entity.
    """
    return await _request("GET", f"/wiki/entities/{entity_id}")


@mcp.tool()
async def get_entity_relations(entity_id: str) -> Any:
    """Return all relations (incoming and outgoing) for an entity."""
    return await _request("GET", f"/entities/{entity_id}/relations")


@mcp.tool()
async def list_all_relations(limit: int = 500) -> Any:
    """Return the entity relation graph as a flat edge list (subject→type→object)."""
    return await _request("GET", "/graph/relations", params={"limit": limit})


@mcp.tool()
async def list_relation_types() -> list[str]:
    """Return the allowlist of valid relation_type values for add_entity_relation."""
    return VALID_RELATION_TYPES


@mcp.tool()
async def list_pipeline_runs(limit: int = 50) -> Any:
    """Return recent pipeline run logs (collect / analyze / extract / embed ...)."""
    return await _request("GET", "/runs", params={"limit": limit})


# ── Write tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def create_signal(
    title: str,
    url: str,
    signal_type: str = "other",
    source_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    abstract: Optional[str] = None,
    content: Optional[str] = None,
    published_at: Optional[str] = None,
    status: str = "collected",
) -> dict:
    """Create a new signal (evidence item) in the knowledge base.

    `url` must be unique. `signal_type` is one of: paper, tweet, blog, news,
    tech_report, github_release, model_release, benchmark, dataset, other.
    `published_at` is ISO-8601 (e.g. 2026-06-01T00:00:00Z).
    """
    body = _clean({
        "title": title, "url": url, "signal_type": signal_type,
        "source_id": source_id, "organization_id": organization_id,
        "abstract": abstract, "content": content,
        "published_at": published_at, "status": status,
    })
    return await _request("POST", "/signals", json=body)


@mcp.tool()
async def create_entity(
    name: str,
    canonical_name: str,
    entity_type: str,
    description: Optional[str] = None,
    homepage_url: Optional[str] = None,
) -> dict:
    """Create a canonical knowledge entity.

    `entity_type`: person | organization | paper | model | method | dataset |
    benchmark | topic | project | system | event.
    The pair (canonical_name, entity_type) must be unique.
    """
    body = _clean({
        "name": name, "canonical_name": canonical_name, "entity_type": entity_type,
        "description": description, "homepage_url": homepage_url, "metadata": {},
    })
    return await _request("POST", "/entities", json=body)


@mcp.tool()
async def create_source(
    name: str,
    source_type: str = "person",
    organization_id: Optional[str] = None,
    affiliation_type: Optional[str] = None,
    role_title: Optional[str] = None,
    description: Optional[str] = None,
    activity_status: str = "unknown",
) -> dict:
    """Create an intelligence source.

    `source_type`: person | organization | rss | website | github_repo |
    arxiv_category | newsletter | social_account.
    """
    body = _clean({
        "name": name, "source_type": source_type, "organization_id": organization_id,
        "affiliation_type": affiliation_type, "role_title": role_title,
        "description": description, "activity_status": activity_status,
    })
    return await _request("POST", "/sources", json=body)


@mcp.tool()
async def add_entity_relation(
    subject_entity_id: str,
    relation_type: str,
    object_entity_id: str,
    source_signal_id: Optional[str] = None,
    confidence: float = 1.0,
    extracted_by: Optional[str] = None,
) -> dict:
    """Create a directed relation between two entities.

    `relation_type` MUST be one of list_relation_types() — arbitrary types are
    rejected with HTTP 422. Optionally cite the `source_signal_id` evidence.
    """
    if relation_type not in VALID_RELATION_TYPES:
        return {
            "error": "invalid_relation_type",
            "detail": f"'{relation_type}' is not allowed.",
            "valid_relation_types": VALID_RELATION_TYPES,
        }
    body = _clean({
        "subject_entity_id": subject_entity_id, "relation_type": relation_type,
        "object_entity_id": object_entity_id, "source_signal_id": source_signal_id,
        "confidence": confidence, "extracted_by": extracted_by,
    })
    return await _request("POST", f"/entities/{subject_entity_id}/relations", json=body)


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("kb://stats")
async def stats_resource() -> dict:
    """Knowledge base aggregate counts, addressable as a resource."""
    return await _request("GET", "/dashboard/stats")


@mcp.resource("kb://entities/{entity_id}")
async def entity_resource(entity_id: str) -> dict:
    """Full Wiki profile of an entity, addressable by URI."""
    return await _request("GET", f"/wiki/entities/{entity_id}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.host = os.getenv("MCP_HOST", "0.0.0.0")
        mcp.settings.port = int(os.getenv("MCP_PORT", "8765"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
