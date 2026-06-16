from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete, func, or_, and_
from sqlalchemy.orm import selectinload

from app.models import (
    Organization, OrgTag, Source, SourceAccount, SourceExperience, Tag, SourceTag,
    Signal, SignalAnalysis, SignalEntity,
    Entity, EntityAlias, EntityRelation,
    PipelineRun,
)
from app.schemas import (
    OrganizationCreate, OrganizationUpdate, OrgTagCreate,
    SourceCreate, SourceUpdate, SourceAccountCreate, SourceTagCreate,
    SourceExperienceCreate,
    SignalCreate, SignalUpdate, SignalAnalysisCreate, SignalEntityCreate,
    EntityCreate, EntityUpdate, EntityAliasCreate, EntityRelationCreate,
    PipelineRunCreate, TagCreate,
)


async def resolve_field_tag_ids(db: AsyncSession, entity_ids: Sequence[str]) -> list[str]:
    """
    Map research-field entity IDs (topic/approach entities) to tag IDs,
    creating a matching tag (by name + type) when one does not yet exist.

    This bridges the two parallel taxonomies: research fields live in the
    `entities` table (managed in the Research Fields page, graph, wiki) while
    source/org topic links use the `tags` table. Tagging by the entity name
    keeps `/graph/sync` (which matches entities by name) consistent.
    """
    if not entity_ids:
        return []
    result = await db.execute(select(Entity).where(Entity.id.in_(list(entity_ids))))
    entities = result.scalars().all()
    tag_ids: list[str] = []
    for ent in entities:
        tag_type = ent.entity_type if ent.entity_type in ("topic", "approach") else "topic"
        existing = await db.execute(select(Tag).where(Tag.name == ent.name))
        tag = existing.scalar_one_or_none()
        if not tag:
            tag = Tag(name=ent.name, tag_type=tag_type)
            db.add(tag)
            await db.flush()
        tag_ids.append(tag.id)
    return tag_ids


# ── Organization ─────────────────────────────────────────────────────────────

class OrganizationRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, skip: int = 0, limit: int = 200) -> Sequence[Organization]:
        result = await self.db.execute(
            select(Organization)
            .options(
                selectinload(Organization.org_tags).selectinload(OrgTag.tag),
            )
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Organization))
        return result.scalar_one()

    async def get(self, org_id: str) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .options(
                selectinload(Organization.org_tags).selectinload(OrgTag.tag),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: OrganizationCreate) -> Organization:
        payload = data.model_dump(exclude={'tag_ids', 'research_field_ids'})
        tag_ids = data.tag_ids
        if data.research_field_ids is not None:
            tag_ids = await resolve_field_tag_ids(self.db, data.research_field_ids)

        obj = Organization(**payload)
        self.db.add(obj)
        await self.db.flush()

        if tag_ids:
            for tid in tag_ids:
                self.db.add(OrgTag(org_id=obj.id, tag_id=tid))

        await self.db.commit()
        return await self.get(obj.id)  # type: ignore[return-value]

    async def update(self, org: Organization, data: OrganizationUpdate) -> Organization:
        updates = data.model_dump(exclude_unset=True, exclude={'tag_ids', 'research_field_ids'})
        for key, value in updates.items():
            setattr(org, key, value)

        tag_ids = data.tag_ids
        if data.research_field_ids is not None:
            tag_ids = await resolve_field_tag_ids(self.db, data.research_field_ids)

        if tag_ids is not None:
            await self.db.execute(
                sa_delete(OrgTag).where(OrgTag.org_id == org.id)
            )
            for tid in tag_ids:
                self.db.add(OrgTag(org_id=org.id, tag_id=tid))

        await self.db.commit()
        return await self.get(org.id)  # type: ignore[return-value]

    async def delete(self, org: Organization) -> None:
        await self.db.delete(org)
        await self.db.commit()


# ── Source ────────────────────────────────────────────────────────────────────

class SourceRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, skip: int = 0, limit: int = 100, source_type: Optional[str] = None) -> Sequence[Source]:
        stmt = (
            select(Source)
            .options(
                selectinload(Source.organization).selectinload(Organization.org_tags).selectinload(OrgTag.tag),
                selectinload(Source.accounts),
                selectinload(Source.source_tags).selectinload(SourceTag.tag),
                selectinload(Source.experiences).selectinload(SourceExperience.organization).selectinload(Organization.org_tags),
            )
            .offset(skip)
            .limit(limit)
        )
        if source_type:
            stmt = stmt.where(Source.source_type == source_type)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Source))
        return result.scalar_one()

    async def get(self, source_id: str) -> Optional[Source]:
        result = await self.db.execute(
            select(Source)
            .where(Source.id == source_id)
            .options(
                selectinload(Source.organization).selectinload(Organization.org_tags).selectinload(OrgTag.tag),
                selectinload(Source.accounts),
                selectinload(Source.source_tags).selectinload(SourceTag.tag),
                selectinload(Source.experiences).selectinload(SourceExperience.organization).selectinload(Organization.org_tags),
            )
        )
        return result.scalar_one_or_none()

    async def get_experiences(self, source_id: str) -> Sequence[SourceExperience]:
        result = await self.db.execute(
            select(SourceExperience)
            .where(SourceExperience.source_id == source_id)
            .options(selectinload(SourceExperience.organization))
            .order_by(SourceExperience.is_current.desc(), SourceExperience.start_date.desc())
        )
        return result.scalars().all()

    async def add_experience(self, source_id: str, data: SourceExperienceCreate) -> SourceExperience:
        obj = SourceExperience(source_id=source_id, **data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        result = await self.db.execute(
            select(SourceExperience)
            .where(SourceExperience.id == obj.id)
            .options(selectinload(SourceExperience.organization))
        )
        return result.scalar_one()

    async def delete_experience(self, exp: SourceExperience) -> None:
        await self.db.delete(exp)
        await self.db.commit()

    async def get_experience(self, exp_id: str) -> Optional[SourceExperience]:
        result = await self.db.execute(
            select(SourceExperience).where(SourceExperience.id == exp_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: SourceCreate) -> Source:
        payload = data.model_dump()
        tag_ids = payload.pop("tag_ids", None)
        field_ids = payload.pop("research_field_ids", None)

        obj = Source(**payload)
        self.db.add(obj)
        await self.db.flush()

        if field_ids is not None:
            tag_ids = await resolve_field_tag_ids(self.db, field_ids)
        if tag_ids:
            for tid in tag_ids:
                self.db.add(SourceTag(source_id=obj.id, tag_id=tid, assigned_by="manual"))

        await self.db.commit()
        return await self.get(obj.id)

    async def update(self, source: Source, data: SourceUpdate) -> Source:
        payload = data.model_dump(exclude_unset=True)
        tag_ids = payload.pop("tag_ids", None)
        field_ids = payload.pop("research_field_ids", None)

        for key, value in payload.items():
            setattr(source, key, value)

        # research_field_ids takes precedence and is resolved to tag IDs
        if field_ids is not None:
            tag_ids = await resolve_field_tag_ids(self.db, field_ids)

        # Atomically replace topic tags when a tag set is explicitly provided
        if tag_ids is not None:
            await self.db.execute(
                sa_delete(SourceTag).where(SourceTag.source_id == source.id)
            )
            for tid in tag_ids:
                self.db.add(SourceTag(source_id=source.id, tag_id=tid, assigned_by="manual"))

        await self.db.commit()
        return await self.get(source.id)

    async def delete(self, source: Source) -> None:
        await self.db.delete(source)
        await self.db.commit()

    async def add_account(self, source_id: str, data: SourceAccountCreate) -> SourceAccount:
        obj = SourceAccount(source_id=source_id, **data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def add_tag(self, source_id: str, data: SourceTagCreate) -> SourceTag:
        obj = SourceTag(source_id=source_id, **data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def search(self, q: str, limit: int = 10) -> Sequence[Source]:
        result = await self.db.execute(
            select(Source)
            .options(selectinload(Source.organization), selectinload(Source.accounts))
            .where(Source.name.ilike(f"%{q}%"))
            .limit(limit)
        )
        return result.scalars().all()


# ── Tag ───────────────────────────────────────────────────────────────────────

class TagRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> Sequence[Tag]:
        result = await self.db.execute(select(Tag))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    async def get(self, tag_id: str) -> Optional[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def list_by_type(self, tag_type: Optional[str] = None) -> Sequence[Tag]:
        stmt = select(Tag).order_by(Tag.name)
        if tag_type:
            stmt = stmt.where(Tag.tag_type == tag_type)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, name: str, tag_type: str = "topic", parent_id: Optional[str] = None) -> Tag:
        obj = Tag(name=name, tag_type=tag_type, parent_id=parent_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, tag: Tag, data: dict) -> Tag:
        for key, value in data.items():
            setattr(tag, key, value)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete(self, tag: Tag) -> None:
        await self.db.delete(tag)
        await self.db.commit()


# ── Signal ────────────────────────────────────────────────────────────────────

class SignalRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        skip: int = 0,
        limit: int = 50,
        signal_type: Optional[str] = None,
        source_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        published_from: Optional[str] = None,
        published_to: Optional[str] = None,
    ) -> Sequence[Signal]:
        stmt = (
            select(Signal)
            .options(selectinload(Signal.analysis))
            .order_by(Signal.created_at.desc())
        )
        if signal_type:
            stmt = stmt.where(Signal.signal_type == signal_type)
        if source_id:
            stmt = stmt.where(Signal.source_id == source_id)
        if organization_id:
            stmt = stmt.where(Signal.organization_id == organization_id)
        if status:
            stmt = stmt.where(Signal.status == status)
        if q:
            stmt = stmt.where(or_(Signal.title.ilike(f"%{q}%"), Signal.abstract.ilike(f"%{q}%")))
        if published_from:
            stmt = stmt.where(Signal.published_at >= published_from)
        if published_to:
            stmt = stmt.where(Signal.published_at <= published_to)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self, **kwargs) -> int:
        result = await self.db.execute(select(func.count()).select_from(Signal))
        return result.scalar_one()

    async def get(self, signal_id: str) -> Optional[Signal]:
        result = await self.db.execute(
            select(Signal)
            .where(Signal.id == signal_id)
            .options(
                selectinload(Signal.analysis),
                selectinload(Signal.signal_entities).selectinload(SignalEntity.entity),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: SignalCreate) -> Signal:
        obj = Signal(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, signal: Signal, data: SignalUpdate) -> Signal:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(signal, key, value)
        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def delete(self, signal: Signal) -> None:
        await self.db.delete(signal)
        await self.db.commit()

    async def add_analysis(self, signal_id: str, data: SignalAnalysisCreate) -> SignalAnalysis:
        payload = data.model_dump()
        metadata = payload.pop("metadata", {})
        obj = SignalAnalysis(signal_id=signal_id, metadata_=metadata, **payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def add_entity(self, signal_id: str, data: SignalEntityCreate) -> SignalEntity:
        obj = SignalEntity(signal_id=signal_id, **data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_related(self, signal_id: str, limit: int = 10) -> Sequence[Signal]:
        # Related signals share entity links
        subq = (
            select(SignalEntity.entity_id)
            .where(SignalEntity.signal_id == signal_id)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(Signal)
            .join(SignalEntity, Signal.id == SignalEntity.signal_id)
            .where(
                and_(
                    SignalEntity.entity_id.in_(subq),
                    Signal.id != signal_id,
                )
            )
            .options(selectinload(Signal.analysis))
            .limit(limit)
        )
        return result.scalars().all()

    async def search(self, q: str, limit: int = 10) -> Sequence[Signal]:
        result = await self.db.execute(
            select(Signal)
            .options(selectinload(Signal.analysis))
            .where(or_(Signal.title.ilike(f"%{q}%"), Signal.abstract.ilike(f"%{q}%")))
            .limit(limit)
        )
        return result.scalars().all()


# ── Entity ────────────────────────────────────────────────────────────────────

class EntityRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        entity_type: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Sequence[Entity]:
        stmt = (
            select(Entity)
            .options(selectinload(Entity.aliases))
            .order_by(Entity.canonical_name)
        )
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        if q:
            stmt = stmt.where(
                or_(Entity.name.ilike(f"%{q}%"), Entity.canonical_name.ilike(f"%{q}%"))
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Entity))
        return result.scalar_one()

    async def get(self, entity_id: str) -> Optional[Entity]:
        result = await self.db.execute(
            select(Entity)
            .where(Entity.id == entity_id)
            .options(selectinload(Entity.aliases))
        )
        return result.scalar_one_or_none()

    async def get_by_name_type(self, name: str, entity_type: str) -> Optional[Entity]:
        result = await self.db.execute(
            select(Entity)
            .where(Entity.name.ilike(name.strip()), Entity.entity_type == entity_type)
            .options(selectinload(Entity.aliases))
        )
        return result.scalars().first()

    async def create(self, data: EntityCreate) -> Entity:
        payload = data.model_dump()
        metadata = payload.pop("metadata", {})
        obj = Entity(metadata_=metadata, **payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return await self.get(obj.id)

    async def update(self, entity: Entity, data: EntityUpdate) -> Entity:
        payload = data.model_dump(exclude_unset=True)
        if "metadata" in payload:
            payload["metadata_"] = payload.pop("metadata")
        for key, value in payload.items():
            setattr(entity, key, value)
        await self.db.commit()
        return await self.get(entity.id)

    async def delete(self, entity: Entity) -> None:
        await self.db.delete(entity)
        await self.db.commit()

    async def add_alias(self, entity_id: str, data: EntityAliasCreate) -> EntityAlias:
        obj = EntityAlias(entity_id=entity_id, **data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_signals(self, entity_id: str, limit: int = 20) -> Sequence[Signal]:
        result = await self.db.execute(
            select(Signal)
            .join(SignalEntity, Signal.id == SignalEntity.signal_id)
            .where(SignalEntity.entity_id == entity_id)
            .options(selectinload(Signal.analysis))
            .order_by(Signal.published_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_relations(self, entity_id: str) -> Sequence[EntityRelation]:
        result = await self.db.execute(
            select(EntityRelation)
            .where(
                or_(
                    EntityRelation.subject_entity_id == entity_id,
                    EntityRelation.object_entity_id == entity_id,
                )
            )
            .options(
                selectinload(EntityRelation.subject).selectinload(Entity.aliases),
                selectinload(EntityRelation.object_entity).selectinload(Entity.aliases),
            )
        )
        return result.scalars().all()

    async def add_relation(self, data: EntityRelationCreate) -> EntityRelation:
        obj = EntityRelation(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        # Eager-load subject/object so EntityRelationOut serialization doesn't
        # trigger a lazy load outside the async context (MissingGreenlet).
        result = await self.db.execute(
            select(EntityRelation)
            .where(EntityRelation.id == obj.id)
            .options(
                selectinload(EntityRelation.subject).selectinload(Entity.aliases),
                selectinload(EntityRelation.object_entity).selectinload(Entity.aliases),
            )
        )
        return result.scalar_one()

    async def get_relation(self, relation_id: str) -> Optional[EntityRelation]:
        result = await self.db.execute(
            select(EntityRelation).where(EntityRelation.id == relation_id)
        )
        return result.scalar_one_or_none()

    async def delete_relation(self, relation: EntityRelation) -> None:
        await self.db.delete(relation)
        await self.db.commit()

    async def count_signal_entities(self, entity_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(SignalEntity).where(SignalEntity.entity_id == entity_id)
        )
        return result.scalar_one()

    async def count_relations(self, entity_id: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(EntityRelation)
            .where(
                or_(
                    EntityRelation.subject_entity_id == entity_id,
                    EntityRelation.object_entity_id == entity_id,
                )
            )
        )
        return result.scalar_one()

    async def search(self, q: str, limit: int = 10) -> Sequence[Entity]:
        result = await self.db.execute(
            select(Entity)
            .options(selectinload(Entity.aliases))
            .where(
                or_(Entity.name.ilike(f"%{q}%"), Entity.canonical_name.ilike(f"%{q}%"))
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def get_outgoing_relations(self, entity_id: str) -> Sequence[EntityRelation]:
        result = await self.db.execute(
            select(EntityRelation)
            .where(EntityRelation.subject_entity_id == entity_id)
            .options(selectinload(EntityRelation.object_entity).selectinload(Entity.aliases))
        )
        return result.scalars().all()

    async def get_incoming_relations(self, entity_id: str) -> Sequence[EntityRelation]:
        result = await self.db.execute(
            select(EntityRelation)
            .where(EntityRelation.object_entity_id == entity_id)
            .options(selectinload(EntityRelation.subject).selectinload(Entity.aliases))
        )
        return result.scalars().all()

    async def get_all_relations(self, limit: int = 500) -> Sequence[EntityRelation]:
        result = await self.db.execute(
            select(EntityRelation)
            .options(
                selectinload(EntityRelation.subject).selectinload(Entity.aliases),
                selectinload(EntityRelation.object_entity).selectinload(Entity.aliases),
            )
            .limit(limit)
        )
        return result.scalars().all()


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, limit: int = 50) -> Sequence[PipelineRun]:
        result = await self.db.execute(
            select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def create(self, data: PipelineRunCreate) -> PipelineRun:
        payload = data.model_dump()
        metadata = payload.pop("metadata", {})
        obj = PipelineRun(metadata_=metadata, **payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
