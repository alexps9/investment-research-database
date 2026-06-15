"""Skill: generate the Daily Boost briefing as markdown."""
from __future__ import annotations

from tools.daily import generate_daily_digest


async def daily_brief(window_days: int = 1) -> str:
    """Generate (or regenerate) the Daily Boost digest and return it as markdown."""
    digest = await generate_daily_digest(window_days=window_days)
    if isinstance(digest, dict) and digest.get("error"):
        return f"Failed to generate digest: {digest}"

    lines = [
        f"# Daily brief — {digest.get('digest_date')}",
        "",
        digest.get("summary") or "(no summary)",
        "",
        "## Highlights",
    ]
    for h in digest.get("highlights", []):
        reason = f" — {h['reason']}" if h.get("reason") else ""
        lines.append(f"- [{h.get('signal_type')}] {h.get('title')}{reason}")
    return "\n".join(lines)


__all__ = ["daily_brief"]
