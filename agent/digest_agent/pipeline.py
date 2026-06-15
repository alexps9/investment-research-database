"""Digest pipeline — LangGraph-backed daily brief.

Run from repo root:
    python -m agent.digest_agent.pipeline [--date YYYY-MM-DD] [--publish]
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

from agent.digest_agent.node import run_digest  # noqa: E402


async def run(date: str | None, window_days: int, publish: bool) -> None:
    result = await run_digest(digest_date=date, window_days=window_days, publish=publish)
    if result.get("errors"):
        print(f"  Errors: {result['errors']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="HH-Research daily digest (LangGraph).")
    parser.add_argument("--date", default=None)
    parser.add_argument("--window-days", type=int, default=1)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.date, args.window_days, args.publish))


if __name__ == "__main__":
    main()
