from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import SourceRepo, OrganizationRepo
from app.schemas import (
    SourceOut, SourceCreate, SourceUpdate,
    SourceAccountCreate, SourceAccountOut,
    SourceTagCreate, SourceTagOut,
    OrganizationOut, OrganizationCreate,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    return await repo.list(skip=skip, limit=limit)


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepo(db)
    return await repo.create(data)


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
    return await repo.update(source, data)


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
