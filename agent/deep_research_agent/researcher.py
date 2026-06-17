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

from .kb import (
    fetch_entities_by_type,
    fetch_entity,
    fetch_graph_relations,
    kb_search,
)
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


# ── Research Studio: scope + industry + mandatory sections ───────────────────

async def _build_scope(
    question: str,
    brief: str,
    subtopics: list[str],
    kb_sources: list[dict],
    blocks: list[dict],
) -> dict:
    """Map the research to existing DB topic lanes/rows and collect related entity IDs.

    Optimised for the cross-region backend: topics, the full relation graph and the
    extra semantic search run *concurrently*, and entity types are read from the
    relations' nested subject/object payloads (an in-memory id→type index) instead
    of one HTTP round-trip per hit — which previously added minutes per run.
    """
    # Kick off the three independent network calls at once.
    topics_task = asyncio.create_task(fetch_entities_by_type("topic", limit=50))
    relations_task = asyncio.create_task(fetch_graph_relations(limit=5000))
    extra_hits_task = asyncio.create_task(kb_search(question, types="entity", limit=12))

    topics = await topics_task
    topic_catalog = []
    for t in topics:
        meta = t.get("metadata") or {}
        topic_catalog.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "level": meta.get("level"),
            "lane_key": meta.get("lane_key"),
            "row_key": meta.get("row_key"),
            "color": meta.get("color"),
        })

    catalog_text = json.dumps(topic_catalog, ensure_ascii=False)[:12000]
    classify_sys = (
        "You are a technology taxonomy expert. Given a research question and the "
        "available topic categories from our knowledge base, select the most "
        "relevant topic IDs. Return ONLY JSON: "
        '{"topic_ids":["uuid",...],"lane_ids":["uuid",...],"rationale":"..."} '
        "topic_ids = row-level topics; lane_ids = lane-level topics. "
        "Pick 1-6 total across both lists."
    )
    classify_user = (
        f"Question: {question}\n\nBrief: {brief}\n\nSubtopics: {subtopics}\n\n"
        f"Available topics:\n{catalog_text}"
    )
    # The classification LLM call overlaps the still-running relations/extra-hits fetches.
    raw = await _chat("research", classify_sys, classify_user, temperature=0.1, max_tokens=800)
    parsed = _extract_json(raw)
    topic_ids: list[str] = []
    lane_ids: list[str] = []
    if isinstance(parsed, dict):
        topic_ids = [str(x) for x in (parsed.get("topic_ids") or []) if x]
        lane_ids = [str(x) for x in (parsed.get("lane_ids") or []) if x]

    valid_ids = {t["id"] for t in topic_catalog if t.get("id")}
    topic_ids = [i for i in topic_ids if i in valid_ids]
    lane_ids = [i for i in lane_ids if i in valid_ids]

    relations = await relations_task
    extra_hits = await extra_hits_task

    # Build an id→entity_type index from the relations' nested entities, so we can
    # classify KB/semantic hits without a per-id fetch.
    type_index: dict[str, str] = {}
    for rel in relations:
        for ent in (rel.get("subject") or {}, rel.get("object_entity") or {}):
            eid, et = ent.get("id"), ent.get("entity_type")
            if eid and et:
                type_index[eid] = et

    paper_ids: set[str] = set()
    person_ids: set[str] = set()
    org_ids: set[str] = set()

    def _classify(eid: str | None) -> None:
        if not eid:
            return
        et = type_index.get(eid)
        if et == "paper":
            paper_ids.add(eid)
        elif et == "person":
            person_ids.add(eid)
        elif et == "organization":
            org_ids.add(eid)

    # KB + semantic hits: resolve via the index first; only fetch the few unknowns
    # (concurrently) so we never serialize round-trips.
    hit_ids = {
        h.get("object_id")
        for h in (list(kb_sources) + list(extra_hits))
        if h.get("object_type") == "entity" and h.get("object_id")
    }
    unknown = [eid for eid in hit_ids if eid and eid not in type_index]
    if unknown:
        fetched = await asyncio.gather(*[fetch_entity(eid) for eid in unknown])
        for ent in fetched:
            if ent and ent.get("id") and ent.get("entity_type"):
                type_index[ent["id"]] = ent["entity_type"]
    for eid in hit_ids:
        _classify(eid)

    # Expand via graph relations around selected topics (papers → authors → orgs).
    focus_topic_ids = set(topic_ids) | set(lane_ids)
    if focus_topic_ids:
        for rel in relations:
            rtype = rel.get("relation_type")
            subj = rel.get("subject") or {}
            obj = rel.get("object_entity") or {}
            subj_id, subj_type = subj.get("id"), subj.get("entity_type")
            obj_id, obj_type = obj.get("id"), obj.get("entity_type")

            if rtype == "FOCUSES_ON" and obj_id in focus_topic_ids and subj_type == "paper":
                paper_ids.add(subj_id)
            if rtype == "FOCUSES_ON" and subj_id in focus_topic_ids and obj_type == "paper":
                paper_ids.add(obj_id)

        # Second pass: authors of the collected papers, then their orgs.
        for rel in relations:
            rtype = rel.get("relation_type")
            subj = rel.get("subject") or {}
            obj = rel.get("object_entity") or {}
            subj_id, subj_type = subj.get("id"), subj.get("entity_type")
            obj_id, obj_type = obj.get("id"), obj.get("entity_type")
            if rtype == "AUTHORED":
                if subj_type == "paper" and subj_id in paper_ids and obj_type == "person":
                    person_ids.add(obj_id)
                if obj_type == "paper" and obj_id in paper_ids and subj_type == "person":
                    person_ids.add(subj_id)

        for rel in relations:
            if rel.get("relation_type") != "WORKS_AT":
                continue
            subj = rel.get("subject") or {}
            obj = rel.get("object_entity") or {}
            if subj.get("entity_type") == "person" and subj.get("id") in person_ids and obj.get("entity_type") == "organization":
                org_ids.add(obj.get("id"))
            if obj.get("entity_type") == "person" and obj.get("id") in person_ids and subj.get("entity_type") == "organization":
                org_ids.add(subj.get("id"))

    return {
        "topic_ids": list(dict.fromkeys(topic_ids)),
        "lane_ids": list(dict.fromkeys(lane_ids)),
        "paper_ids": [i for i in paper_ids if i][:120],
        "person_ids": [i for i in person_ids if i][:80],
        "org_ids": [i for i in org_ids if i][:60],
        "topic_catalog": topic_catalog,
    }


async def _industry_analysis(question: str, brief: str, blocks: list[dict]) -> dict:
    """Web-grounded industry tracking: signals, impact, top people, capital."""
    findings = "\n\n".join(
        f"### {b['subtopic']}\n{b.get('findings', '')}" for b in blocks if b.get("findings")
    )[:8000]

    queries = [
        f"{question} industry adoption funding startup 2024 2025",
        f"{question} leading researchers companies investment",
    ]
    notes: list[str] = []
    sources: list[dict] = []
    seen: set[str] = set()
    for q in queries:
        bundle = await search_and_read(q, max_results=5, read_top=2)
        for s in bundle.get("sources", []):
            if s.get("url") and s["url"] not in seen:
                seen.add(s["url"])
                sources.append(s)
        for r in bundle.get("results", []):
            if r.get("content"):
                notes.append(f"[{r.get('title')}]({r.get('url')})\n{r['content'][:3000]}")

    joined = "\n\n---\n\n".join(notes)[:10000]
    system = (
        "You are an industry analyst. From the research question, brief, findings "
        "and web notes, produce a structured industry-tracking JSON. Return ONLY "
        "valid JSON with keys: "
        "tech_signals (array of {title, summary, url}), "
        "impact_md (markdown string: industry impact analysis), "
        "top_people (array of {name, org, why, url?}), "
        "capital (array of {round, target, amount, investors?, url?}). "
        "Be factual; use the notes; if uncertain, say so briefly. "
        + _lang_clause(question)
    )
    user = (
        f"Question: {question}\n\nBrief: {brief}\n\nFindings:\n{findings}\n\n"
        f"Web notes:\n{joined}"
    )
    raw = await _chat("report", system, user, temperature=0.2, max_tokens=2400)
    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        "tech_signals": parsed.get("tech_signals") or [],
        "impact_md": parsed.get("impact_md") or "",
        "top_people": parsed.get("top_people") or [],
        "capital": parsed.get("capital") or [],
        "sources": sources,
    }


async def _write_studio_sections(
    question: str,
    blocks: list[dict],
    scope: dict,
    industry: dict,
    src_text: str,
) -> str:
    """Write the three mandatory Research Studio sections."""
    findings = "\n\n".join(
        f"### {b['subtopic']}\n{b.get('findings', '')}" for b in blocks if b.get("findings")
    )[:10000]
    scope_text = json.dumps({
        "topic_ids": scope.get("topic_ids"),
        "lane_ids": scope.get("lane_ids"),
        "paper_count": len(scope.get("paper_ids") or []),
        "person_count": len(scope.get("person_ids") or []),
    }, ensure_ascii=False)
    industry_text = json.dumps({
        "tech_signals": industry.get("tech_signals"),
        "top_people": industry.get("top_people"),
        "capital": industry.get("capital"),
        "impact_md": (industry.get("impact_md") or "")[:2000],
    }, ensure_ascii=False)

    system = (
        "You are an expert analyst writing THREE mandatory sections for a "
        "deep-research report. Write ONLY these three Markdown sections, each "
        "starting with the exact heading shown:\n"
        "## 技术路线演进\n"
        "## 核心人物\n"
        "## 产业追踪\n"
        "Cover: (1) how the technology routes evolved and which topic categories "
        "apply; (2) key people/orgs and their roles; (3) industry signals, impact, "
        "top talent locations, and capital involvement. Cite inline as [n] where "
        "relevant. Do not write other sections. " + _lang_clause(question)
    )
    user = (
        f"Question: {question}\n\nFindings:\n{findings}\n\n"
        f"Scope (DB topics/entities):\n{scope_text}\n\n"
        f"Industry analysis:\n{industry_text}\n\n"
        f"Numbered sources:\n{src_text}\n\n"
        "Write the three sections."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=SECTION_MAX_TOKENS * 2)


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

    progress("brief", "正在理解问题、明确研究范围并撰写研究简报…", 5)
    brief = await _write_brief(question)

    progress("plan", "正在把问题拆解为可独立检索的研究子主题…", 15)
    subtopics = await _plan_subtopics(question, brief, max_subtopics)
    preview = "、".join(s[:20] for s in subtopics[:5])
    progress("plan", f"已规划 {len(subtopics)} 个子主题：{preview}", 22)

    # Research sub-topics in parallel (bounded concurrency).
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    done_count = {"n": 0}

    async def _guarded(st: str) -> dict:
        async with sem:
            progress("research", f"正在检索知识库与网络：{st[:40]}", 25 + done_count["n"] * 2)
            res = await _research_subtopic(st, question, searches_per_topic)
            done_count["n"] += 1
            pct = 25 + int(52 * done_count["n"] / max(1, len(subtopics)))
            n_src = len(res.get("sources") or []) + len(res.get("kb_hits") or [])
            progress("research", f"完成子主题 {done_count['n']}/{len(subtopics)}（{n_src} 条来源）", pct)
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

    # Scope mapping, industry analysis and the core report are independent given the
    # researched blocks — run them concurrently to cut tail latency (the report write
    # is the longest leg, so overlapping scope/industry with it is ~free).
    progress("synthesis", "正在归纳技术路线类别、产业信号并综合撰写报告…", 80)
    src_text = _numbered_sources(kb_sources, all_sources)
    scope, industry, report_core = await asyncio.gather(
        _build_scope(question, brief, subtopics, kb_sources, blocks),
        _industry_analysis(question, brief, blocks),
        _write_report(question, brief, blocks, all_sources, kb_sources),
    )

    progress("report", "正在撰写技术路线 / 核心人物 / 产业追踪三大板块…", 92)
    studio_sections = await _write_studio_sections(
        question, blocks, scope, industry, src_text,
    )

    # Insert studio sections before references (strip trailing refs from core if any,
    # then append studio sections + fresh references).
    ref_marker = "\n\n---\n\n## 参考来源"
    if ref_marker in report_core:
        report_body = report_core.split(ref_marker)[0].rstrip()
    else:
        report_body = report_core.rstrip()
    report = (
        report_body + "\n\n" + studio_sections.strip()
        + _build_references(kb_sources, all_sources)
    )

    progress("done", "研究完成", 100)
    return {
        "question": question,
        "brief": brief,
        "subtopics": subtopics,
        "report": report,
        "sources": all_sources,
        "kb_sources": kb_sources,
        "scope": scope,
        "industry": industry,
    }
