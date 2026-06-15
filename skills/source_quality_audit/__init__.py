"""Skill: audit source data completeness."""
from __future__ import annotations

from tools.sources import list_sources

# Fields we consider important for a "complete" source profile.
_KEY_SOURCE_FIELDS = ["tier", "sector", "organization_id", "description", "activity_status"]


async def audit_source_quality(limit: int = 200) -> str:
    """Scan sources and report completeness issues (missing tier/sector/org/etc.).

    Returns a markdown summary the operator (or agent) can act on.
    """
    sources = await list_sources(limit=limit)
    if isinstance(sources, dict) and sources.get("error"):
        return f"Failed to list sources: {sources}"

    total = len(sources)
    issues: list[str] = []
    missing_counts = {f: 0 for f in _KEY_SOURCE_FIELDS}
    for s in sources:
        missing = [f for f in _KEY_SOURCE_FIELDS if not s.get(f)]
        for f in missing:
            missing_counts[f] += 1
        if missing:
            issues.append(f"- `{s.get('name')}` ({s.get('id')}): missing {', '.join(missing)}")

    lines = [
        f"# Source quality audit ({total} sources)",
        "",
        "## Missing-field counts",
        *[f"- {f}: {c}" for f, c in missing_counts.items()],
        "",
        f"## Incomplete sources ({len(issues)})",
        *(issues[:50] or ["- none 🎉"]),
    ]
    if len(issues) > 50:
        lines.append(f"- … and {len(issues) - 50} more")
    return "\n".join(lines)


__all__ = ["audit_source_quality"]
