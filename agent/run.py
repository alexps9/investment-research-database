"""CLI entry for LangGraph pipelines (cron-friendly).

Usage:
    python -m agent.run pipeline          # full intelligence graph
    python -m agent.run ingest
    python -m agent.run analyze
    python -m agent.run entity
    python -m agent.run alert
    python -m agent.run digest [--date YYYY-MM-DD] [--publish]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
    load_dotenv(_REPO_ROOT / "agent" / ".env")
except Exception:
    pass

from agent.analysis_agent import run_analysis
from agent.alert_agent.node import run_alerts
from agent.digest_agent.node import run_digest
from agent.entity_agent import run_entity_extraction
from agent.graph import get_digest_graph, get_intelligence_graph
from agent.ingestion_agent import run_ingestion
from agent.state import empty_state


async def run_pipeline(**run_meta) -> dict:
    graph = get_intelligence_graph()
    state = empty_state(run_meta=run_meta)
    result = await graph.ainvoke(state)
    return result


async def main_async(args: argparse.Namespace) -> None:
    if args.command == "pipeline":
        result = await run_pipeline(
            run_twitter=not args.no_twitter,
            limit=args.limit,
            analysis_limit=args.limit or 20,
            entity_limit=args.limit or 20,
            alert_limit=args.limit or 30,
        )
        print(f"Pipeline done: {result.get('run_meta', {})}")
    elif args.command == "ingest":
        result = await run_ingestion(run_twitter=not args.no_twitter, limit=args.limit)
        print(f"Ingestion done: {result.get('run_meta', {})}")
    elif args.command == "analyze":
        result = await run_analysis(limit=args.limit or 20)
        print(f"Analysis done: {result.get('run_meta', {})}")
    elif args.command == "entity":
        result = await run_entity_extraction(limit=args.limit or 20)
        print(f"Entity done: {result.get('run_meta', {})}")
    elif args.command == "alert":
        result = await run_alerts(limit=args.limit or 30)
        print(f"Alert done: {result.get('run_meta', {})}")
    elif args.command == "digest":
        if args.use_graph:
            graph = get_digest_graph()
            state = empty_state(run_meta={
                "digest_date": args.date,
                "window_days": args.window_days,
                "publish": args.publish,
            })
            result = await graph.ainvoke(state)
        else:
            result = await run_digest(
                digest_date=args.date,
                window_days=args.window_days,
                publish=args.publish,
            )
        print(f"Digest done: {result.get('run_meta', {})}")
    else:
        raise SystemExit(f"Unknown command: {args.command}")


def main() -> None:
    parser = argparse.ArgumentParser(description="HH-Research LangGraph pipelines")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pipe = sub.add_parser("pipeline", help="run full intelligence graph")
    p_pipe.add_argument("--limit", type=int, default=None)
    p_pipe.add_argument("--no-twitter", action="store_true")

    for name in ("ingest", "analyze", "entity", "alert"):
        p = sub.add_parser(name)
        p.add_argument("--limit", type=int, default=None)
        if name == "ingest":
            p.add_argument("--no-twitter", action="store_true")

    p_digest = sub.add_parser("digest")
    p_digest.add_argument("--date", default=None)
    p_digest.add_argument("--window-days", type=int, default=1)
    p_digest.add_argument("--publish", action="store_true")
    p_digest.add_argument("--use-graph", action="store_true")

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
