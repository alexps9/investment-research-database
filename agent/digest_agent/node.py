"""Digest agent — LangGraph node for daily brief generation and Feishu push."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.digest_agent.prompts import DIGEST_AGENT_SYSTEM_MESSAGE, TRACKS
from agent.llm import get_chat_model
from skills.headline_selection import select_headlines
from tools.funding import list_funding
from tools.notify import send_feishu
from tools.signals import list_signals

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WHITELIST_PATH = _REPO_ROOT / "agent" / "alert_agent" / "config" / "p0_whitelist.yml"
DIGEST_DIR = _REPO_ROOT / "data" / "digests"

_PAPER_TYPES = {"paper", "tech_report"}
_INDUSTRY_TYPES = {
    "news", "model_release", "blog", "github_release", "benchmark", "tweet",
    "dataset", "other",
}


def _within_window(ts: str | None, since: datetime) -> bool:
    if not ts:
        return True
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= since
    except Exception:
        return True


def _importance(sig: dict) -> float:
    analysis = sig.get("analysis") or {}
    return float(analysis.get("importance_score") or 0)


async def build_digest_payload(digest_date: str, window_days: int = 1, max_pull: int = 300) -> dict:
    """Pull analyzed signals + funding and bucket into four arrays."""
    since = datetime.fromisoformat(digest_date).replace(tzinfo=timezone.utc) - timedelta(days=window_days - 1)

    raw = await list_signals(status="processed", limit=max_pull)
    if isinstance(raw, dict):
        signals = raw.get("items", [])
    else:
        signals = raw or []

    # Prefer signals with analysis; sort by importance
    recent = [
        s for s in signals
        if _within_window(s.get("published_at") or s.get("created_at"), since) and s.get("analysis")
    ]
    recent.sort(key=_importance, reverse=True)

    papers = [s for s in recent if s.get("signal_type") in _PAPER_TYPES]
    industry = [s for s in recent if s.get("signal_type") in _INDUSTRY_TYPES]

    funding = await list_funding(limit=50) or []
    if isinstance(funding, dict):
        funding = funding.get("items", [])
    capital = [f for f in funding if _within_window(f.get("announced_at") or f.get("created_at"), since)][:8]

    ranked = select_headlines(
        papers + industry,
        whitelist_path=str(_WHITELIST_PATH) if _WHITELIST_PATH.exists() else None,
        max_auto=3,
    )
    headline_candidates = (ranked["auto_headlines"] + ranked["edge_cases"])[:5]
    if not headline_candidates:
        headline_candidates = (papers + industry)[:5]

    return {
        "headline_candidates": headline_candidates,
        "capital": capital,
        "frontier": papers[:20],
        "industry": industry[:30],
        "ranked_counts": ranked.get("counts", {}),
    }


def _format_payload_text(payload: dict, digest_date: str, publish: bool) -> str:
    def _sig_line(s: dict) -> str:
        a = s.get("analysis") or {}
        return f"- [{s.get('signal_type', '?')}] {a.get('tldr') or s.get('title', '')} ({s.get('url', '')})"

    sections = [
        f"日期：{digest_date}",
        f"赛道：{', '.join(TRACKS)}",
        "\n## 头条候选",
        *[_sig_line(s) for s in payload.get("headline_candidates", [])],
        "\n## 资本动态",
        *[f"- {f.get('company_name', '?')} {f.get('round', '')} {f.get('amount_raw', '')}" for f in payload.get("capital", [])],
        "\n## 前沿研究",
        *[_sig_line(s) for s in payload.get("frontier", [])[:10]],
        "\n## 产业动态",
        *[_sig_line(s) for s in payload.get("industry", [])[:10]],
    ]
    if publish:
        sections.append("\n完成后请调用 send_feishu 推送 XML 简报。")
    sections.append("\n请按系统提示输出 Feishu-XML 格式的 HH-Research Daily 简报。")
    return "\n".join(sections)


async def run_digest(
    *,
    digest_date: str | None = None,
    window_days: int = 1,
    publish: bool = False,
) -> dict:
    """Generate daily digest XML and optionally push to Feishu."""
    date = digest_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = await build_digest_payload(date, window_days)
    if not any(payload.get(k) for k in ("headline_candidates", "capital", "frontier", "industry")):
        return {"digest_xml": None, "errors": ["no_signals_in_window"]}

    llm = get_chat_model(temperature=0.3, max_tokens=8192)
    prompt = f"{DIGEST_AGENT_SYSTEM_MESSAGE}\n\n---\n\n{_format_payload_text(payload, date, publish)}"
    try:
        response = await llm.ainvoke(prompt)
        xml = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        return {"errors": [f"llm_failed: {exc}"]}

    xml = xml.replace("TERMINATE", "").strip()
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    out = DIGEST_DIR / f"HH-Research-Daily-{date}.xml"
    out.write_text(xml, encoding="utf-8")
    print(f"  Digest: wrote {out}")

    push_result = None
    if publish and xml:
        push_result = await send_feishu(xml[:4000])

    return {
        "digest_payload": payload,
        "digest_xml": xml,
        "run_meta": {"digest_date": date, "published": bool(publish and push_result)},
        "alerts": [{"type": "digest_push", "result": push_result}] if push_result else [],
    }


async def digest_node(state: dict) -> dict:
    """LangGraph node wrapper."""
    run_meta = state.get("run_meta") or {}
    return await run_digest(
        digest_date=run_meta.get("digest_date"),
        window_days=run_meta.get("window_days", 1),
        publish=run_meta.get("publish", False),
    )
