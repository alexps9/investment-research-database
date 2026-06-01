from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import SourceRepo, SignalRepo, EntityRepo
from app.schemas import SearchResults

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResults)
async def search(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    sources = await SourceRepo(db).search(q)
    signals = await SignalRepo(db).search(q)
    entities = await EntityRepo(db).search(q)
    return SearchResults(sources=list(sources), signals=list(signals), entities=list(entities))
