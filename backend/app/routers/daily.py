from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DailyDigest
from app.schemas import DailyDigestOut
from app.services import daily

router = APIRouter(prefix="/daily", tags=["daily-boost"])


@router.get("", response_model=list[DailyDigestOut])
async def list_digests(limit: int = Query(default=30, le=120), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DailyDigest).order_by(DailyDigest.digest_date.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/latest", response_model=Optional[DailyDigestOut])
async def latest_digest(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DailyDigest).order_by(DailyDigest.digest_date.desc()).limit(1)
    )
    return result.scalars().first()


@router.get("/{digest_date}", response_model=DailyDigestOut)
async def get_digest(digest_date: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DailyDigest).where(DailyDigest.digest_date == digest_date)
    )
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="No digest for that date")
    return row


@router.post("/generate", response_model=DailyDigestOut)
async def generate(
    digest_date: Optional[str] = Query(default=None, description="YYYY-MM-DD; default today (UTC)"),
    window_days: int = Query(default=1, ge=1, le=30),
    limit: int = Query(default=8, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await daily.generate_digest(db, digest_date, window_days=window_days, limit=limit)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Digest generation error: {e}")
