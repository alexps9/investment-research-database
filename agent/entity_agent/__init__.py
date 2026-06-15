"""Entity agent — extract entities/relations from analyzed signals into the KG."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from agent.llm import structured_llm
from tools._client import VALID_RELATION_TYPES
from tools.entities import (
    add_entity_relation,
    create_entity,
    find_entity_by_name,
)
from tools.signals import link_signal_entity
from tools.search import reindex_embeddings
from tools.signals import get_signal, list_signals


class ExtractedEntity(BaseModel):
    name: str
    entity_type: str = Field(description="person|organization|paper|model|method|dataset|benchmark|topic|project|system|event")
    role: str = Field(description="subject|object|author|company|product|mentioned")
    mention_text: Optional[str] = None


class ExtractedRelation(BaseModel):
    subject_name: str
    relation_type: str
    object_name: str
    confidence: float = Field(default=0.8, description="0-1 confidence")


class EntityExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)


ENTITY_PROMPT = """\
你是 HH-Research 的**知识构建 Agent**。从已分析的信号中抽取实体与关系，用于知识图谱。

合法关系类型（relation_type 必须从中选择）：
{valid_types}

信号标题：{title}
分析摘要：{summary}
TLDR：{tldr}
已知实体名（来自分析）：{entity_names}

输出：
- entities：文中出现的实体（name, entity_type, role, mention_text）
- relations：实体间有向关系（subject_name, relation_type, object_name, confidence）
"""


async def _resolve_or_create_entity(name: str, entity_type: str) -> dict | None:
    lookup = await find_entity_by_name(name, entity_type=entity_type)
    if lookup.get("match"):
        return lookup["match"]
    created = await create_entity(name=name, entity_type=entity_type)
    if isinstance(created, dict) and created.get("error"):
        # Retry without type filter
        lookup2 = await find_entity_by_name(name)
        if lookup2.get("match"):
            return lookup2["match"]
        return None
    return created


async def process_signal_entities(signal_id: str) -> dict:
    """Extract and persist entities/relations for one signal."""
    signal = await get_signal(signal_id)
    if isinstance(signal, dict) and signal.get("error"):
        return {"error": signal, "signal_id": signal_id}

    analysis = signal.get("analysis") or {}
    llm = structured_llm(EntityExtractionResult, temperature=0.0)
    prompt = ENTITY_PROMPT.format(
        valid_types=", ".join(sorted(VALID_RELATION_TYPES)),
        title=signal.get("title", ""),
        summary=analysis.get("summary", signal.get("abstract", "")),
        tldr=analysis.get("tldr", ""),
        entity_names=", ".join(analysis.get("entities") or []),
    )
    try:
        extracted: EntityExtractionResult = await llm.ainvoke(prompt)
    except Exception as exc:
        return {"error": f"llm_failed: {exc}", "signal_id": signal_id}

    name_to_id: dict[str, str] = {}
    created_entities: list[dict] = []
    created_relations: list[dict] = []

    for ent in extracted.entities:
        entity = await _resolve_or_create_entity(ent.name, ent.entity_type)
        if not entity or not entity.get("id"):
            continue
        name_to_id[ent.name.lower()] = entity["id"]
        created_entities.append(entity)
        await link_signal_entity(
            signal_id,
            entity["id"],
            role=ent.role,
            mention_text=ent.mention_text or ent.name,
        )

    for rel in extracted.relations:
        if rel.relation_type not in VALID_RELATION_TYPES:
            continue
        subj_id = name_to_id.get(rel.subject_name.lower())
        obj_id = name_to_id.get(rel.object_name.lower())
        if not subj_id:
            subj = await _resolve_or_create_entity(rel.subject_name, "organization")
            subj_id = subj.get("id") if subj else None
        if not obj_id:
            obj = await _resolve_or_create_entity(rel.object_name, "organization")
            obj_id = obj.get("id") if obj else None
        if not subj_id or not obj_id:
            continue
        name_to_id[rel.subject_name.lower()] = subj_id
        name_to_id[rel.object_name.lower()] = obj_id
        rel_result = await add_entity_relation(
            subj_id,
            rel.relation_type,
            obj_id,
            source_signal_id=signal_id,
            confidence=rel.confidence,
        )
        if isinstance(rel_result, dict) and not rel_result.get("error"):
            created_relations.append(rel_result)

    return {
        "signal_id": signal_id,
        "entities": created_entities,
        "relations": created_relations,
    }


async def run_entity_extraction(*, limit: int = 20, reindex: bool = True) -> dict:
    """Process recently analyzed signals into the knowledge graph."""
    raw = await list_signals(status="processed", limit=limit)
    if isinstance(raw, dict):
        signals = raw.get("items", [])
    else:
        signals = raw or []

    all_entities: list[dict] = []
    all_relations: list[dict] = []
    errors: list[str] = []

    for sig in signals:
        if not sig.get("analysis") and not sig.get("id"):
            continue
        sid = sig["id"]
        outcome = await process_signal_entities(sid)
        if outcome.get("error"):
            errors.append(str(outcome))
        else:
            all_entities.extend(outcome.get("entities", []))
            all_relations.extend(outcome.get("relations", []))

    if reindex and (all_entities or all_relations):
        await reindex_embeddings(object_types=["entity", "signal"])

    print(f"  Entity: {len(all_entities)} entities, {len(all_relations)} relations ({len(errors)} errors)")
    return {
        "entities": all_entities,
        "relations": all_relations,
        "errors": errors,
        "run_meta": {"entities_created": len(all_entities), "relations_created": len(all_relations)},
    }


async def entity_node(state: dict) -> dict:
    """LangGraph node wrapper."""
    run_meta = state.get("run_meta") or {}
    limit = run_meta.get("entity_limit", 20)

    # Use signal ids from analyses if available
    analyses = state.get("analyses") or []
    if analyses:
        all_entities: list[dict] = []
        all_relations: list[dict] = []
        errors: list[str] = []
        for item in analyses:
            sid = item.get("signal_id")
            if not sid:
                continue
            outcome = await process_signal_entities(sid)
            if outcome.get("error"):
                errors.append(str(outcome))
            else:
                all_entities.extend(outcome.get("entities", []))
                all_relations.extend(outcome.get("relations", []))
        if all_entities or all_relations:
            await reindex_embeddings(object_types=["entity", "signal"])
        return {
            "entities": all_entities,
            "relations": all_relations,
            "errors": errors,
            "run_meta": {"entities_created": len(all_entities)},
        }

    return await run_entity_extraction(limit=limit)
