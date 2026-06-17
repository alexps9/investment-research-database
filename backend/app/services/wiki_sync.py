"""Keep a knowledge-graph entity (and therefore its wiki page) in sync with a
signal-source record.

The wiki is an entity-centric view, so a source only "has a wiki" once a mirror
entity exists. This service is called whenever a person/organization source is
created or updated so that:

  - creating a source auto-creates its wiki entity (name, intro, homepage, infobox
    metadata), and
  - updating a source refreshes that entity (including renames, tracked via a
    stable ``source_id`` stored in the entity metadata).

It is best-effort and runs in its own transaction *after* the source has been
committed, so a sync hiccup can never break source CRUD.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entity, Organization, Source

# Only these source types correspond to graph entities with wiki pages.
MIRRORED_TYPES = {"person", "organization"}


def _homepage(s: Source) -> str | None:
    for v in (s.personal_url, s.arxiv_homepage_url, s.scholar_url, s.openalex_url,
              s.github_url, s.twitter_url):
        if v:
            return v
    return None


async def _metadata(db: AsyncSession, s: Source) -> dict:
    meta: dict = {"source_id": s.id}
    for key in ("role_title", "tier", "sector", "research_focus", "source_authority",
                "affiliation_type"):
        val = getattr(s, key, None)
        if val:
            meta[key] = val
    if s.organization_id:
        name = (await db.execute(
            select(Organization.name).where(Organization.id == s.organization_id)
        )).scalar_one_or_none()
        if name:
            meta["organization"] = name
    return meta


async def _find_entity(db: AsyncSession, s: Source) -> Entity | None:
    # Prefer the stable source_id link (survives renames); fall back to name+type.
    linked = (await db.execute(
        select(Entity).where(
            Entity.entity_type == s.source_type,
            Entity.metadata_["source_id"].astext == s.id,
        )
    )).scalars().first()
    if linked is not None:
        return linked
    return (await db.execute(
        select(Entity).where(
            Entity.entity_type == s.source_type,
            Entity.name.ilike((s.name or "").strip()),
        )
    )).scalars().first()


async def sync_source_to_entity(db: AsyncSession, source: Source) -> Entity | None:
    """Create or refresh the wiki entity mirroring ``source``. Returns the entity,
    or None when the source type isn't mirrored / sync was skipped."""
    if source.source_type not in MIRRORED_TYPES or not (source.name or "").strip():
        return None

    name = source.name.strip()
    homepage = _homepage(source)
    meta = await _metadata(db, source)
    ent = await _find_entity(db, source)

    if ent is None:
        ent = Entity(
            name=name, canonical_name=name, entity_type=source.source_type,
            introduction=(source.description or None), homepage_url=homepage, metadata_=meta,
        )
        db.add(ent)
    else:
        # Rename: keep display name aligned (canonical_name stays put so the
        # unique (canonical_name, entity_type) index isn't disturbed).
        ent.name = name
        if not ent.canonical_name:
            ent.canonical_name = name
        if source.description:
            ent.introduction = source.description
        if homepage:
            ent.homepage_url = homepage
        merged = dict(ent.metadata_ or {})
        merged.update(meta)
        ent.metadata_ = merged

    try:
        await db.commit()
    except IntegrityError:
        # A different entity already owns this canonical_name+type — adopt it.
        await db.rollback()
        existing = (await db.execute(
            select(Entity).where(
                Entity.entity_type == source.source_type,
                Entity.canonical_name.ilike(name),
            )
        )).scalars().first()
        if existing is None:
            return None
        merged = dict(existing.metadata_ or {})
        merged.update(meta)
        existing.metadata_ = merged
        if source.description and not existing.introduction:
            existing.introduction = source.description
        if homepage and not existing.homepage_url:
            existing.homepage_url = homepage
        await db.commit()
        return existing
    return ent
