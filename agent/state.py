"""Shared LangGraph pipeline state."""
from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


def _merge_dicts(left: dict, right: dict) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class PipelineState(TypedDict, total=False):
    """State flowing through the intelligence pipeline graph."""

    # Run metadata
    run_meta: Annotated[dict[str, Any], _merge_dicts]

    # Ingestion
    raw_items: Annotated[list[dict], operator.add]
    signals: Annotated[list[dict], operator.add]

    # Analysis
    analyses: Annotated[list[dict], operator.add]

    # Entity / KG
    entities: Annotated[list[dict], operator.add]
    relations: Annotated[list[dict], operator.add]

    # Alert
    alerts: Annotated[list[dict], operator.add]

    # Digest (daily graph)
    digest_payload: dict
    digest_xml: Optional[str]

    # Errors accumulate across nodes
    errors: Annotated[list[str], operator.add]


def empty_state(**kwargs: Any) -> PipelineState:
    base: PipelineState = {
        "run_meta": {},
        "raw_items": [],
        "signals": [],
        "analyses": [],
        "entities": [],
        "relations": [],
        "alerts": [],
        "errors": [],
    }
    base.update(kwargs)
    return base
