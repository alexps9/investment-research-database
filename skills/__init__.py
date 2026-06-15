"""Composed skills (workflows) built on top of atomic ``tools``.

Each skill lives in its own directory named after its function:
    skills/source_quality_audit   audit_source_quality
    skills/duplicate_signals      find_duplicate_signals
    skills/daily_brief            daily_brief
    skills/funding_summary        funding_landscape_summary
    skills/rag_answer             answer_with_sources
    skills/signal_triage          triage_signals (score/triangulate/dedup)

Skills vs tools:
    - ``tools`` are atomic, 1:1 with a backend endpoint (e.g. ``list_sources``).
    - ``skills`` orchestrate several tools into a useful workflow that returns a
      human-readable result.

Expose them to an agent via ``SKILLS``.
"""
from skills.source_quality_audit import audit_source_quality
from skills.duplicate_signals import find_duplicate_signals
from skills.daily_brief import daily_brief
from skills.funding_summary import funding_landscape_summary
from skills.rag_answer import answer_with_sources
from skills.signal_triage import triage_signals

SKILLS = [
    audit_source_quality,
    find_duplicate_signals,
    daily_brief,
    funding_landscape_summary,
    answer_with_sources,
    triage_signals,
]

__all__ = [
    "SKILLS",
    "audit_source_quality",
    "find_duplicate_signals",
    "daily_brief",
    "funding_landscape_summary",
    "answer_with_sources",
    "triage_signals",
]
