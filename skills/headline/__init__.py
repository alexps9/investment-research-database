"""Vendored HH-Research v8.0 headline classifier + selector (shared support pkg).

Extracted from jingruzhao103-bit/HH-Research → ``daily-digest/src/hh_research``
so both the alert prefilter and the digest headline selection work out of the box
without that repo on PYTHONPATH:

    pipeline/headline_classifier.py  -> headline_classifier.py (imports rewired)
    pipeline/headline_selector.py    -> headline_selector.py   (imports rewired)
    pipeline/canonical_entity.py     -> canonical_entity.py    (verbatim)
    storage/schemas.py (Signal only) -> schemas.py             (pydantic → dataclass)

NOTE: this is a *support package*, not a skill function — it carries no entry in
``skills.SKILLS``. ``skills/headline_selection`` is the skill that wraps it.

The classifier is deterministic and offline-capable: it scores a ``Signal`` on 5
dimensions (m1–m5) and decides whether it passes one of 8 strong constraints; the
selector then partitions classified signals into auto-headline / edge / body.
"""
from __future__ import annotations

from .canonical_entity import (
    COMPANY_CANONICAL_MAP,
    CanonicalEntity,
    build_event_key,
    canonicalize,
)
from .headline_classifier import ClassificationResult, HeadlineClassifier
from .headline_selector import (
    MAX_AUTO_HEADLINES_PER_DAY,
    HeadlineSelector,
    SelectionResult,
)
from .schemas import Signal
from .whitelist import load_whitelist, name_canon_map

__all__ = [
    "HeadlineClassifier",
    "ClassificationResult",
    "HeadlineSelector",
    "SelectionResult",
    "MAX_AUTO_HEADLINES_PER_DAY",
    "Signal",
    "CanonicalEntity",
    "canonicalize",
    "build_event_key",
    "COMPANY_CANONICAL_MAP",
    "load_whitelist",
    "name_canon_map",
]
