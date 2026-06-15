"""Deterministic pre-filter built on the vendored HH-Research v8.0
HeadlineClassifier (strong-constraint system).

Runs BEFORE the LLM agent. If the signal passes a strong constraint, it's
guaranteed to be alert-worthy (skip the LLM judge, go straight to summary).
If it fails all constraints but scores >=2, it's a borderline case that still
goes to the agent for judgment. If it scores <2, it's noise — skip entirely.

This saves LLM calls on obvious noise while staying aligned with the daily
digest's classification criteria. The classifier is vendored locally in
``agent/alert_agent/headline/`` (extracted from jingruzhao103-bit/HH-Research),
so no external package is required.
"""

from pathlib import Path
from datetime import datetime, timezone

import yaml

from .headline import HeadlineClassifier, Signal, COMPANY_CANONICAL_MAP

_WHITELIST_PATH = Path(__file__).resolve().parent / "config" / "p0_whitelist.yml"


def _load_tier_lookup() -> dict:
    """Load {entity_name: tier} from p0_whitelist.yml."""
    lookup = {}
    try:
        with open(_WHITELIST_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for entry in data.get("entities", []):
            name = entry.get("name", "")
            tier = entry.get("tier", "P2")
            if name:
                lookup[name] = tier
    except Exception:
        pass
    return lookup


_TIER_LOOKUP_RAW = _load_tier_lookup()
_TIER_LOOKUP_LOWER = {k.lower(): v for k, v in _TIER_LOOKUP_RAW.items()}
_NAME_CANON = {k.lower(): k for k in _TIER_LOOKUP_RAW}

_ORG_LOOKUP = {}
try:
    with open(_WHITELIST_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for entry in data.get("entities", []):
        name = entry.get("name", "")
        org = entry.get("org_in_bitable", "")
        if name and org:
            _ORG_LOOKUP[name] = org
except Exception:
    pass

_TIER_LOOKUP = _TIER_LOOKUP_RAW

_CLASSIFIER = HeadlineClassifier(
    tier_lookup=_TIER_LOOKUP,
    organization_lookup=_ORG_LOOKUP,
)


def _tweet_to_signal(tweet: dict) -> Signal:
    """Convert an alert pipeline tweet dict → a headline-classifier Signal."""
    username = tweet.get("username", "")
    author_name = username

    lower = username.lower()
    if lower in _NAME_CANON:
        author_name = _NAME_CANON[lower]
    elif username in COMPANY_CANONICAL_MAP:
        author_name = username
    elif username in _TIER_LOOKUP:
        author_name = username

    return Signal(
        source="x" if tweet.get("source_tier", "twitter") == "twitter" else "rss",
        source_id=f"alert:{tweet.get('tweet_id', '')}",
        author_name=author_name,
        url=tweet.get("url", ""),
        raw_text=tweet.get("text", ""),
        created_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
    )


def prefilter(tweet: dict) -> dict:
    """Run deterministic pre-filter on a tweet.

    Returns:
        {
            "action": "pass" | "borderline" | "skip",
            "constraint_rule": str | None,
            "event_type": str | None,
            "scores": {"m1": int, "m2": int, "m3": int, "m4": int, "m5": int},
            "rationale": str,
        }
    """
    signal = _tweet_to_signal(tweet)
    result = _CLASSIFIER.classify_one(signal)

    total_score = result.m1 + result.m2 + result.m3 + result.m4 + result.m5

    if result.constraint_pass:
        action = "pass"
    elif total_score >= 2:
        action = "borderline"
    else:
        action = "skip"

    return {
        "action": action,
        "constraint_rule": result.constraint_rule,
        "event_type": result.event_type,
        "scores": {
            "m1": result.m1, "m2": result.m2, "m3": result.m3,
            "m4": result.m4, "m5": result.m5,
        },
        "total_score": total_score,
        "rationale": result.rationale,
    }
