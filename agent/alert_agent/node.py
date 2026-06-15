"""Alert agent — LangGraph node for pushing important analyzed signals to Feishu."""
from __future__ import annotations

from pydantic import BaseModel, Field

from agent.alert_agent.prefilter import prefilter
from agent.alert_agent.store import Store
from agent.llm import structured_llm
from tools.notify import send_feishu
from tools.signals import list_signals

ALERT_JUDGE_PROMPT = """\
你是 HH-Research 实时告警 Agent。判断以下**已分析信号**是否值得立即推送给投资人。

推送标准：属于模型发布/技术突破/硬件Infra/大佬观点/评测榜单/Demo/商业动作/人员变动，
且 importance_score >= 0.6 或 reading_priority=high 的事件。

信号：
标题：{title}
TLDR：{tldr}
重要性：{importance}
新颖性：{novelty}
阅读优先级：{priority}
为什么重要：{why}
链接：{url}
"""


class AlertDecision(BaseModel):
    should_alert: bool
    alert_level: str = Field(description="important | medium | skip")
    summary: str = Field(description="20-40字中文推送摘要")
    reason: str = ""


def _format_feishu_message(decision: AlertDecision, signal: dict) -> str:
    prefix = "⚠️" if decision.alert_level == "important" else "🔔"
    lines = [f"{prefix} {decision.summary}", f"🔗 {signal.get('url', '')}"]
    analysis = signal.get("analysis") or {}
    if analysis.get("why_it_matters"):
        lines.append(f"💡 {analysis['why_it_matters'][:120]}")
    return "\n".join(lines)


async def evaluate_and_push(signal: dict, store: Store | None = None) -> dict:
    """Judge one analyzed signal and optionally push to Feishu."""
    signal_id = signal.get("id", "")
    tweet_id = signal.get("external_id") or signal.get("raw_metadata", {}).get("tweet_id") or signal_id

    if store and store.is_sent(str(tweet_id)):
        return {"signal_id": signal_id, "skipped": True, "reason": "already_sent"}

    analysis = signal.get("analysis") or {}
    importance = float(analysis.get("importance_score") or 0)
    priority = (analysis.get("reading_priority") or "").lower()

    # Fast path: low importance without LLM
    if importance < 0.4 and priority not in ("high",):
        return {"signal_id": signal_id, "skipped": True, "reason": "low_importance"}

    llm = structured_llm(AlertDecision, temperature=0.1)
    prompt = ALERT_JUDGE_PROMPT.format(
        title=signal.get("title", ""),
        tldr=analysis.get("tldr", ""),
        importance=importance,
        novelty=analysis.get("novelty_score", 0),
        priority=priority or "unknown",
        why=analysis.get("why_it_matters", ""),
        url=signal.get("url", ""),
    )
    try:
        decision: AlertDecision = await llm.ainvoke(prompt)
    except Exception as exc:
        return {"signal_id": signal_id, "error": f"llm_failed: {exc}"}

    if not decision.should_alert or decision.alert_level == "skip":
        if store:
            store.mark_sent(str(tweet_id), "", "", decision.alert_level, "", decision.summary[:200])
        return {"signal_id": signal_id, "skipped": True, "reason": decision.reason}

    message = _format_feishu_message(decision, signal)
    push = await send_feishu(message)
    if store:
        store.mark_sent(str(tweet_id), "", "", decision.alert_level, message, decision.summary[:200])

    return {
        "signal_id": signal_id,
        "alert_level": decision.alert_level,
        "summary": decision.summary,
        "push": push,
    }


async def run_alerts(*, limit: int = 30) -> dict:
    """Evaluate recently processed signals for alerting."""
    raw = await list_signals(status="processed", limit=limit)
    if isinstance(raw, dict):
        signals = raw.get("items", [])
    else:
        signals = raw or []

    store = Store()
    alerts: list[dict] = []
    errors: list[str] = []
    try:
        for sig in signals:
            if not sig.get("analysis"):
                continue
            # Optional prefilter on raw metadata if present
            meta = sig.get("raw_metadata") or {}
            if meta:
                try:
                    pf = prefilter({**meta, "text": sig.get("abstract", sig.get("title", ""))})
                    if pf.get("action") == "skip":
                        continue
                except Exception:
                    pass
            outcome = await evaluate_and_push(sig, store)
            if outcome.get("error"):
                errors.append(str(outcome))
            elif not outcome.get("skipped"):
                alerts.append(outcome)
    finally:
        store.close()

    print(f"  Alert: pushed {len(alerts)} alerts ({len(errors)} errors)")
    return {"alerts": alerts, "errors": errors, "run_meta": {"alerts_sent": len(alerts)}}


async def alert_node(state: dict) -> dict:
    """LangGraph node: alert on analyzed signals from current run or KB."""
    run_meta = state.get("run_meta") or {}
    limit = run_meta.get("alert_limit", 30)

    analyses = state.get("analyses") or []
    if analyses:
        store = Store()
        alerts: list[dict] = []
        errors: list[str] = []
        try:
            for item in analyses:
                sid = item.get("signal_id")
                if not sid:
                    continue
                from tools.signals import get_signal
                sig = await get_signal(sid)
                if isinstance(sig, dict) and sig.get("error"):
                    errors.append(str(sig))
                    continue
                sig["analysis"] = item.get("analysis") or sig.get("analysis")
                outcome = await evaluate_and_push(sig, store)
                if outcome.get("error"):
                    errors.append(str(outcome))
                elif not outcome.get("skipped"):
                    alerts.append(outcome)
        finally:
            store.close()
        return {"alerts": alerts, "errors": errors, "run_meta": {"alerts_sent": len(alerts)}}

    return await run_alerts(limit=limit)
