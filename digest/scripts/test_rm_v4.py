"""Manual debug entry: 跑单篇 arxiv 论文的 V4 RM enrich，打印结果。

Usage:
  .venv/bin/python scripts/test_rm_v4.py <arxiv_id>

例:
  .venv/bin/python scripts/test_rm_v4.py 2605.18603
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.extract.author_enricher import enrich_paper_coauthors, get_arxiv_full_authors  # noqa: E402
from hh_research.storage.bitable_client import read_whitelist  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    arxiv_id = sys.argv[1]
    print(f"fetching arxiv {arxiv_id} authors ...")
    authors = get_arxiv_full_authors(arxiv_id)
    print(f"  → {len(authors)} authors: {authors}")

    print("loading whitelist from Bitable ...")
    try:
        wl_entries = read_whitelist()
    except Exception as e:  # noqa: BLE001
        print(f"  ! whitelist read failed: {e}; proceeding without")
        wl_entries = []
    wl_match = {e.name: e for e in wl_entries if e.name and e.name in set(authors)}
    print(f"  → {len(wl_match)} whitelist matches")

    print("running V4 enrich ...")
    coauthors = enrich_paper_coauthors(
        arxiv_id=arxiv_id,
        authors=authors,
        whitelist_match=wl_match,
    )
    print(f"\n=== {len(coauthors)} authors enriched ===\n")
    for c in coauthors:
        print(json.dumps(c.model_dump(exclude_none=False), ensure_ascii=False, indent=2))
        print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
