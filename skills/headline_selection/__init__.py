"""Skill: select_headlines — turn a batch of raw signals into ranked headline tiers.

Extracted from the HH-Research daily-digest pipeline (``pipeline/headline_selector``
+ ``pipeline/headline_classifier``). Deterministic and offline-capable:

    raw signal dicts ──► Signal ──► classify_many (m1-m5 + 8 strong constraints)
                                     ──► HeadlineSelector.select
                                     ──► {auto_headlines, edge_cases, body, suppressed}

``auto_headlines`` are the strongest, constraint-passing signals (the digest's
"Top 3 / 头条候选" pool); ``edge_cases`` are borderline; ``body`` is everything
else. The optional whitelist YAML lets the classifier recognise P0+/P0 entities.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from skills.headline import (
    HeadlineClassifier,
    HeadlineSelector,
    Signal,
    load_whitelist,
)


def _to_signal(d: dict[str, Any]) -> Signal:
    """Map a KB / alert signal dict onto the classifier's Signal dataclass."""
    text = d.get("raw_text") or d.get("title") or d.get("summary") or d.get("abstract") or ""
    return Signal(
        source=d.get("source") or d.get("signal_type") or "kb",
        source_id=str(d.get("source_id") or d.get("id") or d.get("url") or text[:64]),
        author_name=d.get("author_name") or d.get("author") or d.get("organization") or "",
        url=d.get("url") or d.get("source_url"),
        raw_text=text,
        lang=d.get("lang") or "zh",
        summary_zh=d.get("summary_zh") or d.get("summary"),
    )


def _signal_to_dict(s: Signal, original: dict[str, Any]) -> dict[str, Any]:
    """Return the original dict enriched with classifier scores (for the agent)."""
    out = dict(original)
    out.update({
        "event_type": s.event_type,
        "m_scores": [s.m1_score, s.m2_score, s.m3_score, s.m4_score, s.m5_score],
        "m_sum": sum(filter(None, [s.m1_score, s.m2_score, s.m3_score, s.m4_score, s.m5_score])),
        "constraint_pass": s.constraint_pass,
        "constraint_rule": s.constraint_rule,
        "primary_org": s.primary_org,
        "canonical_event_key": s.canonical_event_key,
        "auto_headline": s.auto_headline,
        "edge_case": s.edge_case,
    })
    return out


def select_headlines(
    signals: list[dict],
    whitelist_path: Optional[str] = None,
    max_auto: int = 3,
    edge_case_threshold: int = 2,
) -> dict:
    """Classify and rank a batch of signals into headline tiers.

    Args:
        signals: list of signal dicts (KB rows, fetched tweets, …). Recognised
            keys: ``title``/``summary``/``abstract``/``raw_text`` (text),
            ``author_name``/``organization`` (entity), ``url``, ``id``/``source_id``.
        whitelist_path: optional ``p0_whitelist.yml`` so the classifier knows
            P0+/P0 entities (improves headline recall on top labs / people).
        max_auto: cap on auto-headline picks (digest Top 3 → 3).
        edge_case_threshold: min m-sum for a non-passing signal to be an edge case.

    Returns:
        {auto_headlines, edge_cases, body, suppressed, counts} — each list holds
        the input dicts enriched with classifier scores, strongest first.
    """
    if not signals:
        return {"auto_headlines": [], "edge_cases": [], "body": [],
                "suppressed": [], "counts": {"auto": 0, "edge": 0, "body": 0}}

    tier_lookup: dict[str, str] = {}
    org_lookup: dict[str, str] = {}
    if whitelist_path and Path(whitelist_path).exists():
        tier_lookup, org_lookup = load_whitelist(whitelist_path)

    classifier = HeadlineClassifier(tier_lookup=tier_lookup, organization_lookup=org_lookup)
    selector = HeadlineSelector(edge_case_threshold=edge_case_threshold, max_auto_per_day=max_auto)

    sig_objs = [_to_signal(d) for d in signals]
    classifier.classify_many(sig_objs)
    result = selector.select(sig_objs)

    pairs = list(zip(sig_objs, signals))

    def enrich(subset: list) -> list[dict]:
        index = {id(s): orig for s, orig in pairs}
        return [_signal_to_dict(s, index.get(id(s), {})) for s in subset]

    return {
        "auto_headlines": enrich(result.auto_headlines),
        "edge_cases": enrich(result.edge_cases),
        "body": enrich(result.body_signals),
        "suppressed": [
            {"source_id": s.source_id, "reason": reason} for s, reason in result.suppressed
        ],
        "counts": {
            "auto": len(result.auto_headlines),
            "edge": len(result.edge_cases),
            "body": len(result.body_signals),
        },
    }


__all__ = ["select_headlines"]
