"""Enrich the whitelist with arXiv search URLs + OpenAlex-validated profile URLs.

Strategy:
  1. For every whitelist entry: construct an arXiv search URL by name
     (always populated, format `?searchtype=author&query=...`).
  2. Query OpenAlex API by name; among candidates, score each by:
       - topic relevance (CS/AI keywords)        +50
       - affiliation match vs whitelist.org      +40
       - works_count >= 20                       +20
       - has ORCID                               +10
       - irrelevant topics (Medicine, Physics)   -30
     Pick the top candidate; if score >= 80 → "verified"; >= 50 → "ambiguous"; else → "no_match".
  3. Write back to Bitable:
       - arxiv_homepage_url = arxiv search URL (always)
       - openalex_url = OpenAlex author URL (only when verified)

OpenAlex API is free; we add User-Agent + email for the "polite pool".

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/enrich_arxiv_validation.py --probe          # 10 entries, no write
    .venv/bin/python scripts/enrich_arxiv_validation.py --dry-run        # all entries, no write
    .venv/bin/python scripts/enrich_arxiv_validation.py --apply          # all entries + write to Bitable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.storage.bitable_client import read_whitelist  # noqa: E402

UA = {"User-Agent": "HH Research Pipeline; mailto:goalin040302@gmail.com"}

CS_AI_TOPICS = {
    "computer science", "artificial intelligence", "machine learning",
    "deep learning", "natural language processing", "computer vision",
    "pattern recognition", "data mining", "neural networks",
    "reinforcement learning", "robotics",
}
IRRELEVANT_TOPICS = {
    "medicine", "biology", "materials science", "physics", "chemistry",
    "geology", "atmospheric sciences", "meteorology", "oncology",
    "psychology", "economics",
}

# Whitelist.organization → broader affiliation regex (loose match)
ORG_ALIASES: dict[str, list[str]] = {
    "Google": ["google", "deepmind", "alphabet"],
    "Meta": ["meta", "facebook", "fair "],
    "OpenAI": ["openai", "open ai"],
    "Microsoft": ["microsoft", "msr"],
    "NVIDIA": ["nvidia"],
    "Apple": ["apple"],
    "Anthropic": ["anthropic"],
    "xAI": ["xai", "x.ai"],
    "Stanford": ["stanford"],
    "MIT": ["massachusetts institute", "mit"],
    "Berkeley": ["berkeley", "uc berkeley"],
    "UCB": ["berkeley", "uc berkeley"],
    "CMU": ["carnegie mellon", "cmu"],
    "NYU": ["new york university", "courant"],
    "UCSD": ["san diego", "ucsd"],
    "Princeton": ["princeton"],
    "Tsinghua": ["tsinghua", "清华"],
    "CUHK": ["chinese university of hong kong"],
    "NUS": ["national university of singapore"],
    "Cornell": ["cornell"],
    "Caltech": ["california institute of technology"],
    "Harvard": ["harvard"],
    "Cambridge": ["cambridge"],
    "Yale": ["yale"],
    "UW": ["washington"],
    "UMD": ["maryland"],
    "UIUC": ["illinois", "uiuc"],
    "GT": ["georgia tech"],
}


def construct_arxiv_search_url(name: str) -> str:
    """Build a clean arXiv author search URL."""
    return f"https://arxiv.org/search/?searchtype=author&query={urllib.parse.quote_plus(name)}&start=0"


def score_candidate(c: dict, target_org: str | None) -> tuple[int, dict]:
    """Score one OpenAlex author candidate. Returns (score, debug_info).

    debug includes 'affiliation_match' flag — used as a HARD gate for `verified`
    status (because affiliation is the only reliable disambiguator).
    """
    score = 0
    debug = {"topic_match": False, "affiliation_match": False,
             "works": 0, "orcid": False, "irrelevant_topics": False}

    # Topic relevance
    concepts = c.get("x_concepts") or []
    topic_names = [t.get("display_name", "").lower() for t in concepts[:5]]
    if any(t in CS_AI_TOPICS for t in topic_names):
        score += 50
        debug["topic_match"] = True
    if any(t in IRRELEVANT_TOPICS for t in topic_names):
        score -= 50  # strong penalty (was -30)
        debug["irrelevant_topics"] = True

    # Affiliation match
    li = c.get("last_known_institutions") or c.get("last_known_institution") or []
    if isinstance(li, dict):
        li = [li]
    institutions = [(inst.get("display_name") or "").lower() for inst in li if isinstance(inst, dict)]
    if target_org:
        aliases = ORG_ALIASES.get(target_org, [target_org.lower()])
        for inst_name in institutions:
            if any(a in inst_name for a in aliases):
                score += 40
                debug["affiliation_match"] = True
                break

    # Works count
    works = c.get("works_count", 0)
    debug["works"] = works
    if works >= 20:
        score += 20
    elif works >= 5:
        score += 10

    # ORCID
    if c.get("orcid"):
        score += 10
        debug["orcid"] = True

    return score, debug


def verify_with_openalex(name: str, target_org: str | None, client: httpx.Client) -> dict:
    """Search OpenAlex by name; return best match info."""
    try:
        resp = client.get(
            "https://api.openalex.org/authors",
            params={"search": name, "per-page": 5, "select": (
                "id,display_name,works_count,cited_by_count,orcid,"
                "last_known_institutions,x_concepts"
            )},
            headers=UA,
            timeout=15.0,
        )
        if resp.status_code != 200:
            return {"status": "api_error", "error": f"HTTP {resp.status_code}"}
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}

    candidates = data.get("results", [])
    if not candidates:
        return {"status": "no_match"}

    # Score each candidate
    scored = []
    for c in candidates:
        score, dbg = score_candidate(c, target_org)
        scored.append((score, c, dbg))
    scored.sort(key=lambda x: -x[0])

    top_score, top, top_dbg = scored[0]
    top_url = top.get("id", "")

    # Verified requires affiliation match — no exceptions.
    # This is the only reliable disambiguator for common names.
    if top_dbg.get("affiliation_match") and top_score >= 80:
        status = "verified"
    elif top_score >= 60 and not top_dbg.get("irrelevant_topics"):
        status = "ambiguous"
    else:
        status = "no_match"

    li = top.get("last_known_institutions") or [{}]
    if isinstance(li, dict):
        li = [li]
    li_name = (li[0].get("display_name") if li else "") or ""

    return {
        "status": status,
        # Only save openalex_url when we have affiliation-grounded confidence
        "openalex_url": top_url if status == "verified" else None,
        "score": top_score,
        "matched_name": top.get("display_name", ""),
        "matched_institution": li_name,
        "works_count": top.get("works_count", 0),
        "candidate_count": len(candidates),
        "debug": top_dbg,
    }


def write_back(record_id: str, patch: dict[str, str]) -> tuple[bool, str]:
    """Write fields to one Bitable record."""
    payload = {"patch": patch, "record_id_list": [record_id]}
    rel_tmp = "./data/_tmp_arxiv_patch.json"
    Path(rel_tmp).parent.mkdir(parents=True, exist_ok=True)
    Path(rel_tmp).write_text(json.dumps(payload, ensure_ascii=False))

    cmd = [
        "lark-cli", "--profile", "personal",
        "base", "+record-batch-update",
        "--base-token", os.environ["HH_BITABLE_APP_TOKEN"],
        "--table-id", os.environ["HH_WHITELIST_TABLE_ID"],
        "--json", f"@{rel_tmp}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return False, r.stderr[:200]
    try:
        resp = json.loads(r.stdout)
        if resp.get("ok"):
            return True, "ok"
        return False, str(resp.get("error", "unknown"))[:200]
    except json.JSONDecodeError:
        return False, "non-json response"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="test on 10 entries, no write")
    ap.add_argument("--dry-run", action="store_true", help="all entries, no write")
    ap.add_argument("--apply", action="store_true", help="all entries + write to Bitable")
    ap.add_argument("--limit", type=int, default=0, help="cap number of entries (debug)")
    args = ap.parse_args()

    if not (args.probe or args.dry_run or args.apply):
        print("Pick one mode: --probe / --dry-run / --apply")
        sys.exit(1)

    print("Reading whitelist ...")
    wl = read_whitelist()
    persons = [e for e in wl if e.name and not (e.organization and e.organization.strip() == e.name.strip())]
    print(f"  total: {len(wl)}, persons (excl. orgs): {len(persons)}")

    if args.probe:
        targets = persons[:10]
    elif args.limit > 0:
        targets = persons[: args.limit]
    else:
        targets = persons

    print(f"  validating {len(targets)} entries via OpenAlex ...\n")

    results = []
    counts = {"verified": 0, "ambiguous": 0, "no_match": 0, "error": 0}

    with httpx.Client() as client:
        for i, entry in enumerate(targets):
            arxiv_url = construct_arxiv_search_url(entry.name)
            res = verify_with_openalex(entry.name, entry.organization, client)
            status = res.get("status", "error")
            counts[status] = counts.get(status, 0) + 1

            score = res.get("score", 0)
            inst = res.get("matched_institution") or "?"
            works = res.get("works_count", 0)
            tag = (
                f"[{status:9s}] score={score:3d} works={works:5d} "
                f"@ {inst[:30]:30s}"
            )
            print(f"  [{i+1}/{len(targets)}] {entry.name[:30]:30s} {tag}")

            results.append({
                "record_id": entry.record_id,
                "name": entry.name,
                "organization": entry.organization,
                "arxiv_homepage_url": arxiv_url,
                "openalex_url": res.get("openalex_url"),
                "openalex_status": status,
                "openalex_score": score,
                "matched_institution": inst,
                "works_count": works,
            })

            # Be polite to OpenAlex (recommended ~10 req/sec for polite pool, we go 5)
            time.sleep(0.2)

            # Checkpoint every 30
            if (i + 1) % 30 == 0:
                Path("data/arxiv_validation_result.json").write_text(
                    json.dumps(results, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    # Final save
    out_path = Path("data/arxiv_validation_result.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Validation stats ===")
    for k, v in counts.items():
        pct = (v / len(targets) * 100) if targets else 0
        print(f"  {k:10s} {v:3d}/{len(targets)} ({pct:.0f}%)")
    print(f"\nFull result saved to: {out_path}")

    if args.apply:
        print(f"\n=== Writing to Bitable ===")
        ok_count, fail_count = 0, 0
        for i, r in enumerate(results):
            patch = {"arxiv_homepage_url": r["arxiv_homepage_url"]}
            if r.get("openalex_url"):
                patch["openalex_url"] = r["openalex_url"]
            ok, msg = write_back(r["record_id"], patch)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                print(f"  [{i+1}] {r['name']}: FAIL {msg}")
            if (i + 1) % 30 == 0:
                print(f"  ... {i+1}/{len(results)} written, ok={ok_count} fail={fail_count}")
            time.sleep(0.25)

        try:
            Path("./data/_tmp_arxiv_patch.json").unlink()
        except FileNotFoundError:
            pass

        print(f"\nDone: ok={ok_count}, fail={fail_count}")


if __name__ == "__main__":
    main()
