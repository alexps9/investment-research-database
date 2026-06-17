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
import os
import re
from typing import Awaitable, Callable, Optional

from .kb import kb_search
from .llm import ainvoke, make_llm
from .search import search_and_read

ProgressCb = Callable[[str, str, int], None]

# Bounds — keep runs predictable on the shared gateway.
DEFAULT_MAX_SUBTOPICS = 5
DEFAULT_SEARCHES_PER_TOPIC = 2
MAX_CONCURRENCY = 3

# Database-first retrieval: a sub-topic whose KB hits clear these bars is
# considered well-covered internally, so the web is only used to *supplement*
# (1 round) instead of leading the research.
KB_HITS_PER_TOPIC = int(os.getenv("KB_HITS_PER_TOPIC", "8"))
KB_SUFFICIENT_CHARS = int(os.getenv("KB_SUFFICIENT_CHARS", "1200"))
KB_MIN_HITS = int(os.getenv("KB_MIN_HITS", "3"))
# Per-section output cap for the final report. The report is written one section
# at a time so no single token limit can drop a whole "big point" — the failure
# mode the single-shot writer had.
SECTION_MAX_TOKENS = int(os.getenv("REPORT_SECTION_MAX_TOKENS", "2600"))


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
    resp = await ainvoke(llm, [("system", system), ("user", user)])
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
    kb_hits: list[dict] = []
    seen_urls: set[str] = set()
    query = subtopic

    # ── Database-first: ground the sub-topic in the knowledge base before the
    # open web. KB findings lead; the web only supplements when coverage is thin.
    kb_hits = await kb_search(subtopic, limit=KB_HITS_PER_TOPIC)
    kb_chars = 0
    for h in kb_hits:
        line = f"[KB · {h['object_type']}] {h['name']}"
        if h.get("description"):
            line += f": {h['description']}"
        notes.append(line)
        kb_chars += len(h.get("description") or "") + len(h.get("name") or "")

    kb_sufficient = len(kb_hits) >= KB_MIN_HITS and kb_chars >= KB_SUFFICIENT_CHARS
    # When the KB already covers the sub-topic well, do a single web round to add
    # recency/external corroboration; otherwise let the web lead as before.
    web_rounds = 1 if kb_sufficient else searches_per_topic

    for i in range(web_rounds):
        bundle = await search_and_read(query, max_results=6, read_top=3)
        for s in bundle["sources"]:
            if s["url"] and s["url"] not in seen_urls:
                seen_urls.add(s["url"])
                sources.append(s)
        for r in bundle["results"]:
            if r["content"]:
                notes.append(f"[{r['title']}]({r['url']})\n{r['content']}")

        # Reflect: decide whether another, more specific query is needed.
        if i < web_rounds - 1 and notes:
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

    return {"subtopic": subtopic, "findings": findings, "sources": sources, "kb_hits": kb_hits}


# ── phase 5: final report (written section-by-section) ───────────────────────
#
# The report is assembled from independently-written parts — executive summary,
# one section per sub-topic, conclusion — instead of a single LLM call. A single
# call with a fixed max_tokens silently drops whole "big points" once the output
# hits the cap; writing each section on its own budget guarantees full coverage.
# References (KB entries first, with wiki links; external links after) are
# appended deterministically in code so they're always present and accurate.


def _numbered_sources(kb_sources: list[dict], web_sources: list[dict]) -> str:
    """A combined numbered source list the LLM can cite inline as [n]."""
    lines: list[str] = []
    n = 1
    for s in kb_sources:
        desc = f" — {s['description'][:160]}" if s.get("description") else ""
        lines.append(f"[{n}] (知识库/{s.get('object_type')}) {s.get('name')}{desc}")
        n += 1
    for s in web_sources:
        lines.append(f"[{n}] {s.get('title') or s.get('url')} — {s.get('url')}")
        n += 1
    return "\n".join(lines[:60])


def _build_references(kb_sources: list[dict], web_sources: list[dict]) -> str:
    """Markdown references block: database sources (linking to wiki entries)
    above external web links, numbered to match the inline [n] citations."""
    out = ["\n\n---\n\n## 参考来源 / References\n"]
    n = 1
    if kb_sources:
        out.append("### 数据库来源 · Knowledge Base\n")
        for s in kb_sources:
            name = s.get("name") or "(untitled)"
            desc = f" — {s['description']}" if s.get("description") else ""
            if s.get("wiki_url"):
                out.append(f"{n}. [{name}]({s['wiki_url']}){desc}")
            else:
                kind = s.get("object_type") or "entry"
                out.append(f"{n}. {name} *（{kind}）*{desc}")
            n += 1
        out.append("")
    if web_sources:
        out.append("### 外部链接 · External sources\n")
        for s in web_sources:
            title = s.get("title") or s.get("url")
            out.append(f"{n}. [{title}]({s.get('url')})")
            n += 1
    return "\n".join(out)


async def _write_exec_summary(question: str, brief: str, findings_digest: str,
                              src_text: str) -> str:
    system = (
        "You are an expert analyst. Write ONLY the opening of a deep-research "
        "report: a single Markdown H1 title line, then a 2–4 paragraph executive "
        "summary capturing the most important findings and the bottom line. Cite "
        "inline as [n] using the numbered Sources where relevant. Do not write any "
        "other sections. Do not invent facts beyond the findings. " + _lang_clause(question)
    )
    user = (
        f"Question:\n{question}\n\nBrief:\n{brief}\n\n"
        f"Key findings digest:\n{findings_digest}\n\nSources:\n{src_text}\n\n"
        "Write the title + executive summary."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=1400)


async def _write_section(question: str, block: dict, src_text: str) -> str:
    if not block.get("findings"):
        return ""
    system = (
        "You are an expert analyst writing ONE section of a larger deep-research "
        "report. Write an in-depth, well-structured section in Markdown that "
        "starts with a '## ' heading naming the theme. Use sub-headings, concrete "
        "evidence, numbers and names from the findings. Cite inline as [n] using "
        "the numbered Sources. Cover the theme thoroughly — do not summarise to "
        "fit a length; this section stands on its own. Do not invent facts beyond "
        "the findings. Do NOT write an executive summary or conclusion here. "
        + _lang_clause(question)
    )
    user = (
        f"Overall question:\n{question}\n\nThis section's theme:\n{block['subtopic']}\n\n"
        f"Findings for this theme:\n{block['findings'][:16000]}\n\n"
        f"Numbered sources:\n{src_text}\n\nWrite this section."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=SECTION_MAX_TOKENS)


async def _write_conclusion(question: str, findings_digest: str, src_text: str) -> str:
    system = (
        "You are an expert analyst. Write ONLY the closing of a deep-research "
        "report: a '## 结论与展望 / Conclusion' section giving a balanced synthesis, "
        "implications and open questions. Cite inline as [n] where relevant. Do not "
        "repeat earlier sections verbatim. " + _lang_clause(question)
    )
    user = (
        f"Question:\n{question}\n\nFindings digest:\n{findings_digest}\n\n"
        f"Sources:\n{src_text}\n\nWrite the conclusion."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=1400)


async def _write_report(question: str, brief: str, blocks: list[dict],
                        web_sources: list[dict], kb_sources: list[dict]) -> str:
    src_text = _numbered_sources(kb_sources, web_sources)
    active = [b for b in blocks if b.get("findings")]
    digest = "\n\n".join(f"### {b['subtopic']}\n{b['findings']}" for b in active)[:8000]

    # Executive summary first, then all sections in parallel (bounded), preserving
    # sub-topic order; finally the conclusion.
    exec_summary = await _write_exec_summary(question, brief, digest, src_text)

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def _guarded_section(b: dict) -> str:
        async with sem:
            return await _write_section(question, b, src_text)

    sections = await asyncio.gather(*[_guarded_section(b) for b in active])
    conclusion = await _write_conclusion(question, digest, src_text) if active else ""

    body_parts = [exec_summary.strip()]
    body_parts += [s.strip() for s in sections if s.strip()]
    if conclusion.strip():
        body_parts.append(conclusion.strip())
    body = "\n\n".join(body_parts)
    return body + _build_references(kb_sources, web_sources)


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

    # Merge + dedupe external web sources across all sub-topics.
    all_sources: list[dict] = []
    seen: set[str] = set()
    for b in blocks:
        for s in b["sources"]:
            if s["url"] and s["url"] not in seen:
                seen.add(s["url"])
                all_sources.append(s)

    # Merge + dedupe knowledge-base hits (by object), keeping the best score so
    # the report can cite internal sources that jump to their wiki entry.
    kb_map: dict[tuple[str, str], dict] = {}
    for b in blocks:
        for h in b.get("kb_hits", []):
            key = (h.get("object_type"), h.get("object_id"))
            cur = kb_map.get(key)
            if cur is None or (h.get("score") or 0) > (cur.get("score") or 0):
                kb_map[key] = h
    kb_sources = sorted(kb_map.values(), key=lambda h: h.get("score") or 0, reverse=True)

    progress("report", "正在综合撰写最终报告…", 85)
    report = await _write_report(question, brief, blocks, all_sources, kb_sources)

    progress("done", "研究完成", 100)
    return {
        "question": question,
        "brief": brief,
        "subtopics": subtopics,
        "report": report,
        "sources": all_sources,
        "kb_sources": kb_sources,
    }
