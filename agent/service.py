"""FastAPI service — Data Agent Q&A + manual pipeline triggers."""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from typing import Any, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.data_agent import ask_data_agent
from agent.run import run_pipeline
from agent.analysis_agent import run_analysis
from agent.alert_agent.node import run_alerts
from agent.digest_agent.node import run_digest
from agent.entity_agent import run_entity_extraction
from agent.ingestion_agent import run_ingestion
from agent.deep_research_agent import run_deep_research

app = FastAPI(title="HH-Research Agent Service", version="2.0.0")

# Track background job status (in-memory; sufficient for single-container deploy)
_jobs: dict[str, dict[str, Any]] = {}
# Deep-research jobs (long-running; polled for progress + final report)
_research_jobs: dict[str, dict[str, Any]] = {}

# ── Deep-research multi-user controls ────────────────────────────────────────
# The whole pipeline funnels into one LiteLLM worker + one Bedrock account + one
# proxy node, so cap how many runs execute at once and queue the rest. A run that
# can't get a slot stays "queued" (status still "running" so the frontend keeps
# polling) until one frees up. RESEARCH_MAX_PENDING bounds running+queued so a
# burst can't blow up memory / the gateway.
RESEARCH_MAX_CONCURRENT = int(os.getenv("RESEARCH_MAX_CONCURRENT", "2"))
RESEARCH_MAX_PENDING = int(os.getenv("RESEARCH_MAX_PENDING", "12"))
# Drop finished (done/failed) jobs this many seconds after they end so the
# in-memory store stays bounded.
RESEARCH_JOB_TTL = int(os.getenv("RESEARCH_JOB_TTL", "3600"))
_research_sem = asyncio.Semaphore(RESEARCH_MAX_CONCURRENT)


def _prune_research_jobs() -> None:
    """Evict finished jobs past their TTL (keeps the in-memory store bounded)."""
    now = time.time()
    stale = [
        jid for jid, j in _research_jobs.items()
        if j.get("status") in ("done", "failed")
        and now - j.get("ended_ts", now) > RESEARCH_JOB_TTL
    ]
    for jid in stale:
        _research_jobs.pop(jid, None)


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class QAResponse(BaseModel):
    answer: str
    question: str


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    max_subtopics: int = Field(default=4, ge=1, le=6)
    searches_per_topic: int = Field(default=2, ge=1, le=4)


class TriggerRequest(BaseModel):
    limit: Optional[int] = None
    run_twitter: bool = True
    digest_date: Optional[str] = None
    window_days: int = 1
    publish: bool = False


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hh-research-agent"}


@app.post("/qa", response_model=QAResponse)
async def qa(body: QARequest):
    try:
        answer = await ask_data_agent(body.question)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return QAResponse(question=body.question, answer=answer or "(no answer)")


@app.post("/research/start")
async def research_start(body: ResearchRequest, background: BackgroundTasks):
    """Kick off a deep-research run; returns a job_id to poll for progress."""
    _prune_research_jobs()

    # Backpressure: cap total in-flight (running + queued) jobs.
    active = sum(1 for j in _research_jobs.values() if j.get("status") == "running")
    if active >= RESEARCH_MAX_PENDING:
        raise HTTPException(
            status_code=429,
            detail="深度研究当前排队已满，请稍后再试 (too many concurrent research jobs)",
        )

    job_id = f"research-{uuid.uuid4().hex}"
    queued = active >= RESEARCH_MAX_CONCURRENT
    _research_jobs[job_id] = {
        "status": "running",
        "phase": "queued",
        "message": "排队中，等待空闲资源…" if queued else "排队中…",
        "pct": 0, "question": body.question, "result": None, "error": None,
        "created_ts": time.time(), "ended_ts": None,
    }

    def on_progress(phase: str, message: str, pct: int) -> None:
        job = _research_jobs.get(job_id)
        if job is not None:
            job.update(phase=phase, message=message, pct=pct)

    async def _job():
        try:
            # Wait for a concurrency slot; the job shows "排队中" until acquired.
            async with _research_sem:
                job = _research_jobs.get(job_id)
                if job is None:
                    return  # pruned/cancelled while queued
                job.update(phase="brief", message="开始研究…")
                result = await run_deep_research(
                    body.question,
                    on_progress=on_progress,
                    max_subtopics=body.max_subtopics,
                    searches_per_topic=body.searches_per_topic,
                )
            job = _research_jobs.get(job_id, {})
            job.update(status="done", phase="done", message="研究完成", pct=100,
                       result=result, ended_ts=time.time())
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            job = _research_jobs.get(job_id, {})
            job.update(status="failed", error=str(exc), message=f"失败: {exc}",
                       ended_ts=time.time())

    background.add_task(_job)
    return {"job_id": job_id, "status": "running"}


@app.get("/research/status/{job_id}")
async def research_status(job_id: str):
    job = _research_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="research job not found")
    return job


async def _run_stage(stage: str, params: TriggerRequest) -> dict:
    if stage == "pipeline":
        return await run_pipeline(
            run_twitter=params.run_twitter,
            limit=params.limit,
            analysis_limit=params.limit or 20,
            entity_limit=params.limit or 20,
            alert_limit=params.limit or 30,
        )
    if stage == "ingest":
        return await run_ingestion(run_twitter=params.run_twitter, limit=params.limit)
    if stage == "analyze":
        return await run_analysis(limit=params.limit or 20)
    if stage == "entity":
        return await run_entity_extraction(limit=params.limit or 20)
    if stage == "alert":
        return await run_alerts(limit=params.limit or 30)
    if stage == "digest":
        return await run_digest(
            digest_date=params.digest_date,
            window_days=params.window_days,
            publish=params.publish,
        )
    raise ValueError(f"unknown stage: {stage}")


@app.post("/trigger/{stage}")
async def trigger(stage: str, background: BackgroundTasks, body: TriggerRequest = TriggerRequest()):
    valid = {"pipeline", "ingest", "analyze", "entity", "alert", "digest"}
    if stage not in valid:
        raise HTTPException(status_code=404, detail=f"Unknown stage. Valid: {sorted(valid)}")

    job_id = f"{stage}-{asyncio.get_event_loop().time():.0f}"
    _jobs[job_id] = {"stage": stage, "status": "running"}

    async def _job():
        try:
            result = await _run_stage(stage, body)
            _jobs[job_id] = {"stage": stage, "status": "done", "result": {
                k: v for k, v in result.items() if k in ("run_meta", "errors", "alerts")
            }}
        except Exception as exc:
            _jobs[job_id] = {"stage": stage, "status": "failed", "error": str(exc)}

    if background is not None:
        background.add_task(_job)
        return {"job_id": job_id, "status": "accepted", "stage": stage}

    result = await _run_stage(stage, body)
    _jobs[job_id] = {"stage": stage, "status": "done", "result": result}
    return {"job_id": job_id, "status": "done", "stage": stage, "result": result}


@app.get("/jobs/{job_id}")
async def job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


def main():
    import uvicorn
    uvicorn.run("agent.service:app", host="0.0.0.0", port=9000, reload=False)


if __name__ == "__main__":
    main()
