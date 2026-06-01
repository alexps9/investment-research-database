from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import EntityRepo
from app.schemas import WikiEntityProfile, EntityOut

router = APIRouter(prefix="/wiki", tags=["wiki"])


@router.get("/entities/{entity_id}", response_model=WikiEntityProfile)
async def get_entity_wiki(entity_id: str, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    signals = await repo.get_signals(entity_id, limit=20)
    outgoing = await repo.get_outgoing_relations(entity_id)
    incoming = await repo.get_incoming_relations(entity_id)

    related_entity_ids: set[str] = set()
    for rel in outgoing:
        related_entity_ids.add(rel.object_entity_id)
    for rel in incoming:
        related_entity_ids.add(rel.subject_entity_id)
    related_entity_ids.discard(entity_id)

    related_entities = []
    for eid in list(related_entity_ids)[:10]:
        e = await repo.get(eid)
        if e:
            related_entities.append(e)

    return WikiEntityProfile(
        entity=entity,
        aliases=entity.aliases,
        related_signals=list(signals),
        outgoing_relations=list(outgoing),
        incoming_relations=list(incoming),
        related_entities=related_entities,
    )
