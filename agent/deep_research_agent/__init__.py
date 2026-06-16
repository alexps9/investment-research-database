"""Deep-research agent — open_deep_research-style pipeline over the LiteLLM gateway.

Public API:
    run_deep_research(question, on_progress=..., max_subtopics=..., searches_per_topic=...)
        → {question, brief, subtopics, report, sources}
"""
from __future__ import annotations

from .researcher import run_deep_research

__all__ = ["run_deep_research"]
