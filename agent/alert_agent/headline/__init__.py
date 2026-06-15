"""Vendored HH-Research v8.0 headline classifier (the alert prefilter brain).

Extracted from jingruzhao103-bit/HH-Research → ``daily-digest/src/hh_research``
so the alert prefilter works out of the box without that repo on PYTHONPATH:

    pipeline/headline_classifier.py  -> headline_classifier.py (imports rewired)
    pipeline/canonical_entity.py     -> canonical_entity.py    (verbatim)
    storage/schemas.py (Signal only) -> schemas.py             (pydantic → dataclass)

The classifier is deterministic and offline-capable: it scores a ``Signal`` on 5
dimensions (m1–m5) and decides whether it passes one of 8 strong constraints.
"""
from __future__ import annotations

from .canonical_entity import (
    COMPANY_CANONICAL_MAP,
    CanonicalEntity,
    build_event_key,
    canonicalize,
)
from .headline_classifier import ClassificationResult, HeadlineClassifier
from .schemas import Signal

__all__ = [
    "HeadlineClassifier",
    "ClassificationResult",
    "Signal",
    "CanonicalEntity",
    "canonicalize",
    "build_event_key",
    "COMPANY_CANONICAL_MAP",
]
