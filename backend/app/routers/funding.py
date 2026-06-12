import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FundingEvent
from app.schemas import FundingCreate, FundingOut, FundingUpdate

router = APIRouter(prefix="/funding", tags=["funding"])


@router.get("", response_model=list[FundingOut])
async def list_funding(
    sector: Optional[str] = Query(default=None),
    round: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="search company name"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FundingEvent)
    if sector:
        stmt = stmt.where(FundingEvent.sector == sector)
    if round:
        stmt = stmt.where(FundingEvent.round == round)
    if q:
        stmt = stmt.where(FundingEvent.company_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(
        FundingEvent.announced_at.desc().nullslast(),
        FundingEvent.created_at.desc(),
    ).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/trends")
async def funding_trends(db: AsyncSession = Depends(get_db)):
    """Aggregations for charts: by month, by round, by sector, plus totals."""
    month = func.to_char(func.date_trunc("month", FundingEvent.announced_at), "YYYY-MM")

    by_month = (await db.execute(
        select(month.label("month"),
               func.count().label("count"),
               func.coalesce(func.sum(FundingEvent.amount_usd), 0).label("amount"))
        .where(FundingEvent.announced_at.isnot(None))
        .group_by(month)
        .order_by(month)
    )).all()

    by_round = (await db.execute(
        select(func.coalesce(FundingEvent.round, "未知").label("round"),
               func.count().label("count"),
               func.coalesce(func.sum(FundingEvent.amount_usd), 0).label("amount"))
        .group_by(FundingEvent.round)
        .order_by(func.count().desc())
    )).all()

    by_sector = (await db.execute(
        select(func.coalesce(FundingEvent.sector, "未知").label("sector"),
               func.count().label("count"),
               func.coalesce(func.sum(FundingEvent.amount_usd), 0).label("amount"))
        .group_by(FundingEvent.sector)
        .order_by(func.count().desc())
    )).all()

    total_count = (await db.execute(select(func.count()).select_from(FundingEvent))).scalar_one()
    total_amount = (await db.execute(
        select(func.coalesce(func.sum(FundingEvent.amount_usd), 0))
    )).scalar_one()

    return {
        "total_count": total_count,
        "total_amount_usd": float(total_amount or 0),
        "by_month": [{"month": m, "count": c, "amount_usd": float(a)} for m, c, a in by_month],
        "by_round": [{"round": r, "count": c, "amount_usd": float(a)} for r, c, a in by_round],
        "by_sector": [{"sector": s, "count": c, "amount_usd": float(a)} for s, c, a in by_sector],
    }


@router.get("/{funding_id}", response_model=FundingOut)
async def get_funding(funding_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(FundingEvent, funding_id)
    if not row:
        raise HTTPException(status_code=404, detail="Funding event not found")
    return row


@router.post("", response_model=FundingOut, status_code=201)
async def create_funding(data: FundingCreate, db: AsyncSession = Depends(get_db)):
    row = FundingEvent(id=str(uuid.uuid4()), **data.model_dump(exclude_unset=True))
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{funding_id}", response_model=FundingOut)
async def update_funding(funding_id: str, data: FundingUpdate, db: AsyncSession = Depends(get_db)):
    row = await db.get(FundingEvent, funding_id)
    if not row:
        raise HTTPException(status_code=404, detail="Funding event not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{funding_id}", status_code=204)
async def delete_funding(funding_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(FundingEvent, funding_id)
    if not row:
        raise HTTPException(status_code=404, detail="Funding event not found")
    await db.delete(row)
    await db.commit()
