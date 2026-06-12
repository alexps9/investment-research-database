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
from mcp.server.transport_security import TransportSecuritySettings

API_BASE_URL = os.getenv("KB_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = "/api"

# Mirror of backend app.models.VALID_RELATION_TYPES — kept here so agents can
# discover valid values without a round-trip.
VALID_RELATION_TYPES = [
    "WORKS_AT", "AFFILIATED_WITH", "PUBLISHED", "AUTHORED", "RELEASED",
    "PROPOSES", "USES", "EVALUATES_ON", "BUILT_ON", "MENTIONS", "ABOUT",
    "FOCUSES_ON", "RELATED_TO", "COMPETES_WITH", "IMPROVES", "INTRODUCES",
]

# When bound to 0.0.0.0 (containers / HF Spaces), the MCP SDK otherwise enables
# DNS-rebinding protection with an empty allow-list and rejects every request
# behind a proxy with HTTP 421. This server sits behind the platform gateway, so
# disable the host-header check to allow access from any agent.
mcp = FastMCP(
    "ai-knowledge-base",
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


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


# ── Update / delete tools (full CRUD) ─────────────────────────────────────────

@mcp.tool()
async def update_signal(
    signal_id: str,
    title: Optional[str] = None,
    signal_type: Optional[str] = None,
    abstract: Optional[str] = None,
    content: Optional[str] = None,
    published_at: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    """Patch an existing signal. Only the provided fields are changed."""
    body = _clean({
        "title": title, "signal_type": signal_type, "abstract": abstract,
        "content": content, "published_at": published_at, "status": status,
    })
    return await _request("PATCH", f"/signals/{signal_id}", json=body)


@mcp.tool()
async def delete_signal(signal_id: str) -> dict:
    """Delete a signal by id."""
    return await _request("DELETE", f"/signals/{signal_id}")


@mcp.tool()
async def update_source(
    source_id: str,
    name: Optional[str] = None,
    source_type: Optional[str] = None,
    tier: Optional[str] = None,
    sector: Optional[str] = None,
    description: Optional[str] = None,
    activity_status: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """Patch an existing source. Only the provided fields are changed."""
    body = _clean({
        "name": name, "source_type": source_type, "tier": tier, "sector": sector,
        "description": description, "activity_status": activity_status, "is_active": is_active,
    })
    return await _request("PATCH", f"/sources/{source_id}", json=body)


@mcp.tool()
async def delete_source(source_id: str) -> dict:
    """Delete a source by id."""
    return await _request("DELETE", f"/sources/{source_id}")


@mcp.tool()
async def update_entity(
    entity_id: str,
    name: Optional[str] = None,
    canonical_name: Optional[str] = None,
    entity_type: Optional[str] = None,
    description: Optional[str] = None,
    homepage_url: Optional[str] = None,
) -> dict:
    """Patch an existing entity. Only the provided fields are changed."""
    body = _clean({
        "name": name, "canonical_name": canonical_name, "entity_type": entity_type,
        "description": description, "homepage_url": homepage_url,
    })
    return await _request("PATCH", f"/entities/{entity_id}", json=body)


# ── Semantic / vector search + RAG ────────────────────────────────────────────

@mcp.tool()
async def ai_status() -> dict:
    """Report whether embeddings (vector search) and chat (RAG) are configured."""
    return await _request("GET", "/ai/status")


@mcp.tool()
async def semantic_search(q: str, types: Optional[str] = None, limit: int = 10) -> Any:
    """Vector (embedding) similarity search across the knowledge base.

    Unlike `search_knowledge` (keyword match), this finds semantically related
    entities/sources/signals even without shared words.

    Args:
        q: natural-language query.
        types: comma-separated subset of entity,source,signal (default: all).
        limit: max hits.
    Returns a ranked list of {object_type, object_id, name, description, score}.
    Requires EMBEDDING_API_KEY configured on the backend (build the index first
    with `reindex_embeddings`).
    """
    return await _request("GET", "/ai/search", params=_clean({"q": q, "types": types, "limit": limit}))


@mcp.tool()
async def ask(question: str, top_k: int = 8) -> dict:
    """RAG question answering grounded in the knowledge base.

    Retrieves the most relevant entries by vector similarity, then asks the chat
    LLM (DeepSeek) to answer using only that context. Returns {answer, sources}.
    Requires EMBEDDING_API_KEY and DEEPSEEK_API_KEY configured on the backend.
    """
    return await _request("POST", "/ai/ask", json={"question": question, "top_k": top_k})


@mcp.tool()
async def reindex_embeddings(object_types: Optional[list[str]] = None) -> dict:
    """(Re)build the vector index for semantic_search / ask.

    Args:
        object_types: subset of ["entity","source","signal"]; default all.
    Run once after data changes. Requires EMBEDDING_API_KEY on the backend.
    """
    return await _request("POST", "/ai/reindex", json=_clean({"object_types": object_types}))


# ── Funding (investment / financing) tools ────────────────────────────────────

@mcp.tool()
async def list_funding(
    sector: Optional[str] = None,
    round: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
) -> Any:
    """List investment / financing events. Filter by sector, round, or company (q)."""
    return await _request("GET", "/funding", params=_clean({
        "sector": sector, "round": round, "q": q, "limit": limit,
    }))


@mcp.tool()
async def get_funding(funding_id: str) -> dict:
    """Get one funding event by id."""
    return await _request("GET", f"/funding/{funding_id}")


@mcp.tool()
async def funding_trends() -> dict:
    """Aggregated funding analytics: totals plus breakdowns by month, round, sector."""
    return await _request("GET", "/funding/trends")


@mcp.tool()
async def create_funding(
    company_name: str,
    round: Optional[str] = None,
    amount_usd: Optional[float] = None,
    currency: Optional[str] = None,
    sector: Optional[str] = None,
    investors: Optional[list[str]] = None,
    announced_at: Optional[str] = None,
    source_url: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Create an investment/financing event.

    `amount_usd` is in USD millions. `announced_at` is ISO-8601.
    `investors` is a list of investor names.
    """
    body = _clean({
        "company_name": company_name, "round": round, "amount_usd": amount_usd,
        "currency": currency, "sector": sector, "investors": investors or [],
        "announced_at": announced_at, "source_url": source_url,
        "description": description, "extracted_by": "mcp",
    })
    return await _request("POST", "/funding", json=body)


@mcp.tool()
async def update_funding(
    funding_id: str,
    company_name: Optional[str] = None,
    round: Optional[str] = None,
    amount_usd: Optional[float] = None,
    currency: Optional[str] = None,
    sector: Optional[str] = None,
    investors: Optional[list[str]] = None,
    announced_at: Optional[str] = None,
    source_url: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Patch a funding event. Only the provided fields are changed."""
    body = _clean({
        "company_name": company_name, "round": round, "amount_usd": amount_usd,
        "currency": currency, "sector": sector, "investors": investors,
        "announced_at": announced_at, "source_url": source_url, "description": description,
    })
    return await _request("PATCH", f"/funding/{funding_id}", json=body)


@mcp.tool()
async def delete_funding(funding_id: str) -> dict:
    """Delete a funding event by id."""
    return await _request("DELETE", f"/funding/{funding_id}")


# ── Daily Boost (daily digest) tools ──────────────────────────────────────────

@mcp.tool()
async def get_daily_digest(date: Optional[str] = None) -> dict:
    """Get the Daily Boost digest for a date (YYYY-MM-DD), or the latest if omitted."""
    if date:
        return await _request("GET", f"/daily/{date}")
    return await _request("GET", "/daily/latest")


@mcp.tool()
async def list_daily_digests(limit: int = 30) -> Any:
    """List recent Daily Boost digests (most recent first)."""
    return await _request("GET", "/daily", params={"limit": limit})


@mcp.tool()
async def generate_daily_digest(
    date: Optional[str] = None,
    window_days: int = 1,
    limit: int = 8,
) -> dict:
    """Generate (or regenerate) the Daily Boost digest.

    Picks the most important signals in the window ending on `date` (default
    today, UTC) and writes an LLM summary. `window_days` widens the look-back.
    """
    params = _clean({"digest_date": date, "window_days": window_days, "limit": limit})
    return await _request("POST", "/daily/generate", params=params)


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("kb://stats")
async def stats_resource() -> dict:
    """Knowledge base aggregate counts, addressable as a resource."""
    return await _request("GET", "/dashboard/stats")


@mcp.resource("kb://entities/{entity_id}")
async def entity_resource(entity_id: str) -> dict:
    """Full Wiki profile of an entity, addressable by URI."""
    return await _request("GET", f"/wiki/entities/{entity_id}")


@mcp.resource("kb://daily/latest")
async def daily_latest_resource() -> dict:
    """Latest Daily Boost digest, addressable as a resource."""
    return await _request("GET", "/daily/latest")


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
