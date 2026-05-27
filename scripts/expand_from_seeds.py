#!/usr/bin/env python3
"""
Expand paper database via citation snowball from OpenAlex.

Strategy:
1. For each seed paper, search OpenAlex by title to get its Work ID
2. Fetch cited_by (papers that cite our seed) and references (papers our seed cites)
3. Filter by WM keywords in title
4. Output candidates as JSON for human review

Usage:
  python scripts/expand_from_seeds.py                  # dry run: output candidates
  python scripts/expand_from_seeds.py --apply          # write to DB after review
  python scripts/expand_from_seeds.py --max-seeds 20   # limit seeds processed
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

BASE_URL = "https://api.openalex.org"
HEADERS = {"User-Agent": "SignalPaperAnalysis/1.0 (mailto:product@miracleplus.com)"}

WM_KEYWORDS = [
    'world model', 'video generation', 'video prediction', 'video synthesis',
    'diffusion policy', 'vla', 'vision-language-action',
    'embodied', 'dreamer', 'jepa', 'latent dynamics',
    'robot control', 'action model', 'world simulator',
    'model-based reinforcement', 'model-based rl', 'imagination',
    'latent world', 'neural simulator', 'planning from pixels',
    'slot attention', 'object-centric',
    'sora', 'genie', 'cosmos', 'oasis',
    'diffuser', 'decision transformer',
]

YEAR_MIN = 2018
YEAR_MAX = 2026


def api_get(url: str, params: dict = None, retries: int = 3) -> dict | None:
    if params:
        query_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query_str}"
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            if attempt == retries - 1:
                print(f"  [ERROR] {e.code} for {url[:100]}")
                return None
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [ERROR] {e} for {url[:100]}")
                return None
            time.sleep(1)
    return None


def search_openalex_by_title(title: str, year: int) -> str | None:
    """Search OpenAlex for a paper by title, return Work ID or None."""
    params = {
        "search": title.replace(" ", "+"),
        "filter": f"publication_year:{max(year-1, 2015)}-{year+1}",
        "per-page": "3",
        "select": "id,title,publication_year,cited_by_count",
    }
    data = api_get(f"{BASE_URL}/works", params)
    if not data or not data.get("results"):
        return None
    for r in data["results"]:
        if abs(r.get("publication_year", 0) - year) <= 1:
            return r["id"].split("/")[-1]
    return data["results"][0]["id"].split("/")[-1] if data["results"] else None


def is_wm_relevant(title: str) -> bool:
    """Check if a paper title matches WM keywords."""
    t = title.lower()
    return any(kw in t for kw in WM_KEYWORDS)


def fetch_cited_by(work_id: str, per_page: int = 50) -> list[dict]:
    """Fetch papers that cite this work."""
    params = {
        "filter": f"cites:{work_id},publication_year:{YEAR_MIN}-{YEAR_MAX}",
        "sort": "cited_by_count:desc",
        "per-page": str(per_page),
        "select": "id,title,publication_year,cited_by_count,doi,authorships",
    }
    data = api_get(f"{BASE_URL}/works", params)
    if not data:
        return []
    return data.get("results", [])


def fetch_references_of(work_id: str) -> list[dict]:
    """Fetch referenced works metadata for a given work."""
    data = api_get(f"{BASE_URL}/works/{work_id}", {"select": "referenced_works"})
    if not data:
        return []
    ref_urls = data.get("referenced_works", [])
    if not ref_urls:
        return []
    ref_ids = [r.split("/")[-1] for r in ref_urls[:50]]
    pipe_filter = "|".join(f"https://openalex.org/{rid}" for rid in ref_ids)
    params = {
        "filter": f"openalex_id:{pipe_filter}",
        "per-page": "50",
        "select": "id,title,publication_year,cited_by_count,doi,authorships",
    }
    data2 = api_get(f"{BASE_URL}/works", params)
    if not data2:
        return []
    return data2.get("results", [])


def extract_first_author_org(work: dict) -> str:
    """Extract first author's institution."""
    authorships = work.get("authorships", [])
    if not authorships:
        return ""
    first = authorships[0]
    insts = first.get("institutions", [])
    if insts:
        return insts[0].get("display_name", "")
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-seeds", type=int, default=50)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", default="scripts/expand_candidates.json")
    args = parser.parse_args()

    from app.db import get_connection, init_db
    init_db()
    conn = get_connection()

    seeds = conn.execute(
        "SELECT id, title, full_title, year FROM papers ORDER BY impact_score DESC LIMIT ?",
        (args.max_seeds,)
    ).fetchall()
    print(f"Processing {len(seeds)} seed papers...")

    existing_titles = set()
    existing_short = set()
    for row in conn.execute("SELECT title, full_title FROM papers"):
        existing_titles.add(row["title"].lower().strip())
        existing_short.add(row["title"].lower().strip())
        if row["full_title"]:
            existing_titles.add(row["full_title"].lower().strip())

    def is_existing(title: str) -> bool:
        t = title.lower().strip()
        if t in existing_titles:
            return True
        for short in existing_short:
            if len(short) >= 4 and short in t:
                return True
        return False

    candidates = {}  # openalex_id -> info
    seed_map = {}  # openalex_id -> our paper id

    for i, seed in enumerate(seeds):
        title = seed["full_title"] or seed["title"]
        print(f"[{i+1}/{len(seeds)}] {seed['id']}: {title}")

        work_id = search_openalex_by_title(title, seed["year"])
        if not work_id:
            print(f"  -> not found on OpenAlex")
            continue

        seed_map[seed["id"]] = work_id
        time.sleep(0.15)

        # Fetch cited_by
        cited_by = fetch_cited_by(work_id, per_page=30)
        time.sleep(0.15)

        for w in cited_by:
            wid = w["id"].split("/")[-1]
            wtitle = w.get("title") or ""
            if is_existing(wtitle):
                continue
            if not is_wm_relevant(wtitle):
                continue
            yr = w.get("publication_year", 0)
            if yr < YEAR_MIN or yr > YEAR_MAX:
                continue
            if wid not in candidates:
                candidates[wid] = {
                    "openalex_id": wid,
                    "title": wtitle,
                    "year": yr,
                    "cited_by_count": w.get("cited_by_count", 0),
                    "doi": w.get("doi"),
                    "org": extract_first_author_org(w),
                    "found_via": [],
                }
            candidates[wid]["found_via"].append(f"cites:{seed['id']}")

        # Fetch references (papers this seed cites)
        refs = fetch_references_of(work_id)
        time.sleep(0.15)

        for w in refs:
            wid = w["id"].split("/")[-1]
            wtitle = w.get("title") or ""
            if is_existing(wtitle):
                continue
            if not is_wm_relevant(wtitle):
                continue
            yr = w.get("publication_year", 0)
            if yr < YEAR_MIN or yr > YEAR_MAX:
                continue
            if wid not in candidates:
                candidates[wid] = {
                    "openalex_id": wid,
                    "title": wtitle,
                    "year": yr,
                    "cited_by_count": w.get("cited_by_count", 0),
                    "doi": w.get("doi"),
                    "org": extract_first_author_org(w),
                    "found_via": [],
                }
            candidates[wid]["found_via"].append(f"ref_of:{seed['id']}")

    conn.close()

    # Sort by citations desc
    sorted_candidates = sorted(candidates.values(), key=lambda x: x["cited_by_count"], reverse=True)

    print(f"\n{'='*60}")
    print(f"Found {len(sorted_candidates)} candidate papers")
    print(f"{'='*60}")

    # Print top 30
    for i, c in enumerate(sorted_candidates[:30]):
        vias = ", ".join(set(c["found_via"][:3]))
        print(f"  {i+1:3d}. [{c['year']}] {c['title'][:60]}")
        print(f"       citations={c['cited_by_count']:,}  org={c['org'][:30]}  via={vias}")

    if len(sorted_candidates) > 30:
        print(f"  ... and {len(sorted_candidates) - 30} more")

    # Save full list
    output_path = Path(__file__).parent / Path(args.output).name
    with open(output_path, "w") as f:
        json.dump(sorted_candidates, f, indent=2, ensure_ascii=False)
    print(f"\nFull list saved to: {output_path}")
    print("Review the file, then run with --apply to import selected papers.")


if __name__ == "__main__":
    main()
