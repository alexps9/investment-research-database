"""Alert agent — real-time AI-industry signal triage & Feishu push (LangGraph).

Infrastructure (fetcher, prefilter, store) lives in this package.
The LangGraph node is in ``node.py``; legacy AutoGen factory removed.
"""
from __future__ import annotations

from agent.alert_agent.node import alert_node, evaluate_and_push, run_alerts

EVENT_TYPE_MAP = {
    "模型/产品发布": "model_release",
    "技术研究突破": "paper",
    "硬件/Infra突破": "news",
    "大佬评论/观点": "tweet",
    "评测/榜单": "benchmark",
    "Demo/演示": "other",
    "公司间商业动作": "news",
    "顶级人员变动": "news",
}


def format_signal_for_agent(signal: dict) -> str:
    """Render an analyzed signal for LLM judgement."""
    analysis = signal.get("analysis") or {}
    return (
        f"标题：{signal.get('title', '')}\n"
        f"TLDR：{analysis.get('tldr', '')}\n"
        f"重要性：{analysis.get('importance_score', 0)}\n"
        f"链接：{signal.get('url', '')}\n"
        f"正文：{(signal.get('abstract') or '')[:1500]}"
    )


__all__ = [
    "alert_node",
    "run_alerts",
    "evaluate_and_push",
    "format_signal_for_agent",
    "EVENT_TYPE_MAP",
]
