from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import SignalRepo
from app.schemas import (
    SignalOut, SignalCreate, SignalUpdate,
    SignalAnalysisCreate, SignalAnalysisOut,
    SignalEntityCreate,
)

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalOut])
async def list_signals(
    skip: int = 0,
    limit: int = 50,
    signal_type: Optional[str] = Query(default=None),
    source_id: Optional[str] = Query(default=None),
    organization_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    published_from: Optional[str] = Query(default=None),
    published_to: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = SignalRepo(db)
    return await repo.list(
        skip=skip,
        limit=limit,
        signal_type=signal_type,
        source_id=source_id,
        organization_id=organization_id,
        status=status,
        q=q,
        published_from=published_from,
        published_to=published_to,
    )


@router.post("", response_model=SignalOut, status_code=201)
async def create_signal(data: SignalCreate, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    return await repo.create(data)


@router.get("/{signal_id}", response_model=SignalOut)
async def get_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    signal = await repo.get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.patch("/{signal_id}", response_model=SignalOut)
async def update_signal(signal_id: str, data: SignalUpdate, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    signal = await repo.get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return await repo.update(signal, data)


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    signal = await repo.get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    await repo.delete(signal)


@router.post("/{signal_id}/analysis", response_model=SignalAnalysisOut, status_code=201)
async def add_analysis(signal_id: str, data: SignalAnalysisCreate, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    signal = await repo.get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return await repo.add_analysis(signal_id, data)


@router.post("/{signal_id}/entities", status_code=201)
async def add_entity_mention(signal_id: str, data: SignalEntityCreate, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    signal = await repo.get(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return await repo.add_entity(signal_id, data)


@router.get("/{signal_id}/related", response_model=list[SignalOut])
async def get_related_signals(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepo(db)
    return await repo.get_related(signal_id)
