"""CLI entrypoint for the HH-Research multi-agent system.

Run from the repo root:

    python -m agent.main "Audit source data quality and list the worst offenders"

or interactively (no task argument):

    python -m agent.main

Requires (env or .env at repo root):
    LLM_API_KEY / DEEPSEEK_API_KEY   chat model key
    KB_API_BASE_URL                  backend URL (default http://localhost:8000)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow `python agent/main.py` (not just `-m agent.main`) by putting repo root on path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
    load_dotenv(_REPO_ROOT / "agent" / ".env")
except Exception:
    pass

from autogen_agentchat.ui import Console  # noqa: E402

from agent.config import get_model_client  # noqa: E402
from agent.team import build_team  # noqa: E402


async def run_once(task: str) -> None:
    model_client = get_model_client()
    team = build_team(model_client)
    try:
        await Console(team.run_stream(task=task))
    finally:
        await model_client.close()


async def interactive() -> None:
    model_client = get_model_client()
    team = build_team(model_client)
    print("HH-Research agent. Type a task ('exit' to quit).")
    try:
        while True:
            task = input("\n> ").strip()
            if task.lower() in {"exit", "quit"}:
                break
            if not task:
                continue
            await Console(team.run_stream(task=task))
            await team.reset()
    finally:
        await model_client.close()


def main() -> None:
    if not (os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
        print("ERROR: set LLM_API_KEY (or DEEPSEEK_API_KEY) first.", file=sys.stderr)
        sys.exit(1)
    task = " ".join(sys.argv[1:]).strip()
    asyncio.run(run_once(task) if task else interactive())


if __name__ == "__main__":
    main()
