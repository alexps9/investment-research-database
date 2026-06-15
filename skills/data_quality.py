"""Data-quality skills: audit and improve the knowledge base.

Skills are higher-level workflows composed from atomic ``tools``. They return
human-readable summaries (strings) so they can be used both programmatically and
as agent tools.
"""
from __future__ import annotations

from tools import kb_client as kb

# Fields we consider important for a "complete" source profile.
_KEY_SOURCE_FIELDS = ["tier", "sector", "organization_id", "description", "activity_status"]


async def audit_source_quality(limit: int = 200) -> str:
    """Scan sources and report completeness issues (missing tier/sector/org/etc.).

    Returns a markdown summary the operator (or agent) can act on.
    """
    sources = await kb.list_sources(limit=limit)
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


async def find_duplicate_signals(limit: int = 200) -> str:
    """Heuristically flag signals that look like duplicates (same normalised title)."""
    signals = await kb.list_signals(limit=limit)
    if isinstance(signals, dict) and signals.get("error"):
        return f"Failed to list signals: {signals}"

    seen: dict[str, list[str]] = {}
    for s in signals:
        key = (s.get("title") or "").strip().lower()
        seen.setdefault(key, []).append(s.get("id"))

    dups = {k: v for k, v in seen.items() if len(v) > 1}
    if not dups:
        return "No duplicate signal titles found."
    lines = [f"# Potential duplicate signals ({len(dups)} groups)"]
    for title, ids in list(dups.items())[:50]:
        lines.append(f"- \"{title}\" → {len(ids)} copies: {', '.join(ids)}")
    return "\n".join(lines)
