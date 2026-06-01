from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import PipelineRepo, EntityRepo, SourceRepo, SignalRepo
from app.schemas import PipelineRunOut, PipelineRunCreate

router = APIRouter(prefix="/runs", tags=["pipeline"])


@router.get("", response_model=list[PipelineRunOut])
async def list_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    repo = PipelineRepo(db)
    return await repo.list(limit=limit)


@router.post("/mock", response_model=PipelineRunOut, status_code=201)
async def create_mock_run(data: PipelineRunCreate, db: AsyncSession = Depends(get_db)):
    repo = PipelineRepo(db)
    return await repo.create(data)
