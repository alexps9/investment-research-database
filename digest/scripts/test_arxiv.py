"""Day 2 E2E smoke test for the arXiv collector.

Runs three checks:
1. Read whitelist from Bitable → confirm 246 entries
2. Pick a few known authors, build ad-hoc WhitelistEntry objects, run collector
3. Verify SQLiteDedupStore filters duplicates on rerun

Invoke:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/test_arxiv.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src/ to path so we can import without pip install -e
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.collectors.arxiv_collector import ArxivCollector  # noqa: E402
from hh_research.storage.bitable_client import read_whitelist  # noqa: E402
from hh_research.storage.schemas import WhitelistEntry  # noqa: E402
from hh_research.storage.sqlite_dedup import SQLiteDedupStore  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("DAY 2 ARXIV SMOKE TEST")
    print("=" * 70)

    # --- Check 1: read whitelist ---
    print("\n[1] Reading whitelist from Bitable ...")
    wl = read_whitelist()
    print(f"    Got {len(wl)} whitelist entries")
    with_query = [e for e in wl if e.arxiv_author_query]
    with_regex = [e for e in wl if e.affiliation_regex]
    print(f"    With arxiv_author_query: {len(with_query)}")
    print(f"    With affiliation_regex:  {len(with_regex)}")
    if wl:
        sample = wl[0]
        print(f"    Sample entry: {sample.name} (org={sample.organization}, cat={sample.category})")

    # --- Check 2: ad-hoc test with known authors ---
    # Use a 365-day window since senior researchers may not publish every month.
    # For the production daily pipeline, window will be 1 day.
    print("\n[2] Running collector with 5 ad-hoc test authors (last 365 days) ...")
    test_authors = [
        WhitelistEntry(record_id="t1", name="Noam Shazeer", arxiv_author_query='au:"Noam Shazeer"'),
        WhitelistEntry(record_id="t2", name="Percy Liang", arxiv_author_query='au:"Percy Liang"'),
        WhitelistEntry(record_id="t3", name="Sasha Rush", arxiv_author_query='au:"Alexander Rush"'),
        WhitelistEntry(record_id="t4", name="Chelsea Finn", arxiv_author_query='au:"Chelsea Finn"'),
        WhitelistEntry(record_id="t5", name="Tri Dao", arxiv_author_query='au:"Tri Dao"'),
    ]
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=365)
    collector = ArxivCollector()

    signals = list(collector.collect(test_authors, since, now))
    print(f"    Fetched {len(signals)} papers total")
    for i, sig in enumerate(signals[:5]):
        print(f"    [{i + 1}] {sig.created_at.date()}  {sig.author_name}")
        print(f"        title: {sig.raw_text.splitlines()[0][:110]}")
        print(f"        url:   {sig.url}")
        print(f"        sid:   {sig.source_id}")

    # --- Check 3: dedup ---
    print("\n[3] Testing SQLite DedupStore ...")
    dedup = SQLiteDedupStore()
    sids = [s.source_id for s in signals]
    unseen_before = dedup.filter_unseen(sids)
    print(f"    Before marking: {len(unseen_before)} unseen / {len(sids)} total")
    dedup.mark_many(sids)
    unseen_after = dedup.filter_unseen(sids)
    print(f"    After marking:  {len(unseen_after)} unseen / {len(sids)} total")
    print(f"    DedupStore row count: {dedup.count()}")

    print("\n" + "=" * 70)
    print("SMOKE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
