"""Skill: summarise the investment/financing landscape."""
from __future__ import annotations

from tools.funding import funding_trends


async def funding_landscape_summary() -> str:
    """Summarise the investment/financing landscape from aggregated trends."""
    trends = await funding_trends()
    if isinstance(trends, dict) and trends.get("error"):
        return f"Failed to load trends: {trends}"

    def fmt(rows, key):
        return "\n".join(
            f"- {r.get(key)}: {r['count']} deals, ${r['amount_usd']:.1f}M" for r in rows[:10]
        ) or "- (none)"

    return "\n".join([
        "# Funding landscape",
        f"\nTotal: {trends.get('total_count')} deals, "
        f"${trends.get('total_amount_usd', 0):.1f}M raised",
        "\n## By sector", fmt(trends.get("by_sector", []), "sector"),
        "\n## By round", fmt(trends.get("by_round", []), "round"),
        "\n## By month", fmt(trends.get("by_month", []), "month"),
    ])


__all__ = ["funding_landscape_summary"]
