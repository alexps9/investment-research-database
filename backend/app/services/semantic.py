"""Semantic indexing & search over entities / sources / signals using pgvector."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Embedding, Entity, Source, Signal
from app.services import llm

settings = get_settings()

EMBED_BATCH = 64
SUPPORTED_TYPES = ("entity", "source", "signal")


# ── text builders ───────────────────────────────────────────────────────────────

def _entity_text(e: Entity) -> str:
    parts = [e.name]
    if e.canonical_name and e.canonical_name != e.name:
        parts.append(e.canonical_name)
    if e.entity_type:
        parts.append(f"type: {e.entity_type}")
    if e.introduction:
        parts.append(e.introduction)
    meta = e.metadata_ or {}
    for key in ("research_focus", "sector", "tier"):
        if meta.get(key):
            parts.append(f"{key}: {meta[key]}")
    return " | ".join(str(p) for p in parts if p)


def _source_text(s: Source) -> str:
    parts = [s.name, f"type: {s.source_type}"]
    for val in (s.sector, s.tier, s.role_title, s.description, s.tier_reason):
        if val:
            parts.append(str(val))
    return " | ".join(parts)


def _signal_text(sig: Signal) -> str:
    parts = [sig.title]
    if sig.abstract:
        parts.append(sig.abstract)
    if sig.analysis and sig.analysis.tldr:
        parts.append(sig.analysis.tldr)
    return " | ".join(parts)


# ── reindex ───────────────────────────────────────────────────────────────────

async def _upsert_embeddings(db: AsyncSession, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = pg_insert(Embedding).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["object_type", "object_id", "embedding_type", "model_name"],
        set_={"vector": stmt.excluded.vector},
    )
    await db.execute(stmt)
    await db.commit()


async def reindex(db: AsyncSession, object_types: Optional[list[str]] = None) -> dict:
    """(Re)generate embeddings for the given object types. Returns per-type counts."""
    if not llm.embeddings_enabled():
        raise llm.LLMNotConfigured("EMBEDDING_API_KEY is not set; cannot build embeddings.")

    types = object_types or list(SUPPORTED_TYPES)
    counts: dict[str, int] = {}
    model = settings.embedding_model

    for otype in types:
        if otype == "entity":
            items = (await db.execute(select(Entity))).scalars().all()
            text_fn, embed_type = _entity_text, "entity_description"
        elif otype == "source":
            items = (await db.execute(select(Source))).scalars().all()
            text_fn, embed_type = _source_text, "summary"
        elif otype == "signal":
            from sqlalchemy.orm import selectinload
            items = (await db.execute(select(Signal).options(selectinload(Signal.analysis)))).scalars().all()
            text_fn, embed_type = _signal_text, "abstract"
        else:
            continue

        total = 0
        for start in range(0, len(items), EMBED_BATCH):
            batch = items[start:start + EMBED_BATCH]
            texts = [text_fn(it) for it in batch]
            vectors = await llm.embed_texts(texts)
            rows = [
                {
                    "id": str(uuid.uuid4()),  # multi-row core insert skips Python defaults
                    "object_type": otype,
                    "object_id": it.id,
                    "embedding_type": embed_type,
                    "model_name": model,
                    "vector": vec,
                }
                for it, vec in zip(batch, vectors)
            ]
            await _upsert_embeddings(db, rows)
            total += len(rows)
        counts[otype] = total

    return counts


# ── search ──────────────────────────────────────────────────────────────────────

async def semantic_search(
    db: AsyncSession,
    query: str,
    object_types: Optional[list[str]] = None,
    limit: int = 10,
) -> list[dict]:
    """Embed the query and return nearest objects by cosine distance."""
    if not llm.embeddings_enabled():
        raise llm.LLMNotConfigured("EMBEDDING_API_KEY is not set; semantic search disabled.")

    qvec = await llm.embed_text(query)
    types = object_types or list(SUPPORTED_TYPES)

    distance = Embedding.vector.cosine_distance(qvec).label("distance")
    stmt = (
        select(Embedding.object_type, Embedding.object_id, distance)
        .where(Embedding.object_type.in_(types))
        .where(Embedding.vector.isnot(None))
        .order_by(distance)
        .limit(limit)
    )
    hits = (await db.execute(stmt)).all()

    # group ids by type, then hydrate
    by_type: dict[str, list[str]] = {}
    for otype, oid, _dist in hits:
        by_type.setdefault(otype, []).append(oid)

    hydrated: dict[tuple[str, str], object] = {}
    if by_type.get("entity"):
        rows = (await db.execute(select(Entity).where(Entity.id.in_(by_type["entity"])))).scalars().all()
        for r in rows:
            hydrated[("entity", r.id)] = r
    if by_type.get("source"):
        rows = (await db.execute(select(Source).where(Source.id.in_(by_type["source"])))).scalars().all()
        for r in rows:
            hydrated[("source", r.id)] = r
    if by_type.get("signal"):
        rows = (await db.execute(select(Signal).where(Signal.id.in_(by_type["signal"])))).scalars().all()
        for r in rows:
            hydrated[("signal", r.id)] = r

    results = []
    for otype, oid, dist in hits:
        obj = hydrated.get((otype, oid))
        if obj is None:
            continue
        name = getattr(obj, "name", None) or getattr(obj, "title", "")
        desc = getattr(obj, "introduction", None) or getattr(obj, "description", None) or getattr(obj, "abstract", None)
        results.append({
            "object_type": otype,
            "object_id": oid,
            "name": name,
            "description": desc,
            "score": round(1.0 - float(dist), 4),   # cosine similarity
        })
    return results
