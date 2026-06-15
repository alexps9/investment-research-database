"""Skill: detect likely-duplicate signals."""
from __future__ import annotations

from tools.signals import list_signals


async def find_duplicate_signals(limit: int = 200) -> str:
    """Heuristically flag signals that look like duplicates (same normalised title)."""
    signals = await list_signals(limit=limit)
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


__all__ = ["find_duplicate_signals"]
