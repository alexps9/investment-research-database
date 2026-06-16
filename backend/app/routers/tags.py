"""Tags CRUD — topic / approach classification."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import TagRepo
from app.schemas import TagOut, TagCreate, TagTreeOut

router = APIRouter(prefix="/tags", tags=["tags"])


def _build_tree(tags: list[TagOut]) -> list[TagTreeOut]:
    """Assemble flat tag list into parent-child tree."""
    by_id: dict[str, TagTreeOut] = {t.id: TagTreeOut(**t.model_dump()) for t in tags}
    roots: list[TagTreeOut] = []
    for node in by_id.values():
        if node.parent_id and node.parent_id in by_id:
            by_id[node.parent_id].children.append(node)
        else:
            roots.append(node)
    return sorted(roots, key=lambda x: x.name)


@router.get("", response_model=list[TagOut])
async def list_tags(
    tag_type: Optional[str] = Query(default=None, description="Filter by type: topic, approach, domain…"),
    db: AsyncSession = Depends(get_db),
):
    repo = TagRepo(db)
    return await repo.list_by_type(tag_type)


@router.get("/tree", response_model=list[TagTreeOut])
async def tag_tree(
    tag_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Return tags as a nested tree (for hierarchical topic selectors)."""
    repo = TagRepo(db)
    flat = await repo.list_by_type(tag_type)
    flat_out = [TagOut.model_validate(t) for t in flat]
    return _build_tree(flat_out)


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db)):
    repo = TagRepo(db)
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=409, detail="Tag name already exists")
    return await repo.create(
        name=data.name,
        tag_type=data.tag_type,
        parent_id=data.parent_id,
    )


@router.patch("/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    repo = TagRepo(db)
    tag = await repo.get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    allowed = {"name", "tag_type", "parent_id", "description"}
    payload = {k: v for k, v in data.items() if k in allowed}
    return await repo.update(tag, payload)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, db: AsyncSession = Depends(get_db)):
    repo = TagRepo(db)
    tag = await repo.get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await repo.delete(tag)
