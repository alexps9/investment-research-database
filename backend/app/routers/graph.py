"""Graph relations: query, structured sync, and implicit-relation inference."""
from __future__ import annotations
from itertools import combinations
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import (
    Source, SourceExperience, Organization, OrgTag, Entity, EntityRelation,
    SourceTag, Tag, Signal, SignalEntity,
)
from app.repositories import EntityRepo
from app.schemas import EntityRelationOut, EntityRelationCreate

router = APIRouter(prefix="/graph", tags=["graph"])

# Cap pairwise colleague inference per organization to avoid an O(n^2) edge
# explosion that would swamp the graph for very large orgs.
_MAX_GROUP_FOR_PAIRS = 25


async def _lookup_entity(db: AsyncSession, name: str, etype: str) -> Entity | None:
    """
    Find an entity by name *or* canonical_name (case-insensitive). Matching on
    both avoids duplicate-key inserts, because the unique constraint lives on
    (canonical_name, entity_type) while data is often referenced by name.
    Picks the oldest match deterministically.
    """
    result = await db.execute(
        select(Entity)
        .where(
            or_(Entity.name.ilike(name), Entity.canonical_name.ilike(name)),
            Entity.entity_type == etype,
        )
        .order_by(Entity.created_at)
    )
    return result.scalars().first()


def _index_entity(index: dict[tuple[str, str], Entity], ent: Entity) -> None:
    """Register an entity under both its name and canonical_name keys."""
    for label in (ent.name, ent.canonical_name):
        if label:
            index.setdefault((ent.entity_type, label.strip().lower()), ent)


async def _build_entity_index(db: AsyncSession) -> dict[tuple[str, str], Entity]:
    """Load all entities once into an (entity_type, lower-name/canonical) map."""
    result = await db.execute(select(Entity).order_by(Entity.created_at))
    index: dict[tuple[str, str], Entity] = {}
    for ent in result.scalars().all():
        _index_entity(index, ent)
    return index


async def _load_relation_triples(db: AsyncSession) -> set[tuple[str, str, str]]:
    """Load all existing (subject, type, object) relation triples once."""
    result = await db.execute(
        select(
            EntityRelation.subject_entity_id,
            EntityRelation.object_entity_id,
            EntityRelation.relation_type,
        )
    )
    return {(s, o, t) for s, o, t in result.all()}


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

    # Preload every entity and existing relation triple in two queries so the
    # rest of the routine runs entirely in memory (no per-item round-trip to a
    # remote DB, which previously made a full sync take minutes).
    entity_index = await _build_entity_index(db)
    existing_triples = await _load_relation_triples(db)

    async def get_or_create_entity(name: str, etype: str) -> Entity:
        nm = name.strip()
        ent = entity_index.get((etype, nm.lower()))
        if ent is not None:
            return ent
        ent = Entity(name=nm, entity_type=etype, canonical_name=nm)
        db.add(ent)
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            # Pre-existing canonical_name under another name (or a race): fall
            # back to a direct lookup.
            ent = await _lookup_entity(db, nm, etype)
            if ent is None:
                raise
        _index_entity(entity_index, ent)
        return ent

    def ensure_relation(subj_id: str, obj_id: str, rel_type: str) -> bool:
        nonlocal created, skipped
        triple = (subj_id, obj_id, rel_type)
        if triple in existing_triples:
            skipped += 1
            return False
        existing_triples.add(triple)
        db.add(EntityRelation(
            subject_entity_id=subj_id,
            object_entity_id=obj_id,
            relation_type=rel_type,
            confidence=0.9,
            extracted_by="sync",
        ))
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
            ensure_relation(person_ent.id, org_ent.id, "WORKS_AT")

        # FOCUSES_ON topics
        for st in src.source_tags:
            if st.tag:
                topic_ent = await get_or_create_entity(st.tag.name, st.tag.tag_type)
                ensure_relation(person_ent.id, topic_ent.id, "FOCUSES_ON")

        # PRE_WORKED_AT past experiences
        for exp in src.experiences:
            if exp.organization:
                org_ent = await get_or_create_entity(exp.organization.name, "organization")
                rel_type = "WORKS_AT" if exp.is_current else "PRE_WORKED_AT"
                ensure_relation(person_ent.id, org_ent.id, rel_type)
            elif exp.org_name_raw:
                org_ent = await get_or_create_entity(exp.org_name_raw, "organization")
                rel_type = "WORKS_AT" if exp.is_current else "PRE_WORKED_AT"
                ensure_relation(person_ent.id, org_ent.id, rel_type)

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
                ensure_relation(org_ent.id, topic_ent.id, "FOCUSES_ON")

        # SUBSIDIARY_OF parent org
        if org.parent_org_id and org.parent_org_id in org_id_name:
            parent_ent = await get_or_create_entity(org_id_name[org.parent_org_id], "organization")
            ensure_relation(org_ent.id, parent_ent.id, "SUBSIDIARY_OF")

    await db.commit()

    return {
        "status": "ok",
        "created": created,
        "skipped": skipped,
    }


@router.post("/infer")
async def infer_relations(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Derive *implicit* relations that aren't entered directly, then materialise
    them as graph edges. Idempotent and symmetric (one edge per unordered pair).

    Inferred:
    - **CO_WORK** between two people who share an organization — either the same
      current org (`source.organization_id`) or a shared work history org
      (`source_experiences`). Captures colleagues / former colleagues.
    - **CO_AUTHOR** between two people linked to the same signal (paper/release)
      via `signal_entities`.

    Person↔topic, person↔org and org↔parent edges are produced by `/graph/sync`;
    org↔org relations (partner/competitor/…) stay manual.
    """
    created = 0
    skipped = 0
    entity_index = await _build_entity_index(db)
    existing_triples = await _load_relation_triples(db)

    async def get_or_create_person(name: str) -> Entity:
        nm = name.strip()
        ent = entity_index.get(("person", nm.lower()))
        if ent is not None:
            return ent
        ent = Entity(name=nm, entity_type="person", canonical_name=nm)
        db.add(ent)
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            ent = await _lookup_entity(db, nm, "person")
            if ent is None:
                raise
        _index_entity(entity_index, ent)
        return ent

    def ensure_symmetric(a_id: str, b_id: str, rel_type: str) -> None:
        """Create one canonical edge (min,max) if neither direction exists."""
        nonlocal created, skipped
        if a_id == b_id:
            return
        subj, obj = sorted([a_id, b_id])
        # Symmetric: skip if an edge of this type exists in *either* direction.
        if (subj, obj, rel_type) in existing_triples or (obj, subj, rel_type) in existing_triples:
            skipped += 1
            return
        existing_triples.add((subj, obj, rel_type))
        db.add(EntityRelation(
            subject_entity_id=subj, object_entity_id=obj,
            relation_type=rel_type, confidence=0.7, extracted_by="infer",
        ))
        created += 1

    # ── 1. Colleagues / former colleagues via shared organizations ────────────
    person_result = await db.execute(
        select(Source)
        .where(Source.source_type == "person")
        .options(
            selectinload(Source.organization),
            selectinload(Source.experiences).selectinload(SourceExperience.organization),
        )
    )
    persons = person_result.scalars().all()

    # org-key → set of person entity ids that share it
    org_groups: dict[str, set[str]] = {}
    for src in persons:
        if not src.name:
            continue
        person_ent = await get_or_create_person(src.name)
        org_keys: set[str] = set()
        if src.organization:
            org_keys.add(f"id::{src.organization.id}")
        for exp in src.experiences:
            if exp.organization:
                org_keys.add(f"id::{exp.organization.id}")
            elif exp.org_name_raw:
                org_keys.add(f"raw::{exp.org_name_raw.strip().lower()}")
        for k in org_keys:
            org_groups.setdefault(k, set()).add(person_ent.id)

    for member_ids in org_groups.values():
        if len(member_ids) < 2 or len(member_ids) > _MAX_GROUP_FOR_PAIRS:
            continue
        for a_id, b_id in combinations(sorted(member_ids), 2):
            ensure_symmetric(a_id, b_id, "CO_WORK")

    # ── 2. Co-authors via shared signals ──────────────────────────────────────
    sig_rows = await db.execute(
        select(SignalEntity.signal_id, SignalEntity.entity_id)
        .join(Entity, Entity.id == SignalEntity.entity_id)
        .where(Entity.entity_type == "person")
    )
    signal_people: dict[str, set[str]] = {}
    for signal_id, entity_id in sig_rows.all():
        signal_people.setdefault(signal_id, set()).add(entity_id)

    for people in signal_people.values():
        if len(people) < 2 or len(people) > _MAX_GROUP_FOR_PAIRS:
            continue
        for a_id, b_id in combinations(sorted(people), 2):
            ensure_symmetric(a_id, b_id, "CO_AUTHOR")

    await db.commit()
    return {"status": "ok", "created": created, "skipped": skipped}
