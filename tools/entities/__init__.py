"""Entity & knowledge-graph tools."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import VALID_RELATION_TYPES, clean, request


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
    params = clean({"entity_type": entity_type, "q": q, "skip": skip, "limit": limit})
    return await request("GET", "/entities", params=params)


async def get_entity(entity_id: str) -> dict:
    """Get one entity by id (with aliases)."""
    return await request("GET", f"/entities/{entity_id}")


async def get_entity_wiki(entity_id: str) -> dict:
    """Get the full Wiki profile of an entity (aliases, relations, signals)."""
    return await request("GET", f"/wiki/entities/{entity_id}")


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
    body = clean({
        "subject_entity_id": subject_entity_id, "relation_type": relation_type,
        "object_entity_id": object_entity_id, "source_signal_id": source_signal_id,
        "confidence": confidence, "extracted_by": "agent",
    })
    return await request("POST", f"/entities/{subject_entity_id}/relations", json=body)


async def create_entity(
    name: str,
    entity_type: str,
    canonical_name: Optional[str] = None,
    description: Optional[str] = None,
    homepage_url: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a knowledge-graph entity (POST /api/entities)."""
    body = clean({
        "name": name,
        "canonical_name": canonical_name or name,
        "entity_type": entity_type,
        "description": description,
        "homepage_url": homepage_url,
        "metadata": metadata or {},
    })
    return await request("POST", "/entities", json=body)


async def add_entity_alias(
    entity_id: str,
    alias: str,
    alias_type: str = "other",
) -> dict:
    """Add an alias to an entity."""
    body = clean({"alias": alias, "alias_type": alias_type})
    return await request("POST", f"/entities/{entity_id}/aliases", json=body)


async def get_graph_relations(limit: int = 500) -> Any:
    """Return all graph edges for visualisation / inspection."""
    return await request("GET", "/graph/relations", params={"limit": limit})


async def find_entity_by_name(
    name: str,
    entity_type: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """Search entities by name and return the best match (if any).

    Returns ``{"match": entity_dict | None, "candidates": [...]}``.
    """
    results = await list_entities(entity_type=entity_type, q=name, limit=limit)
    if isinstance(results, dict):
        candidates = results.get("items", results.get("results", []))
    elif isinstance(results, list):
        candidates = results
    else:
        candidates = []

    if not candidates:
        return {"match": None, "candidates": []}

    needle = name.strip().lower()
    for ent in candidates:
        if ent.get("name", "").strip().lower() == needle:
            return {"match": ent, "candidates": candidates}
        if ent.get("canonical_name", "").strip().lower() == needle:
            return {"match": ent, "candidates": candidates}
        for alias in ent.get("aliases", []):
            alias_text = alias.get("alias", "") if isinstance(alias, dict) else str(alias)
            if alias_text.strip().lower() == needle:
                return {"match": ent, "candidates": candidates}

    return {"match": candidates[0] if len(candidates) == 1 else None, "candidates": candidates}


__all__ = [
    "list_entities",
    "get_entity",
    "get_entity_wiki",
    "add_entity_relation",
    "create_entity",
    "add_entity_alias",
    "get_graph_relations",
    "find_entity_by_name",
]
