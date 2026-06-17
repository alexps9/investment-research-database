"""Research Studio session persistence + agent proxy.

Creates a DB row per research run, forwards work to the agent container, and
persists the final report/scope/industry when the agent job completes.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.models import ResearchSession
from app.schemas import ResearchSessionCreate, ResearchSessionListOut, ResearchSessionOut

router = APIRouter(prefix="/research/sessions", tags=["research-sessions"])

_settings = get_settings()
_START_TIMEOUT = 15.0
_STATUS_TIMEOUT = 15.0


def _agent_url(path: str) -> str:
    return f"{_settings.agent_base_url.rstrip('/')}{path}"


async def _sync_from_agent(session: ResearchSession, db: AsyncSession) -> ResearchSession:
    """Poll agent job and persist result when done."""
    if session.status != "running" or not session.agent_job_id:
        return session
    try:
        async with httpx.AsyncClient(timeout=_STATUS_TIMEOUT) as client:
            resp = await client.get(_agent_url(f"/research/status/{session.agent_job_id}"))
    except httpx.RequestError:
        return session
    if resp.status_code == 404:
        session.status = "failed"
        session.error = "研究任务不存在或已过期"
        await db.commit()
        await db.refresh(session)
        return session
    if resp.status_code >= 400:
        return session
    job = resp.json()
    session.phase = job.get("phase")
    session.pct = int(job.get("pct") or 0)
    if job.get("status") == "running":
        await db.commit()
        await db.refresh(session)
        return session
    if job.get("status") == "failed":
        session.status = "failed"
        session.error = job.get("error") or job.get("message") or "研究失败"
        await db.commit()
        await db.refresh(session)
        return session
    if job.get("status") == "done":
        result = job.get("result") or {}
        session.status = "done"
        session.phase = "done"
        session.pct = 100
        session.brief = result.get("brief")
        session.subtopics = result.get("subtopics") or []
        session.report = result.get("report")
        session.sources = result.get("sources") or []
        session.kb_sources = result.get("kb_sources") or []
        session.scope = result.get("scope")
        session.industry = result.get("industry")
        session.error = None
        await db.commit()
        await db.refresh(session)
    return session


@router.post("", response_model=ResearchSessionOut, status_code=201)
async def create_session(body: ResearchSessionCreate, db: AsyncSession = Depends(get_db)):
    session = ResearchSession(question=body.question.strip())
    db.add(session)
    await db.flush()
    try:
        async with httpx.AsyncClient(timeout=_START_TIMEOUT) as client:
            resp = await client.post(
                _agent_url("/research/start"),
                json={
                    "question": body.question,
                    "max_subtopics": body.max_subtopics,
                    "searches_per_topic": body.searches_per_topic,
                },
            )
    except httpx.RequestError as exc:
        session.status = "failed"
        session.error = f"研究服务不可达: {exc}"
        await db.commit()
        await db.refresh(session)
        raise HTTPException(status_code=502, detail=session.error) from exc
    if resp.status_code >= 400:
        session.status = "failed"
        session.error = resp.text
        await db.commit()
        await db.refresh(session)
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    session.agent_job_id = data.get("job_id")
    session.phase = "queued"
    session.pct = 0
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[ResearchSessionListOut])
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(ResearchSession)
        .order_by(desc(ResearchSession.created_at))
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.get("/{session_id}", response_model=ResearchSessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.status == "running":
        session = await _sync_from_agent(session, db)
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.delete(session)
    await db.commit()
