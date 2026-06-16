"""Deep-research proxy router.

The deep-research agent (LangGraph + LiteLLM) runs in the `agent` container on
:9000. The backend proxies `/api/research/*` to it so the frontend reaches
long-running research jobs over the same `/api` channel (and the same
Vercel→Tencent edge proxy) — no extra public port needed.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings

router = APIRouter(prefix="/research", tags=["research"])

_settings = get_settings()
# Deep research can take minutes; status polls must be quick. The /start call
# returns immediately (agent runs the job in the background) so a short connect
# timeout is fine.
_START_TIMEOUT = 15.0
_STATUS_TIMEOUT = 15.0


class ResearchStartRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    max_subtopics: int = Field(default=4, ge=1, le=6)
    searches_per_topic: int = Field(default=2, ge=1, le=4)


def _agent_url(path: str) -> str:
    return f"{_settings.agent_base_url.rstrip('/')}{path}"


@router.post("/start")
async def start_research(body: ResearchStartRequest):
    try:
        async with httpx.AsyncClient(timeout=_START_TIMEOUT) as client:
            resp = await client.post(_agent_url("/research/start"), json=body.model_dump())
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"研究服务不可达: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.get("/status/{job_id}")
async def research_status(job_id: str):
    try:
        async with httpx.AsyncClient(timeout=_STATUS_TIMEOUT) as client:
            resp = await client.get(_agent_url(f"/research/status/{job_id}"))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"研究服务不可达: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="研究任务不存在或已过期")
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
