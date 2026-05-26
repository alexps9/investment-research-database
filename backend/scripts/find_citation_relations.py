"""
MVP: 自动找新论文与库内论文的引用关系 + 分类（inherits/competes/borrows）

使用方式：
  python scripts/find_citation_relations.py <paper_title_or_id>

流程：
  1. 用 Semantic Scholar 搜论文，拿到 references 列表
  2. 和我们库（world-model-data.json）做 intersection
  3. 对命中的引用，拿 citation context + intent
  4. Level 1: SS intent 直接映射 (methodology→inherits, result_comparison→competes)
  5. Level 2: 关键词规则 on citation context
  6. 输出建议的 connections

无需 API key（Semantic Scholar 免费额度 100 req/5min）
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx

SS_BASE = "https://api.semanticscholar.org/graph/v1"
SS_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
DATA_PATH = Path(__file__).parent.parent.parent / "frontend" / "src" / "data" / "world-model-data.json"

KEYWORD_RULES_ORDERED = [
    ("competes", [
        "outperform", "outperforms", "unlike", "in contrast to", "compared to",
        "surpass", "surpasses", "superior to", "alternative to",
    ]),
    ("borrows", [
        "inspired by", "similar to", "adopt the", "borrow", "borrows",
        "incorporate", "incorporates", "draw from", "draws from", "drawing from",
    ]),
    ("inherits", [
        "build upon", "builds upon", "built upon", "extend", "extends", "extending",
        "follow", "follows", "following the", "based on", "leverage", "leverages",
        "adopt", "adopts", "use the framework", "fine-tune", "finetune",
    ]),
]


def load_library():
    with open(DATA_PATH) as f:
        data = json.load(f)
    papers = data["papers"]
    title_to_id = {}
    for p in papers:
        title_to_id[p["title"].lower()] = p["id"]
        title_to_id[p["id"].lower()] = p["id"]
    return papers, title_to_id


import re

# Map from common full titles (as they appear on SS) to our library IDs
TITLE_ALIASES = {
    "learning latent dynamics for planning from pixels": "planet",
    "dream to control: learning behaviors by latent imagination": "dreamer_v1",
    "mastering atari with discrete world models": "dreamer_v2",
    "mastering diverse domains through world models": "dreamer_v3",
    "video generation models as world simulators": "sora",
    "scaling rectified flow transformers for high-resolution image synthesis": "sora",
    "genie: generative interactive environments": "genie2",
    "temporal difference learning for model predictive control": "tdmpc",
    "td-mpc2: scalable, robust world models for continuous control": "tdmpc2",
    "diffusion policy: visuomotor policy learning via action diffusion": "diffusion_policy",
}


def fuzzy_match_library(cited_title: str, title_to_id: dict, papers: list) -> str | None:
    lower = cited_title.lower()
    if lower in title_to_id:
        return title_to_id[lower]
    if lower in TITLE_ALIASES:
        return TITLE_ALIASES[lower]
    # Match on prefix before colon (e.g. "Cosmos" matches "Cosmos World Foundation...")
    cited_prefix = lower.split(":")[0].strip()
    for p in papers:
        short = p["title"].lower()
        prefix = short.split(":")[0].strip()
        if len(prefix) >= 5 and prefix == cited_prefix:
            return p["id"]
    # Word-boundary substring match for longer titles
    for p in papers:
        short = p["title"].lower()
        if len(short) >= 8 and re.search(r'\b' + re.escape(short) + r'\b', lower):
            return p["id"]
    return None


def ss_get(url: str, params: dict, max_retries: int = 3) -> httpx.Response | None:
    headers = {"x-api-key": SS_API_KEY} if SS_API_KEY else {}
    for attempt in range(max_retries):
        r = httpx.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            return r
        if r.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  Rate limited, waiting {wait}s...{' (set SEMANTIC_SCHOLAR_API_KEY for higher limits)' if not SS_API_KEY else ''}")
            time.sleep(wait)
            continue
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
        return None
    print(f"  Failed after {max_retries} retries")
    return None


def search_paper(query: str) -> dict | None:
    url = f"{SS_BASE}/paper/search"
    params = {"query": query, "fields": "paperId,title,references", "limit": 1}
    r = ss_get(url, params)
    if not r:
        return None
    data = r.json()
    if not data.get("data"):
        print(f"  No results for: {query}")
        return None
    return data["data"][0]


def get_paper_references(paper_id: str) -> list[dict]:
    url = f"{SS_BASE}/paper/{paper_id}/references"
    params = {"fields": "paperId,title,contexts,intents", "limit": 100}
    r = ss_get(url, params)
    if not r:
        return []
    return r.json().get("data", [])


def classify_intent(intents: list[str], contexts: list[str]) -> str:
    for intent in intents:
        if intent == "methodology":
            return "inherits"
        if intent == "result_comparison":
            return "competes"

    context_text = " ".join(contexts).lower()
    for rel_type, keywords in KEYWORD_RULES_ORDERED:
        for kw in keywords:
            if kw in context_text:
                return rel_type

    return "inherits"


def find_relations(query: str):
    print(f"\n{'='*60}")
    print(f"Finding citation relations for: {query}")
    print(f"{'='*60}\n")

    papers, title_to_id = load_library()
    print(f"Library: {len(papers)} papers loaded")

    print(f"\n[1/3] Searching Semantic Scholar...")
    result = search_paper(query)
    if not result:
        return

    paper_id = result["paperId"]
    print(f"  Found: {result['title']} (SS ID: {paper_id})")

    print(f"\n[2/3] Fetching references...")
    time.sleep(1)
    refs = get_paper_references(paper_id)
    if not refs:
        print("  No references found (paper may not be fully indexed)")
        return
    print(f"  Got {len(refs)} references")

    print(f"\n[3/3] Matching against library...")
    matches = []
    for ref in refs:
        cited = ref.get("citedPaper", {})
        if not cited or not cited.get("title"):
            continue
        lib_id = fuzzy_match_library(cited["title"], title_to_id, papers)
        if lib_id:
            intents = ref.get("intents") or []
            contexts = ref.get("contexts") or []
            rel_type = classify_intent(intents, contexts)
            matches.append({
                "target": lib_id,
                "type": rel_type,
                "title": cited["title"],
                "intents": intents,
                "context_preview": (contexts[0][:120] + "...") if contexts else "",
            })

    if not matches:
        print("  No matches found in library.")
        print("  Tip: paper may use different title variants or not cite our papers directly.")
        return

    print(f"\n  Found {len(matches)} connections to library papers:\n")
    print(f"  {'Type':<10} {'Target':<25} {'Title':<40} {'Evidence'}")
    print(f"  {'-'*10} {'-'*25} {'-'*40} {'-'*30}")
    for m in matches:
        print(f"  {m['type']:<10} {m['target']:<25} {m['title'][:38]:<40} {m['context_preview'][:30]}")

    print(f"\n\n  JSON (copy to data):")
    json_out = [{"target": m["target"], "type": m["type"]} for m in matches]
    print(f"  \"connections\": {json.dumps(json_out, indent=4)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_citation_relations.py <paper_title_or_query>")
        print("Example: python scripts/find_citation_relations.py 'DreamDojo'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    find_relations(query)
