"""Graph relations: query and sync."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Source, SourceExperience, Organization, OrgTag, Entity, EntityRelation, SourceTag, Tag
from app.repositories import EntityRepo
from app.schemas import EntityRelationOut, EntityRelationCreate

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/relations", response_model=list[EntityRelationOut])
async def get_all_relations(limit: int = 500, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    return await repo.get_all_relations(limit=limit)


@router.post("/sync")
async def sync_graph(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Derive entity-relations from the structured source/organization/tag data.

    What gets created / updated:
    - Person-source → WORKS_AT → current-org entity
    - Person-source → FOCUSES_ON → topic entity  (via source_tags)
    - Person-source → PRE_WORKED_AT → past-org entity  (via source_experiences)
    - Org-source → FOCUSES_ON → topic entity  (via org_tags)
    - Org with parent_org → SUBSIDIARY_OF → parent-org entity

    Entities are matched by name (case-insensitive, stripped). Missing entities
    are created automatically.  Pre-existing relations of the same type between
    the same pair are skipped (idempotent).
    """
    created = 0
    skipped = 0

    # Helper: get or create entity by name + type
    entity_cache: dict[str, Entity] = {}

    async def get_or_create_entity(name: str, etype: str) -> Entity:
        key = f"{etype}::{name.strip().lower()}"
        if key in entity_cache:
            return entity_cache[key]
        result = await db.execute(
            select(Entity).where(
                Entity.name.ilike(name.strip()),
                Entity.entity_type == etype,
            )
        )
        ent = result.scalar_one_or_none()
        if not ent:
            ent = Entity(name=name.strip(), entity_type=etype, canonical_name=name.strip())
            db.add(ent)
            await db.flush()
        entity_cache[key] = ent
        return ent

    # Helper: create relation if not exists
    async def ensure_relation(subj_id: str, obj_id: str, rel_type: str) -> bool:
        nonlocal created, skipped
        result = await db.execute(
            select(EntityRelation).where(
                EntityRelation.subject_entity_id == subj_id,
                EntityRelation.object_entity_id == obj_id,
                EntityRelation.relation_type == rel_type,
            )
        )
        if result.scalar_one_or_none():
            skipped += 1
            return False
        rel = EntityRelation(
            subject_entity_id=subj_id,
            object_entity_id=obj_id,
            relation_type=rel_type,
            confidence=0.9,
            source="sync",
        )
        db.add(rel)
        created += 1
        return True

    # ── 1. Load all person sources with related data ──────────────────────────
    person_result = await db.execute(
        select(Source)
        .where(Source.source_type == "person")
        .options(
            selectinload(Source.organization),
            selectinload(Source.source_tags).selectinload(SourceTag.tag),
            selectinload(Source.experiences).selectinload(SourceExperience.organization),
        )
    )
    persons = person_result.scalars().all()

    for src in persons:
        person_ent = await get_or_create_entity(src.name, "person")

        # WORKS_AT current org
        if src.organization:
            org_ent = await get_or_create_entity(src.organization.name, "organization")
            await ensure_relation(person_ent.id, org_ent.id, "WORKS_AT")

        # FOCUSES_ON topics
        for st in src.source_tags:
            if st.tag:
                topic_ent = await get_or_create_entity(st.tag.name, st.tag.tag_type)
                await ensure_relation(person_ent.id, topic_ent.id, "FOCUSES_ON")

        # PRE_WORKED_AT past experiences
        for exp in src.experiences:
            if exp.organization:
                org_ent = await get_or_create_entity(exp.organization.name, "organization")
                rel_type = "WORKS_AT" if exp.is_current else "PRE_WORKED_AT"
                await ensure_relation(person_ent.id, org_ent.id, rel_type)
            elif exp.org_name_raw:
                org_ent = await get_or_create_entity(exp.org_name_raw, "organization")
                rel_type = "WORKS_AT" if exp.is_current else "PRE_WORKED_AT"
                await ensure_relation(person_ent.id, org_ent.id, rel_type)

    # ── 2. Load all organizations with org_tags + parent ──────────────────────
    org_result = await db.execute(
        select(Organization)
        .options(
            selectinload(Organization.org_tags).selectinload(OrgTag.tag),
        )
    )
    orgs = org_result.scalars().all()

    # Build a quick id→name map for parent lookups
    org_id_name: dict[str, str] = {o.id: o.name for o in orgs}

    for org in orgs:
        org_ent = await get_or_create_entity(org.name, "organization")

        # FOCUSES_ON topics via org_tags
        for ot in org.org_tags:
            if ot.tag:
                topic_ent = await get_or_create_entity(ot.tag.name, ot.tag.tag_type)
                await ensure_relation(org_ent.id, topic_ent.id, "FOCUSES_ON")

        # SUBSIDIARY_OF parent org
        if org.parent_org_id and org.parent_org_id in org_id_name:
            parent_ent = await get_or_create_entity(org_id_name[org.parent_org_id], "organization")
            await ensure_relation(org_ent.id, parent_ent.id, "SUBSIDIARY_OF")

    await db.commit()

    return {
        "status": "ok",
        "created": created,
        "skipped": skipped,
    }
