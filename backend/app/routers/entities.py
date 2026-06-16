from typing import Optional
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import EntityRepo
from app.schemas import (
    EntityOut, EntityCreate, EntityUpdate,
    EntityAliasCreate, EntityAliasOut,
    EntityRelationCreate, EntityRelationOut,
    SignalOut,
)
from app.models import VALID_RELATION_TYPES

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=list[EntityOut])
async def list_entities(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = EntityRepo(db)
    return await repo.list(skip=skip, limit=limit, entity_type=entity_type, q=q)


@router.post("", response_model=EntityOut, status_code=201)
async def create_entity(data: EntityCreate, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    return await repo.create(data)


@router.get("/{entity_id}", response_model=EntityOut)
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}", response_model=EntityOut)
async def update_entity(entity_id: str, data: EntityUpdate, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return await repo.update(entity, data)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    """Delete entity and cascade-remove all its graph relations."""
    repo = EntityRepo(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    await repo.delete(entity)


@router.post("/{entity_id}/aliases", response_model=EntityAliasOut, status_code=201)
async def add_alias(entity_id: str, data: EntityAliasCreate, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return await repo.add_alias(entity_id, data)


@router.get("/{entity_id}/signals", response_model=list[SignalOut])
async def get_entity_signals(entity_id: str, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    return await repo.get_signals(entity_id)


@router.get("/{entity_id}/relations", response_model=list[EntityRelationOut])
async def get_entity_relations(entity_id: str, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    return await repo.get_relations(entity_id)


@router.post("/{entity_id}/relations", response_model=EntityRelationOut, status_code=201)
async def add_relation(entity_id: str, data: EntityRelationCreate, db: AsyncSession = Depends(get_db)):
    if data.relation_type not in VALID_RELATION_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid relation_type. Valid types: {sorted(VALID_RELATION_TYPES)}",
        )
    if data.subject_entity_id != entity_id:
        raise HTTPException(status_code=422, detail="subject_entity_id must match path entity_id")
    repo = EntityRepo(db)
    return await repo.add_relation(data)


@router.delete("/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(relation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a single entity relation by ID."""
    repo = EntityRepo(db)
    rel = await repo.get_relation(relation_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    await repo.delete_relation(rel)
