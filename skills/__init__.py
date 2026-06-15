"""Composed skills (workflows) built on top of atomic ``tools``.

Skills vs tools:
    - ``tools`` are atomic, 1:1 with a backend endpoint (e.g. ``list_sources``).
    - ``skills`` orchestrate several tools into a useful workflow that returns a
      human-readable result (e.g. ``audit_source_quality``, ``daily_brief``).

Expose them to an agent via ``SKILLS``.
"""
from skills.data_quality import audit_source_quality, find_duplicate_signals
from skills.reporting import answer_with_sources, daily_brief, funding_landscape_summary

SKILLS = [
    audit_source_quality,
    find_duplicate_signals,
    daily_brief,
    funding_landscape_summary,
    answer_with_sources,
]

__all__ = [
    "SKILLS",
    "audit_source_quality",
    "find_duplicate_signals",
    "daily_brief",
    "funding_landscape_summary",
    "answer_with_sources",
]
