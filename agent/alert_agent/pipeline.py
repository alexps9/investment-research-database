"""Alert pipeline — LangGraph-backed (delegates to agent.run).

Run from repo root:
    python -m agent.alert_agent.pipeline [--limit N] [--no-twitter]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
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

from agent.alert_agent.node import run_alerts  # noqa: E402
from agent.run import run_pipeline  # noqa: E402


async def run(limit: int | None = None, run_twitter: bool = True, full_pipeline: bool = False) -> None:
    if full_pipeline:
        await run_pipeline(run_twitter=run_twitter, limit=limit, alert_limit=limit or 30)
    else:
        await run_alerts(limit=limit or 30)


def main() -> None:
    parser = argparse.ArgumentParser(description="HH-Research alert pipeline (LangGraph).")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-twitter", action="store_true")
    parser.add_argument("--full-pipeline", action="store_true", help="run ingest→analyze→entity→alert")
    args = parser.parse_args()
    asyncio.run(run(limit=args.limit, run_twitter=not args.no_twitter, full_pipeline=args.full_pipeline))


if __name__ == "__main__":
    main()
