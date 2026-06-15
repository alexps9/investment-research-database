"""Skill: RAG answer with cited sources."""
from __future__ import annotations

from tools.search import ask


async def answer_with_sources(question: str, top_k: int = 8) -> str:
    """Answer a question via RAG and append the cited sources."""
    res = await ask(question, top_k=top_k)
    if isinstance(res, dict) and res.get("error"):
        return f"RAG failed: {res}"
    lines = [res.get("answer", "(no answer)"), "", "## Sources"]
    for s in res.get("sources", []):
        lines.append(f"- ({s.get('object_type')}) {s.get('name')} — score {s.get('score', 0):.2f}")
    return "\n".join(lines)


__all__ = ["answer_with_sources"]
