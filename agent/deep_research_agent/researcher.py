"""Deep-research orchestrator.

A faithful, deployment-friendly port of langchain-ai/open_deep_research's flow:

    brief  →  plan (supervisor decomposes into sub-topics)
           →  research each sub-topic in parallel (search + read + reflect)
           →  compress each sub-topic's findings
           →  write the final report (with cited sources)

All LLM calls go through the LiteLLM gateway (see ``llm.py``); search uses the
repo's free DuckDuckGo tool (see ``search.py``). Progress is reported via an
``on_progress(phase, message, pct)`` callback so the HTTP layer can stream it to
the UI. The whole run is async and bounded (sub-topic + search caps) to keep
latency and cost predictable on the shared gateway.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Awaitable, Callable, Optional

from .llm import make_llm
from .search import search_and_read

ProgressCb = Callable[[str, str, int], None]

# Bounds — keep runs predictable on the shared gateway.
DEFAULT_MAX_SUBTOPICS = 4
DEFAULT_SEARCHES_PER_TOPIC = 2
MAX_CONCURRENCY = 3


def _is_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _lang_clause(question: str) -> str:
    return "用中文撰写。" if _is_chinese(question) else "Write in English."


def _extract_json(text: str):
    """Best-effort JSON extraction from an LLM reply (handles ```json fences)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    if start == -1:
        start = text.find("{")
    if start != -1:
        text = text[start:]
    try:
        return json.loads(text)
    except Exception:
        # last resort: grab the first [...] block
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


async def _chat(role: str, system: str, user: str, *, temperature: float = 0.0,
                max_tokens: int | None = None) -> str:
    llm = make_llm(role, temperature=temperature, max_tokens=max_tokens)
    resp = await llm.ainvoke([("system", system), ("user", user)])
    return (resp.content or "").strip() if isinstance(resp.content, str) else str(resp.content)


# ── phase 1: research brief ──────────────────────────────────────────────────

async def _write_brief(question: str) -> str:
    system = (
        "You are a senior research lead. Turn the user's request into a tight, "
        "actionable research brief: restate the core question, list the key "
        "aspects worth investigating, and note what a high-quality answer must "
        "cover. Be concise (one short paragraph + bullet aspects). "
        + _lang_clause(question)
    )
    return await _chat("research", system, f"User request:\n{question}", temperature=0.2)


# ── phase 2: plan / supervisor ───────────────────────────────────────────────

async def _plan_subtopics(question: str, brief: str, max_subtopics: int) -> list[str]:
    system = (
        "You are a research supervisor. Decompose the brief into at most "
        f"{max_subtopics} focused, non-overlapping sub-topics, each phrased as a "
        "self-contained web-search question that a researcher can investigate "
        "independently. Return ONLY a JSON array of strings, no prose."
    )
    user = f"Brief:\n{brief}\n\nReturn the JSON array of sub-topic search questions."
    raw = await _chat("research", system, user, temperature=0.3)
    parsed = _extract_json(raw)
    subtopics: list[str] = []
    if isinstance(parsed, list):
        subtopics = [str(s).strip() for s in parsed if str(s).strip()]
    if not subtopics:
        subtopics = [question]
    return subtopics[:max_subtopics]


# ── phase 3+4: research a sub-topic (search + read + reflect → compress) ──────

async def _research_subtopic(
    subtopic: str, question: str, searches_per_topic: int,
) -> dict:
    notes: list[str] = []
    sources: list[dict] = []
    seen_urls: set[str] = set()
    query = subtopic

    for i in range(searches_per_topic):
        bundle = await search_and_read(query, max_results=6, read_top=3)
        for s in bundle["sources"]:
            if s["url"] and s["url"] not in seen_urls:
                seen_urls.add(s["url"])
                sources.append(s)
        for r in bundle["results"]:
            if r["content"]:
                notes.append(f"[{r['title']}]({r['url']})\n{r['content']}")

        # Reflect: decide whether another, more specific query is needed.
        if i < searches_per_topic - 1 and notes:
            reflect_sys = (
                "You are a researcher. Given the sub-topic and notes gathered so "
                "far, decide if a follow-up web search would meaningfully improve "
                "coverage. If yes, return ONLY the next search query string. If the "
                "notes are already sufficient, return exactly: DONE."
            )
            joined = "\n\n---\n\n".join(notes)[:8000]
            nxt = await _chat(
                "research", reflect_sys,
                f"Sub-topic: {subtopic}\n\nNotes so far:\n{joined}",
                temperature=0.2, max_tokens=120,
            )
            if nxt.strip().upper().startswith("DONE") or not nxt.strip():
                break
            query = nxt.strip().strip('"')

    # Compress the notes into findings for this sub-topic.
    if notes:
        compress_sys = (
            "You are a research analyst. Synthesize the notes into concise, "
            "factual findings for the sub-topic. Preserve concrete facts, numbers "
            "and names; cite sources inline as [n] using the order they appear. "
            "Omit fluff and duplicates. " + _lang_clause(question)
        )
        joined = "\n\n---\n\n".join(notes)[:12000]
        findings = await _chat(
            "compression", compress_sys,
            f"Sub-topic: {subtopic}\n\nNotes:\n{joined}",
            temperature=0.1,
        )
    else:
        findings = ""

    return {"subtopic": subtopic, "findings": findings, "sources": sources}


# ── phase 5: final report ────────────────────────────────────────────────────

async def _write_report(question: str, brief: str, blocks: list[dict],
                        all_sources: list[dict]) -> str:
    parts = []
    for b in blocks:
        if b["findings"]:
            parts.append(f"## Sub-topic: {b['subtopic']}\n{b['findings']}")
    findings_text = "\n\n".join(parts)[:18000]

    src_lines = [f"[{i}] {s['title']} — {s['url']}" for i, s in enumerate(all_sources, 1)]
    src_text = "\n".join(src_lines[:40])

    system = (
        "You are an expert analyst writing a deep-research report. Using ONLY the "
        "research findings provided, write a well-structured, in-depth report in "
        "Markdown with: a short executive summary, themed sections with headings, "
        "concrete evidence, and a balanced synthesis/conclusion. Cite sources "
        "inline as [n] referencing the numbered Sources list, and end with a "
        "'## 参考来源 / Sources' section listing the cited sources. Do not invent "
        "facts beyond the findings. " + _lang_clause(question)
    )
    user = (
        f"Original question:\n{question}\n\nResearch brief:\n{brief}\n\n"
        f"Findings:\n{findings_text}\n\nSources:\n{src_text}\n\nWrite the report."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=4000)


# ── public entrypoint ────────────────────────────────────────────────────────

async def run_deep_research(
    question: str,
    *,
    on_progress: Optional[ProgressCb] = None,
    max_subtopics: int = DEFAULT_MAX_SUBTOPICS,
    searches_per_topic: int = DEFAULT_SEARCHES_PER_TOPIC,
) -> dict:
    """Run the full deep-research pipeline. Returns ``{report, brief, subtopics, sources}``."""
    def progress(phase: str, message: str, pct: int) -> None:
        if on_progress:
            try:
                on_progress(phase, message, pct)
            except Exception:
                pass

    progress("brief", "正在理解问题并撰写研究简报…", 5)
    brief = await _write_brief(question)

    progress("plan", "正在拆解研究子主题…", 15)
    subtopics = await _plan_subtopics(question, brief, max_subtopics)
    progress("plan", f"已规划 {len(subtopics)} 个子主题", 20)

    # Research sub-topics in parallel (bounded concurrency).
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    done_count = {"n": 0}

    async def _guarded(st: str) -> dict:
        async with sem:
            progress("research", f"正在研究：{st}", 25)
            res = await _research_subtopic(st, question, searches_per_topic)
            done_count["n"] += 1
            pct = 25 + int(55 * done_count["n"] / max(1, len(subtopics)))
            progress("research", f"完成子主题 {done_count['n']}/{len(subtopics)}", pct)
            return res

    blocks = await asyncio.gather(*[_guarded(st) for st in subtopics])

    # Merge + dedupe sources across all sub-topics.
    all_sources: list[dict] = []
    seen: set[str] = set()
    for b in blocks:
        for s in b["sources"]:
            if s["url"] and s["url"] not in seen:
                seen.add(s["url"])
                all_sources.append(s)

    progress("report", "正在综合撰写最终报告…", 85)
    report = await _write_report(question, brief, blocks, all_sources)

    progress("done", "研究完成", 100)
    return {
        "question": question,
        "brief": brief,
        "subtopics": subtopics,
        "report": report,
        "sources": all_sources,
    }
