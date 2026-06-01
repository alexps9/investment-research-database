from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import EntityRepo
from app.schemas import EntityRelationOut

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/relations", response_model=list[EntityRelationOut])
async def get_all_relations(limit: int = 500, db: AsyncSession = Depends(get_db)):
    repo = EntityRepo(db)
    return await repo.get_all_relations(limit=limit)
