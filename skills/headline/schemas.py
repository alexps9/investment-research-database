"""Standalone ``Signal`` DTO for the vendored headline classifier.

A dependency-free trim of the upstream HH-Research ``hh_research.storage.schemas``
pydantic model — only the fields the ``HeadlineClassifier`` reads/writes (plus the
constructor fields the alert prefilter supplies). This keeps the vendored prefilter
self-contained (no pydantic, no upstream package on PYTHONPATH).

Upstream: jingruzhao103-bit/HH-Research → daily-digest/src/hh_research/storage/schemas.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Signal:
    """One collected signal (tweet / RSS post / arxiv paper / ...)."""

    # ── Source / identity (set by the collector / alert prefilter) ──────────
    source: str = "other"           # x | arxiv | openalex | rss | other
    source_id: str = ""             # globally unique, e.g. "x:<tweet_id>"
    author_name: str = ""           # matched against the whitelist
    url: str = ""
    raw_text: str = ""
    lang: str = "en"
    created_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None

    # ── LLM-extracted fields (empty for raw alert signals) ──────────────────
    summary_zh: Optional[str] = None
    cognitive_takeaway_zh: Optional[str] = None
    result_summary_zh: Optional[str] = None
    core_findings_zh: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)

    # ── v8.0 classifier outputs (filled by HeadlineClassifier) ──────────────
    event_type: Optional[str] = None
    m1_score: Optional[int] = None  # 投研可操作性
    m2_score: Optional[int] = None  # 实体级别
    m3_score: Optional[int] = None  # 数字震撼度
    m4_score: Optional[int] = None  # 跨信号共识
    m5_score: Optional[int] = None  # 范式动摇
    constraint_pass: bool = False
    constraint_rule: Optional[str] = None
    primary_org: Optional[str] = None
    canonical_event_key: Optional[str] = None
    auto_headline: bool = False     # set by HeadlineSelector
    edge_case: bool = False         # set by HeadlineSelector


__all__ = ["Signal"]
