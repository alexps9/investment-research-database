"""Load tier / organization lookups from a ``p0_whitelist.yml`` snapshot.

Shared by the alert prefilter and the digest headline selection so the v8
HeadlineClassifier can identify P0+/P0 entities. Always reads as UTF-8 (the
whitelist is full of Chinese; the OS default codec would otherwise fail on
Windows and silently produce empty lookups).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml


def load_whitelist(path: str | Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return ``(tier_lookup, org_lookup)`` from a whitelist YAML.

    - ``tier_lookup``: {entity_name: "P0+"/"P0"/"P1"/"P2"}
    - ``org_lookup``:  {entity_name: org_in_bitable}

    Returns two empty dicts if the file is missing or unparsable.
    """
    tier_lookup: dict[str, str] = {}
    org_lookup: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for entry in data.get("entities", []):
            name = entry.get("name", "")
            if not name:
                continue
            tier_lookup[name] = entry.get("tier", "P2")
            org = entry.get("org_in_bitable", "")
            if org:
                org_lookup[name] = org
    except Exception:
        pass
    return tier_lookup, org_lookup


def name_canon_map(tier_lookup: dict[str, str]) -> dict[str, str]:
    """{lowercased_name: original_name} for case-insensitive author matching."""
    return {k.lower(): k for k in tier_lookup}


__all__ = ["load_whitelist", "name_canon_map"]
