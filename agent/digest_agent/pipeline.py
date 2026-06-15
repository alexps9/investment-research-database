"""Digest pipeline — AutoGen refactor of the original ``hh_research.pipeline.daily``.

Flow:
    fetch the day's KB signals + funding   -> tools.signals / tools.funding   [deterministic]
    bucket into the four payload arrays      -> this module                     [deterministic]
    rank headline candidates                 -> skills.headline_selection       [deterministic]
    curate + write the Feishu-XML brief       -> digest_agent (AutoGen)          [LLM-driven]
    (optional) publish                        -> tools.notify.send_feishu        [via agent]

The deterministic bucketing/ranking stays cheap + reproducible; only the curation
and writing is delegated to the AutoGen ``digest_agent``. The brief is written to
``data/digests/HH-Research-Daily-{date}.xml``.

Run from the repo root:

    python -m agent.digest_agent.pipeline                 # today (UTC), no push
    python -m agent.digest_agent.pipeline --date 2026-06-15
    python -m agent.digest_agent.pipeline --window-days 1 --publish

Env (repo .env / agent/.env / agent/digest_agent/.env):
    LLM_API_KEY / DEEPSEEK_API_KEY   chat model key (required)
    KB_API_BASE_URL                  backend URL (default http://localhost:8000)
    FEISHU_WEBHOOK_URL               push target (only used with --publish)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
    load_dotenv(_REPO_ROOT / "agent" / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

from autogen_agentchat.ui import Console  # noqa: E402

from agent.config import get_model_client  # noqa: E402
from agent.digest_agent import build_digest_agent, format_payload_for_agent  # noqa: E402
from skills.headline_selection import select_headlines  # noqa: E402
from tools.funding import list_funding  # noqa: E402
from tools.signals import list_signals  # noqa: E402

# Shared whitelist so the headline classifier recognises P0+/P0 entities.
_WHITELIST_PATH = _REPO_ROOT / "agent" / "alert_agent" / "config" / "p0_whitelist.yml"

_PAPER_TYPES = {"paper", "tech_report"}
_INDUSTRY_TYPES = {
    "news", "model_release", "blog", "github_release", "benchmark", "tweet",
    "dataset", "other",
}
_FRONTIER_TRACKS = {"基础模型", "世界模型", "AI infra", "AI4S"}

DIGEST_DIR = _REPO_ROOT / "data" / "digests"


def _within_window(ts: str | None, since: datetime) -> bool:
    if not ts:
        return True  # undated → keep (let the writer judge)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= since
    except Exception:
        return True


async def build_payload(digest_date: str, window_days: int, max_pull: int = 300) -> dict:
    """Pull the day's KB signals + funding and bucket them into the four arrays."""
    since = datetime.fromisoformat(digest_date).replace(tzinfo=timezone.utc) - timedelta(
        days=window_days - 1
    )

    signals = await list_signals(limit=max_pull) or []
    if isinstance(signals, dict):  # some backends wrap in {"items": [...]}
        signals = signals.get("items", [])
    recent = [s for s in signals if _within_window(
        s.get("published_at") or s.get("created_at"), since)]

    papers = [s for s in recent if (s.get("signal_type") in _PAPER_TYPES)]
    industry = [s for s in recent if (s.get("signal_type") in _INDUSTRY_TYPES)]

    funding = await list_funding(limit=50) or []
    if isinstance(funding, dict):
        funding = funding.get("items", [])
    capital = [f for f in funding if _within_window(
        f.get("announced_at") or f.get("created_at"), since)][:8]

    # Deterministic headline ranking across all (non-funding) signals.
    ranked = select_headlines(
        papers + industry,
        whitelist_path=str(_WHITELIST_PATH) if _WHITELIST_PATH.exists() else None,
        max_auto=3,
    )
    headline_candidates = (ranked["auto_headlines"] + ranked["edge_cases"])[:5]
    if not headline_candidates:  # classifier found nothing strong → fall back to newest
        headline_candidates = (papers + industry)[:5]

    print(f"  payload: {len(headline_candidates)} headline candidates, {len(capital)} capital, "
          f"{len(papers)} frontier, {len(industry)} industry "
          f"(auto={ranked['counts']['auto']}, edge={ranked['counts']['edge']})")

    return {
        "headline_candidates": headline_candidates,
        "capital": capital,
        "frontier": papers,
        "industry": industry,
    }


async def run(date: str | None, window_days: int, publish: bool) -> None:
    digest_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Digest pipeline start ({digest_date})")

    payload = await build_payload(digest_date, window_days)
    if not any(payload[k] for k in ("headline_candidates", "capital", "frontier", "industry")):
        print("  No signals in window, done.")
        return

    task = format_payload_for_agent(payload, digest_date, publish=publish)

    model_client = get_model_client()
    result_text = ""
    try:
        agent = build_digest_agent(model_client)
        result = await Console(agent.run_stream(task=task))
        for msg in reversed(getattr(result, "messages", [])):
            content = getattr(msg, "content", "")
            if isinstance(content, str) and "<title>" in content:
                result_text = content
                break
    finally:
        await model_client.close()

    if result_text:
        xml = result_text.replace("TERMINATE", "").strip()
        DIGEST_DIR.mkdir(parents=True, exist_ok=True)
        out = DIGEST_DIR / f"HH-Research-Daily-{digest_date}.xml"
        out.write_text(xml, encoding="utf-8")
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Wrote {out}")
    else:
        print("\n  [WARN] agent did not return an XML brief; nothing written.")


def main() -> None:
    parser = argparse.ArgumentParser(description="HH-Research daily digest pipeline (AutoGen).")
    parser.add_argument("--date", default=None, help="digest date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--window-days", type=int, default=1,
                        help="how many days of signals to include (default 1)")
    parser.add_argument("--publish", action="store_true",
                        help="also push the brief to Feishu via send_feishu")
    args = parser.parse_args()
    asyncio.run(run(date=args.date, window_days=args.window_days, publish=args.publish))


if __name__ == "__main__":
    main()
