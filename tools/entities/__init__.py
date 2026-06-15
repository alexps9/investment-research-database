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


__all__ = ["list_entities", "get_entity", "get_entity_wiki", "add_entity_relation"]
