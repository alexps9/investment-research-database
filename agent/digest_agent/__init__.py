"""Digest agent — HH Research Daily brief writer (LangGraph)."""
from __future__ import annotations

from agent.digest_agent.node import build_digest_payload, digest_node, run_digest
from agent.digest_agent.prompts import DIGEST_AGENT_SYSTEM_MESSAGE, TRACKS


def format_payload_for_agent(payload: dict, digest_date: str, publish: bool = False) -> str:
    from agent.digest_agent.node import _format_payload_text
    return _format_payload_text(payload, digest_date, publish)


__all__ = [
    "digest_node",
    "run_digest",
    "build_digest_payload",
    "DIGEST_AGENT_SYSTEM_MESSAGE",
    "TRACKS",
    "format_payload_for_agent",
]
