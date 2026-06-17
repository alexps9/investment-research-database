from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import SourceRepo, OrganizationRepo
from app.schemas import (
    SourceOut, SourceListOut, SourceCreate, SourceUpdate,
    SourceAccountCreate, SourceAccountOut,
    SourceTagCreate, SourceTagOut,
    SourceExperienceCreate, SourceExperienceOut,
    OrganizationOut, OrganizationCreate,
)
from app.services.wiki_sync import sync_source_to_entity

router = APIRouter(prefix="/sources", tags=["sources"])


async def _sync_wiki(db: AsyncSession, source) -> None:
    """Auto-create / refresh the source's wiki entity (best-effort)."""
    try:
        await sync_source_to_entity(db, source)
    except Exception:
        # Never let wiki mirroring break source CRUD; the graph sync job will
        # reconcile any source that slipped through.
        await db.rollback()


@router.get("", response_model=list[SourceListOut])
async def list_sources(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepo(db)
    return await repo.list(skip=skip, limit=limit, source_type=source_type)


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.create(data)
    await _sync_wiki(db, source)
    return source


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(source_id: str, data: SourceUpdate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    updated = await repo.update(source, data)
    await _sync_wiki(db, updated)
    return updated


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await repo.delete(source)


@router.post("/{source_id}/accounts", response_model=SourceAccountOut, status_code=status.HTTP_201_CREATED)
async def add_account(source_id: str, data: SourceAccountCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return await repo.add_account(source_id, data)


@router.post("/{source_id}/tags", response_model=SourceTagOut, status_code=status.HTTP_201_CREATED)
async def add_tag(source_id: str, data: SourceTagCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    source = await repo.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return await repo.add_tag(source_id, data)


# ── Experiences ────────────────────────────────────────────────────────────────

@router.get("/{source_id}/experiences", response_model=list[SourceExperienceOut])
async def list_experiences(source_id: str, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    if not await repo.get(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return await repo.get_experiences(source_id)


@router.post("/{source_id}/experiences", response_model=SourceExperienceOut, status_code=status.HTTP_201_CREATED)
async def add_experience(source_id: str, data: SourceExperienceCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    if not await repo.get(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return await repo.add_experience(source_id, data)


@router.delete("/{source_id}/experiences/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(source_id: str, exp_id: str, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    exp = await repo.get_experience(exp_id)
    if not exp or exp.source_id != source_id:
        raise HTTPException(status_code=404, detail="Experience not found")
    await repo.delete_experience(exp)
