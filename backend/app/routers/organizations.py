"""Organizations CRUD with tag/parent-org management."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories import OrganizationRepo
from app.schemas import (
    OrganizationOut, OrganizationCreate, OrganizationUpdate,
    OrgTagCreate, OrgTagOut,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(
    skip: int = 0,
    limit: int = 200,
    q: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = OrganizationRepo(db)
    orgs = await repo.list(skip=skip, limit=limit)
    if q:
        kw = q.lower()
        orgs = [o for o in orgs if kw in o.name.lower()]
    return orgs


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(data: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepo(db)
    return await repo.create(data)


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: str, db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepo(db)
    org = await repo.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationOut)
async def update_organization(org_id: str, data: OrganizationUpdate, db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepo(db)
    org = await repo.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return await repo.update(org, data)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(org_id: str, db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepo(db)
    org = await repo.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    await repo.delete(org)
