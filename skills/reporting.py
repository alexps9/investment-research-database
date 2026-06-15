"""Reporting skills: turn raw KB data into briefings."""
from __future__ import annotations

from tools import kb_client as kb


async def daily_brief(window_days: int = 1) -> str:
    """Generate (or regenerate) the Daily Boost digest and return it as markdown."""
    digest = await kb.generate_daily_digest(window_days=window_days)
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


async def funding_landscape_summary() -> str:
    """Summarise the investment/financing landscape from aggregated trends."""
    trends = await kb.funding_trends()
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


async def answer_with_sources(question: str, top_k: int = 8) -> str:
    """Answer a question via RAG and append the cited sources."""
    res = await kb.ask(question, top_k=top_k)
    if isinstance(res, dict) and res.get("error"):
        return f"RAG failed: {res}"
    lines = [res.get("answer", "(no answer)"), "", "## Sources"]
    for s in res.get("sources", []):
        lines.append(f"- ({s.get('object_type')}) {s.get('name')} — score {s.get('score', 0):.2f}")
    return "\n".join(lines)
