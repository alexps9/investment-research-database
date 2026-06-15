"""FastAPI service — Data Agent Q&A + manual pipeline triggers."""
from __future__ import annotations

import asyncio
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

app = FastAPI(title="HH-Research Agent Service", version="2.0.0")

# Track background job status (in-memory; sufficient for single-container deploy)
_jobs: dict[str, dict[str, Any]] = {}


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class QAResponse(BaseModel):
    answer: str
    question: str


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
