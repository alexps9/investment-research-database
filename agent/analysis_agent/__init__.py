"""Analysis agent — convert collected signals into structured intelligence."""
from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field

from agent.llm import structured_llm
from tools.signals import add_signal_analysis, list_signals, set_signal_status


class SignalAnalysisResult(BaseModel):
    tldr: str = Field(description="One-line TL;DR in Chinese for investors")
    summary: str = Field(description="2-4 sentence summary in Chinese")
    why_it_matters: str = Field(description="Why this matters for AI investment research")
    technical_points: list[str] = Field(default_factory=list)
    limitations: Optional[str] = None
    topic_tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list, description="Named entities mentioned")
    importance_score: float = Field(description="0-1 importance")
    novelty_score: float = Field(description="0-1 novelty")
    relevance_score: float = Field(description="0-1 relevance")
    confidence_score: float = Field(description="0-1 confidence")
    reading_priority: str = Field(description="high | medium | low")


ANALYSIS_PROMPT = """\
你是 HH-Research 的**信号理解 Agent**。将一条原始信号转化为结构化情报，供投研团队使用。

要求：
- 用中文输出 tldr / summary / why_it_matters
- importance/novelty/relevance/confidence 均为 0-1 浮点数
- topic_tags 用英文或中文短标签
- entities 列出文中出现的公司/人物/模型/方法名
- reading_priority 只能是 high / medium / low

信号标题：{title}
类型：{signal_type}
链接：{url}
摘要/正文：
{body}
"""


async def analyze_one_signal(signal: dict) -> dict:
    """Run LLM analysis and persist to KB."""
    signal_id = signal.get("id")
    if not signal_id:
        return {"error": "missing_signal_id", "signal": signal}

    body = signal.get("abstract") or signal.get("content") or signal.get("title", "")
    llm = structured_llm(SignalAnalysisResult, temperature=0.1)
    prompt = ANALYSIS_PROMPT.format(
        title=signal.get("title", ""),
        signal_type=signal.get("signal_type", "other"),
        url=signal.get("url", ""),
        body=body[:4000],
    )
    try:
        result: SignalAnalysisResult = await llm.ainvoke(prompt)
    except Exception as exc:
        return {"error": f"llm_failed: {exc}", "signal_id": signal_id}

    model_name = os.getenv("LLM_MODEL", "deepseek-chat")
    stored = await add_signal_analysis(
        signal_id,
        tldr=result.tldr,
        summary=result.summary,
        why_it_matters=result.why_it_matters,
        technical_points=result.technical_points,
        limitations=result.limitations,
        topic_tags=result.topic_tags,
        entities=result.entities,
        importance_score=result.importance_score,
        novelty_score=result.novelty_score,
        relevance_score=result.relevance_score,
        confidence_score=result.confidence_score,
        reading_priority=result.reading_priority,
        model_name=model_name,
        prompt_version="langgraph-v1",
    )
    if isinstance(stored, dict) and stored.get("error"):
        return {"error": stored, "signal_id": signal_id}

    await set_signal_status(signal_id, "processed")
    return {
        "signal_id": signal_id,
        "analysis": result.model_dump(),
        "stored": stored,
    }


async def run_analysis(*, limit: int = 20) -> dict:
    """Analyze up to ``limit`` collected signals."""
    raw = await list_signals(status="collected", limit=limit)
    if isinstance(raw, dict):
        signals = raw.get("items", [])
    else:
        signals = raw or []

    analyses: list[dict] = []
    errors: list[str] = []
    for sig in signals:
        outcome = await analyze_one_signal(sig)
        if outcome.get("error"):
            errors.append(str(outcome))
        else:
            analyses.append(outcome)

    print(f"  Analysis: processed {len(analyses)} signals ({len(errors)} errors)")
    return {
        "signals": signals,
        "analyses": analyses,
        "errors": errors,
        "run_meta": {"analyzed": len(analyses)},
    }


async def analysis_node(state: dict) -> dict:
    """LangGraph node: analyze collected signals or pass-through from ingestion."""
    run_meta = state.get("run_meta") or {}
    limit = run_meta.get("analysis_limit", 20)

    # Prefer freshly ingested signals; fall back to querying collected.
    if state.get("signals"):
        analyses: list[dict] = []
        errors: list[str] = []
        for sig in state["signals"]:
            if sig.get("status") and sig.get("status") != "collected":
                continue
            outcome = await analyze_one_signal(sig)
            if outcome.get("error"):
                errors.append(str(outcome))
            else:
                analyses.append(outcome)
        return {"analyses": analyses, "errors": errors, "run_meta": {"analyzed": len(analyses)}}

    return await run_analysis(limit=limit)
