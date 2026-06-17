from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Source, Signal, Entity, EntityRelation, PipelineRun
from app.schemas import PipelineRunOut, SignalOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # One round-trip instead of four — the DB is in another region (~120ms each),
    # so collapsing the counts into a single scalar-subquery row is a 4x win.
    row = (await db.execute(
        select(
            select(func.count()).select_from(Source).scalar_subquery(),
            select(func.count()).select_from(Signal).scalar_subquery(),
            select(func.count()).select_from(Entity).scalar_subquery(),
            select(func.count()).select_from(EntityRelation).scalar_subquery(),
        )
    )).one()
    return {
        "total_sources": row[0],
        "total_signals": row[1],
        "total_entities": row[2],
        "total_relations": row[3],
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
