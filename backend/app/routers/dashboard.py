from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Source, Signal, Entity, EntityRelation, PipelineRun
from app.schemas import PipelineRunOut, SignalOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    source_count = (await db.execute(select(func.count()).select_from(Source))).scalar_one()
    signal_count = (await db.execute(select(func.count()).select_from(Signal))).scalar_one()
    entity_count = (await db.execute(select(func.count()).select_from(Entity))).scalar_one()
    relation_count = (await db.execute(select(func.count()).select_from(EntityRelation))).scalar_one()
    return {
        "total_sources": source_count,
        "total_signals": signal_count,
        "total_entities": entity_count,
        "total_relations": relation_count,
    }


@router.get("/latest-signals", response_model=list[SignalOut])
async def get_latest_signals(limit: int = 10, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Signal)
        .options(selectinload(Signal.analysis))
        .order_by(Signal.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/latest-runs", response_model=list[PipelineRunOut])
async def get_latest_runs(limit: int = 5, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    )
    return result.scalars().all()
