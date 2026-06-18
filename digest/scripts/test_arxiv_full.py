"""Full-whitelist smoke test.

Reads the 246 whitelist entries from Bitable, runs arXiv collector over a
7-day window, reports counts and distribution.

This is a CAUTIOUS test — it makes ~226 arXiv API calls (one per filled author
query) with ~3s delay each → ~11 min. Run only when you have time.

Invoke:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/test_arxiv_full.py [--days N]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.collectors.arxiv_collector import ArxivCollector  # noqa: E402
from hh_research.storage.bitable_client import read_whitelist  # noqa: E402
from hh_research.storage.sqlite_dedup import SQLiteDedupStore  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="Window size in days (default 7)")
    ap.add_argument("--limit-authors", type=int, default=0,
                    help="If > 0, use only first N whitelist entries (for quick testing)")
    args = ap.parse_args()

    print(f"Reading whitelist ...")
    wl = read_whitelist()
    filled = [e for e in wl if e.arxiv_author_query]
    print(f"  total: {len(wl)}, with arxiv_author_query: {len(filled)}")

    if args.limit_authors > 0:
        filled = filled[: args.limit_authors]
        print(f"  limited to first {len(filled)} for quick test")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)
    print(f"\nWindow: {since.date()} -> {now.date()} ({args.days} days)")
    print(f"Running arXiv collector (this may take ~{len(filled) * 3 // 60} min due to rate limiting) ...\n")

    collector = ArxivCollector()
    signals = list(collector.collect(filled, since, now))

    print(f"\n=== Results ===")
    print(f"Total papers: {len(signals)}")

    # Papers per author
    author_counter = Counter(s.author_name for s in signals)
    top_authors = author_counter.most_common(10)
    print("\nTop 10 most-publishing authors in window:")
    for author, count in top_authors:
        print(f"  {count:3d}  {author}")

    # Show 5 sample papers
    print("\nSample 5 papers:")
    for i, sig in enumerate(signals[:5]):
        title = sig.raw_text.splitlines()[0]
        print(f"  [{i + 1}] {sig.created_at.date()}  {sig.author_name}")
        print(f"        {title[:100]}")
        print(f"        {sig.url}")

    # Dedup check
    dedup = SQLiteDedupStore()
    unseen = dedup.filter_unseen([s.source_id for s in signals])
    print(f"\nDedup: {len(unseen)} of {len(signals)} are new (haven't been seen in prior runs)")


if __name__ == "__main__":
    main()
