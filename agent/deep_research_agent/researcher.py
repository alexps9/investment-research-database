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


def _scan_balanced(text: str, start: int) -> str | None:
    """Return the complete JSON value (object/array) beginning at ``text[start]``
    by scanning for the matching close bracket, honouring strings/escapes."""
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _extract_json(text: str):
    """Best-effort JSON extraction from an LLM reply (handles ```json fences).

    IMPORTANT: pick whichever of ``{`` / ``[`` appears FIRST so that an object
    which merely *contains* an array (e.g. ``{"categories":[...],"x":{}}``) is
    parsed as the object, not mis-truncated to its inner array.
    """
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    obj_at = text.find("{")
    arr_at = text.find("[")
    candidates = [p for p in (obj_at, arr_at) if p != -1]
    if not candidates:
        return None
    start = min(candidates)
    # 1) Whole remainder (fast path for clean replies).
    try:
        return json.loads(text[start:])
    except Exception:
        pass
    # 2) Balanced-bracket extraction from the first opening bracket.
    snippet = _scan_balanced(text, start)
    if snippet:
        try:
            return json.loads(snippet)
        except Exception:
            pass
    # 3) Last resort: try the other bracket type if present.
    other = arr_at if start == obj_at else obj_at
    if other != -1:
        snippet = _scan_balanced(text, other)
        if snippet:
            try:
                return json.loads(snippet)
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
        "report: a single Markdown H1 title line (the report title), then on the "
        "next line the exact heading '## 1. 执行摘要', then a 3–5 paragraph executive "
        "summary that distils the bottom line — the main technology routes, the key "
        "people/teams, and the industry & capital picture. Cite inline as [n] using "
        "the numbered Sources where relevant. Do NOT write any other section or any "
        "'##' heading besides '## 1. 执行摘要'. Do not invent facts beyond the "
        "findings. " + _lang_clause(question)
    )
    user = (
        f"Question:\n{question}\n\nBrief:\n{brief}\n\n"
        f"Key findings digest:\n{findings_digest}\n\nSources:\n{src_text}\n\n"
        "Write the H1 title + '## 1. 执行摘要' section."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=1500)


async def _write_route_section(question: str, findings_digest: str, scope: dict,
                               src_text: str) -> str:
    categories = [c.get("label") for c in (scope.get("route_categories") or []) if c.get("label")]
    if categories:
        cat_lines = "\n".join(f"{i + 1}. {lab}" for i, lab in enumerate(categories))
        category_clause = (
            "Organise the section into numbered sub-sections, ONE per technology-route "
            "category below, IN THIS ORDER, using these EXACT names as the sub-section "
            "titles (e.g. '### 2.1 <category>'):\n" + cat_lines + "\n"
            "These categories are the same ones shown on the Technology-Trajectory page, "
            "so they must match. Assign each work/finding to its category. Omit a "
            "category only if it has no relevant content; do not invent new categories.\n"
        )
    else:
        category_clause = (
            "Group the technical approaches into numbered sub-sections "
            "'### 2.1 <route name>', '### 2.2 <route name>', … one per route or major "
            "technical theme.\n"
        )
    system = (
        "You are an expert analyst writing the '技术路线' section of a deep-research "
        "report. Start with the exact heading '## 2. 技术路线'. " + category_clause +
        "Fold ALL relevant technical findings into these sub-sections: how each route "
        "evolved over time, representative works/models with dates, and the "
        "relationships and trade-offs between routes. Cite inline as [n]. Do NOT create "
        "any other top-level '##' heading and do NOT write an executive summary, people "
        "or industry section here. " + _lang_clause(question)
    )
    user = (
        f"Question:\n{question}\n\nFindings:\n{findings_digest}\n\n"
        f"Numbered sources:\n{src_text}\n\n"
        "Write the '## 2. 技术路线' section with numbered sub-headings."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=SECTION_MAX_TOKENS * 2)


async def _write_people_section(question: str, findings_digest: str, scope: dict,
                                src_text: str) -> str:
    people_hint = json.dumps({
        "core_people": [
            {"name": p.get("name"), "org": p.get("org")} for p in (scope.get("core_people") or [])
        ],
        "person_count": len(scope.get("person_ids") or []),
        "org_count": len(scope.get("org_ids") or []),
    }, ensure_ascii=False)[:3500]
    system = (
        "You are an expert analyst writing the '核心人物' section of a deep-research "
        "report. Start with the exact heading '## 3. 核心人物'. Use numbered "
        "sub-sections '### 3.1 <person or team>', '### 3.2 …' covering the key "
        "researchers/teams/organisations (prefer the core_people listed), their "
        "affiliations, signature contributions, and how they relate to each other and "
        "the technology routes. Fold all people/org findings here. Cite inline as [n]. "
        "Do NOT create any other top-level '##' heading. " + _lang_clause(question)
    )
    user = (
        f"Question:\n{question}\n\nKey people (DB):\n{people_hint}\n\n"
        f"Findings:\n{findings_digest}\n\nNumbered sources:\n{src_text}\n\n"
        "Write the '## 3. 核心人物' section with numbered sub-headings."
    )
    return await _chat("report", system, user, temperature=0.3, max_tokens=SECTION_MAX_TOKENS)


def _compose_industry_section(industry: dict) -> str:
    """Deterministically assemble '## 4. 产业追踪' from the industry dict, so the
    report's section 4 stays consistent with the Industry Tracking page."""
    lines: list[str] = ["## 4. 产业追踪", ""]

    signals = industry.get("tech_signals") or []
    lines.append("### 4.1 技术信号")
    if signals:
        for s in signals:
            title = (s.get("title") or "").strip()
            summary = (s.get("summary") or "").strip()
            lines.append(f"- **{title}** — {summary}" if title else f"- {summary}")
    else:
        lines.append("_暂无明确的技术信号。_")
    lines.append("")

    impact = (industry.get("impact_md") or "").strip()
    lines.append("### 4.2 产业影响")
    lines.append(impact or "_暂无产业影响分析。_")
    lines.append("")

    people = industry.get("core_people") or []
    lines.append("### 4.3 核心人物与实时信号")
    if people:
        for p in people[:12]:
            name = (p.get("name") or "").strip()
            org = (p.get("org") or "").strip()
            wiki = p.get("wiki_url")
            label = f"[{name}]({wiki})" if wiki else name
            lines.append(f"- {label}{f' · {org}' if org else ''}")
    else:
        lines.append("_暂无核心人物。_")
    psig = industry.get("person_signals") or []
    for it in psig[:12]:
        person = (it.get("person") or "").strip()
        title = (it.get("title") or "").strip()
        url = it.get("url")
        date = (it.get("date") or "").strip()
        head = f"[{title}]({url})" if url else title
        lines.append(f"  - {person}：{head}{f'（{date}）' if date else ''}")
    lines.append("")

    cap = industry.get("capital") or []
    fund = industry.get("funding") or []
    lines.append("### 4.4 资本介入与融资")
    if cap or fund:
        for c in cap[:12]:
            person = (c.get("person") or "").strip()
            target = (c.get("target") or "").strip()
            parts = [x for x in (c.get("round"), c.get("amount"), c.get("investors")) if x]
            url = c.get("url")
            tail = f"（{c.get('date')}）" if c.get("date") else ""
            line = f"- 资本介入 · {person}：{target} {' · '.join(parts)}{tail}".rstrip()
            if url:
                line += f" [链接]({url})"
            lines.append(line)
        for f in fund[:12]:
            person = (f.get("person") or "").strip()
            company = (f.get("company") or "").strip()
            parts = [x for x in (f.get("round"), f.get("amount")) if x]
            url = f.get("url")
            tail = f"（{f.get('date')}）" if f.get("date") else ""
            line = f"- 融资 · {person}：{company} {' · '.join(parts)}{tail}".rstrip()
            if url:
                line += f" [链接]({url})"
            lines.append(line)
    else:
        lines.append("_暂未发现明确的资本介入或融资事件。_")
    lines.append("")
    return "\n".join(lines)


async def _write_report(question: str, brief: str, blocks: list[dict], scope: dict,
                        web_sources: list[dict], kb_sources: list[dict]) -> str:
    """Write report sections 1–3 (执行摘要 / 技术路线 / 核心人物). Section 4 (产业追踪)
    is composed separately from the industry data, and references are appended by the
    caller — because industry analysis is derived from this report body."""
    src_text = _numbered_sources(kb_sources, web_sources)
    active = [b for b in blocks if b.get("findings")]
    digest = "\n\n".join(f"### {b['subtopic']}\n{b['findings']}" for b in active)[:12000]

    exec_summary, routes, people = await asyncio.gather(
        _write_exec_summary(question, brief, digest, src_text),
        _write_route_section(question, digest, scope, src_text),
        _write_people_section(question, digest, scope, src_text),
    )
    return "\n\n".join(p.strip() for p in (exec_summary, routes, people) if p.strip())


# ── Research Studio: scope + industry + mandatory sections ───────────────────

async def _classify_routes(question: str, brief: str, papers: list[dict]) -> tuple[list[dict], dict]:
    """Group the scope papers into technology-route categories — derived from the
    works themselves (count is data-driven, NOT a fixed list). Returns
    ``(categories=[{key,label}], assignments={paper_id: key})``.

    Both the report's §2 sub-headings and the Trajectory page's lanes use these, so
    the two always agree and the labels are never hard-coded."""
    if not papers:
        return [], {}
    listing = json.dumps(papers, ensure_ascii=False)[:11000]
    system = (
        "You are a technology-taxonomy expert. Group the listed academic works into "
        "the main TECHNOLOGY ROUTES for this research question. Derive the routes from "
        "the works themselves and choose however many distinct routes best fit the data "
        "(do NOT force a fixed number). Return JSON ONLY: "
        '{"categories":[{"key":"snake_case_id","label":"简短类别名"}],'
        '"assignments":{"<paper_id>":"<category_key>"}}. '
        "Assign EVERY paper to exactly one existing category key. Keep labels short and "
        "human-readable. " + _lang_clause(question)
    )
    user = f"Question: {question}\n\nBrief: {brief}\n\nWorks (id + title):\n{listing}"
    raw = await _chat("research", system, user, temperature=0.1, max_tokens=1600)
    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        return [], {}
    cats: list[dict] = []
    seen: set[str] = set()
    for c in parsed.get("categories") or []:
        key = str((c or {}).get("key") or "").strip()
        label = str((c or {}).get("label") or "").strip()
        if key and label and key not in seen:
            seen.add(key)
            cats.append({"key": key, "label": label})
    valid_keys = {c["key"] for c in cats}
    assignments: dict[str, str] = {}
    for pid, key in (parsed.get("assignments") or {}).items():
        k = str(key or "").strip()
        if k in valid_keys:
            assignments[str(pid)] = k
    return cats, assignments


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

    # Build id→entity_type and id→name indexes from the relations' nested entities,
    # so we can classify KB/semantic hits without a per-id fetch.
    type_index: dict[str, str] = {}
    name_index: dict[str, str] = {}
    paper_lane: dict[str, str] = {}  # paper_id → lane key (for route categories)
    for rel in relations:
        for ent in (rel.get("subject") or {}, rel.get("object_entity") or {}):
            eid, et = ent.get("id"), ent.get("entity_type")
            if eid and et:
                type_index[eid] = et
                if ent.get("name"):
                    name_index[eid] = ent["name"]
                if et == "paper":
                    lane = (ent.get("metadata") or {}).get("lane")
                    if lane:
                        paper_lane[eid] = lane

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
                if ent.get("name"):
                    name_index[ent["id"]] = ent["name"]
    for eid in hit_ids:
        _classify(eid)

    # Expand papers via FOCUSES_ON to the classified topics (only when topics exist).
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

    # Author + org expansion runs ALWAYS (not gated on topic classification): every
    # author of a retrieved/expanded paper is a core person, and their org is added.
    # This is why "all queried sources" (e.g. paper authors) become core people even
    # when topic classification is thin or empty.
    for rel in relations:
        if rel.get("relation_type") != "AUTHORED":
            continue
        subj = rel.get("subject") or {}
        obj = rel.get("object_entity") or {}
        subj_id, subj_type = subj.get("id"), subj.get("entity_type")
        obj_id, obj_type = obj.get("id"), obj.get("entity_type")
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

    # person → org name (best-effort, from WORKS_AT) for richer "core people" cards.
    person_org: dict[str, str] = {}
    for rel in relations:
        if rel.get("relation_type") != "WORKS_AT":
            continue
        subj = rel.get("subject") or {}
        obj = rel.get("object_entity") or {}
        if subj.get("entity_type") == "person" and obj.get("entity_type") == "organization":
            person_org.setdefault(subj.get("id"), obj.get("name") or "")
        if obj.get("entity_type") == "person" and subj.get("entity_type") == "organization":
            person_org.setdefault(obj.get("id"), subj.get("name") or "")

    person_list = [i for i in person_ids if i][:120]

    # Resolve names for any person still missing one, so core_people can cover ALL
    # the persons we found (every queried person source is a core person).
    missing_names = [pid for pid in person_list if not name_index.get(pid)]
    if missing_names:
        fetched = await asyncio.gather(*[fetch_entity(pid) for pid in missing_names])
        for ent in fetched:
            if ent and ent.get("id") and ent.get("name"):
                name_index[ent["id"]] = ent["name"]

    core_people = [
        {
            "id": pid,
            "name": name_index.get(pid) or "",
            "org": person_org.get(pid) or "",
            "wiki_url": f"/wiki/entities/{pid}",
        }
        for pid in person_list
        if name_index.get(pid)
    ]

    paper_list = [i for i in paper_ids if i][:120]

    # Dynamic technology-route categories (shared by report §2 + trajectory lanes).
    papers_for_cat = [
        {"id": pid, "title": name_index.get(pid) or "", "lane_hint": paper_lane.get(pid, "")}
        for pid in paper_list if name_index.get(pid)
    ][:90]
    route_categories, paper_categories = await _classify_routes(question, brief, papers_for_cat)

    return {
        "topic_ids": list(dict.fromkeys(topic_ids)),
        "lane_ids": list(dict.fromkeys(lane_ids)),
        "paper_ids": paper_list,
        "person_ids": person_list,
        "org_ids": [i for i in org_ids if i][:60],
        "core_people": core_people,
        "route_categories": route_categories,
        "paper_categories": paper_categories,
        "topic_catalog": topic_catalog,
    }


async def _interpret_report_signals(question: str, report_body: str) -> dict:
    """ONE LLM call that reads the generated report and extracts tech signals +
    an industry-impact reading (no web search — pure interpretation)."""
    system = (
        "You are an industry analyst. Read the deep-research REPORT and produce a "
        "structured reading as JSON ONLY: "
        '{"tech_signals":[{"title":"...","summary":"..."}],'
        '"impact_md":"markdown industry-impact analysis"}. '
        "tech_signals = 4–8 concrete technical signals/trends the report implies "
        "(each a short title + 1–2 sentence summary). impact_md = a few markdown "
        "paragraphs on industrialisation impact, adoption and what it means for the "
        "field. Base everything strictly on the report. " + _lang_clause(question)
    )
    user = f"Question: {question}\n\nREPORT:\n{report_body[:14000]}"
    raw = await _chat("report", system, user, temperature=0.2, max_tokens=1800)
    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        "tech_signals": parsed.get("tech_signals") or [],
        "impact_md": parsed.get("impact_md") or "",
    }


async def _track_people_events(question: str, core_people: list[dict]) -> dict:
    """Web-search each core person for their real-time signals, capital involvement
    and funding events; structure into JSON. Prefer recent events but widen the
    window when nothing fresh exists so the page is never empty."""
    people = [p for p in core_people if p.get("name")][:8]
    sources: list[dict] = []
    seen: set[str] = set()
    if not people:
        return {"person_signals": [], "capital": [], "funding": [], "sources": []}

    async def _search_person(p: dict) -> tuple[dict, list[dict]]:
        org = p.get("org") or ""
        # Two angles per person: investment/funding and general recent activity.
        queries = [
            f"{p['name']} {org} funding investment round raised acquisition",
            f"{p['name']} {org} latest news 2026 2025 announcement",
        ]
        bundles = await asyncio.gather(*[
            search_and_read(q, max_results=6, read_top=2) for q in queries
        ])
        return p, bundles

    results = await asyncio.gather(*[_search_person(p) for p in people])
    notes: list[str] = []
    for p, bundles in results:
        chunks: list[str] = []
        for bundle in bundles:
            for s in bundle.get("sources", []):
                if s.get("url") and s["url"] not in seen:
                    seen.add(s["url"])
                    sources.append(s)
            for r in bundle.get("results", []):
                if r.get("content"):
                    chunks.append(f"[{r.get('title')}]({r.get('url')})\n{r['content'][:2000]}")
        notes.append(
            f"### PERSON {p['name']} (id={p['id']}, org={p.get('org', '')})\n"
            + "\n\n".join(chunks)[:6000]
        )
    joined = "\n\n---\n\n".join(notes)[:16000]

    system = (
        "You are an industry analyst tracking specific researchers/founders. From the "
        "per-person web notes, extract their capital-involvement and funding events and "
        "notable signals. Prefer the MOST RECENT events; widen the time window as needed "
        "(last months, then last 1–2 years) so you do not return empty results. Sort "
        "every list by date DESCENDING (most recent first) and include a 'date' "
        "(YYYY-MM or YYYY-MM-DD) whenever known. IMPORTANT: across capital + funding "
        "combined, return AT LEAST 3 events whenever the notes contain any plausible "
        "investment/funding/partnership/acquisition information for these people or "
        "their organisations; only return fewer if the notes truly contain none. "
        "Return JSON ONLY with keys: "
        '"person_signals":[{"person_id","person","title","summary","url","date"}], '
        '"capital":[{"person_id","person","target","round","amount","investors","url","date"}], '
        '"funding":[{"person_id","person","company","round","amount","url","date"}]. '
        "person_signals = notable activity/news; capital = investments the person/their "
        "org made or received; funding = funding rounds. Always set person_id to the id "
        "shown for that person. Do not fabricate; only use the notes. " + _lang_clause(question)
    )
    user = f"Question: {question}\n\nPer-person web notes:\n{joined}"
    raw = await _chat("report", system, user, temperature=0.2, max_tokens=2800)
    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        "person_signals": parsed.get("person_signals") or [],
        "capital": parsed.get("capital") or [],
        "funding": parsed.get("funding") or [],
        "sources": sources,
    }


async def _industry_analysis(question: str, report_body: str, scope: dict) -> dict:
    """Industry tracking, built on the generated report + the core people:

    - tech_signals & impact_md: one LLM interpretation of the report.
    - core_people: the DB core people (link to their wiki page).
    - person_signals / capital / funding: web search of each core person's recent
      (≈ last month) events.
    """
    core_people = scope.get("core_people") or []
    interp, events = await asyncio.gather(
        _interpret_report_signals(question, report_body),
        _track_people_events(question, core_people),
    )
    wiki = {p["id"]: p.get("wiki_url") for p in core_people if p.get("id")}
    for bucket in ("person_signals", "capital", "funding"):
        for it in events.get(bucket, []):
            if isinstance(it, dict) and it.get("person_id") in wiki:
                it["wiki_url"] = wiki[it["person_id"]]
    return {
        "core_people": core_people,
        "tech_signals": interp.get("tech_signals") or [],
        "impact_md": interp.get("impact_md") or "",
        "person_signals": events.get("person_signals") or [],
        "capital": events.get("capital") or [],
        "funding": events.get("funding") or [],
        "sources": events.get("sources") or [],
    }


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

    # Scope (DB topic/people mapping) first, then write report sections 1–3.
    progress("synthesis", "正在归纳技术路线类别与核心人物…", 80)
    scope = await _build_scope(question, brief, subtopics, kb_sources, blocks)

    progress("report", "正在撰写报告：执行摘要 / 技术路线 / 核心人物…", 88)
    report_core = await _write_report(question, brief, blocks, scope, all_sources, kb_sources)

    # Industry tracking is derived from the report (tech signals + impact) plus a web
    # search of each core person's recent capital/funding/signals.
    progress("report", "正在追踪核心人物的实时信号、资本与融资…", 94)
    industry = await _industry_analysis(question, report_core, scope)

    # Section 4 (产业追踪) is composed from the industry data so it matches the page.
    section4 = _compose_industry_section(industry)
    report = (
        report_core + "\n\n" + section4 + _build_references(kb_sources, all_sources)
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
