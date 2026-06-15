"""CLI entry — delegates to LangGraph pipelines.

Legacy AutoGen chat is replaced by:
    python -m agent.run pipeline
    curl -X POST http://localhost:9000/qa -d '{"question":"..."}'
"""
from __future__ import annotations

import sys

from agent.run import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in (
        "pipeline", "ingest", "analyze", "entity", "alert", "digest",
    ):
        print(
            "AutoGen chat mode is deprecated. Use:\n"
            "  python -m agent.run pipeline\n"
            "  python -m agent.service  (HTTP Q&A on :9000)\n"
            f"Unknown command: {sys.argv[1]}"
        )
        sys.exit(1)
    main()
