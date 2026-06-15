"""Semantic search & RAG tools (vector search + grounded Q&A)."""
from __future__ import annotations

from typing import Any, Optional

from tools._client import clean, request


async def ai_status() -> dict:
    """Report whether embeddings (vector search) and chat (RAG) are configured."""
    return await request("GET", "/ai/status")


async def semantic_search(q: str, types: Optional[str] = None, limit: int = 10) -> Any:
    """Vector (embedding) similarity search across the knowledge base.

    Args:
        q: natural-language query.
        types: comma-separated subset of entity,source,signal (default all).
    Returns ranked ``{object_type, object_id, name, description, score}`` hits.
    """
    return await request("GET", "/ai/search", params=clean({"q": q, "types": types, "limit": limit}))


async def ask(question: str, top_k: int = 8) -> dict:
    """RAG question answering grounded in the knowledge base. Returns {answer, sources}."""
    return await request("POST", "/ai/ask", json={"question": question, "top_k": top_k})


async def reindex_embeddings(object_types: Optional[list[str]] = None) -> dict:
    """(Re)build the vector index for semantic_search / ask."""
    return await request("POST", "/ai/reindex", json=clean({"object_types": object_types}))


__all__ = ["ai_status", "semantic_search", "ask", "reindex_embeddings"]
