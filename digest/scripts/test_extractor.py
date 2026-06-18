"""Smoke test the signal extractor on real arXiv papers.

Goals:
1. Verify tool_use returns valid structured JSON
2. Verify prompt caching works (cache_read_tokens > 0 on call 2+)
3. Verify Chinese summary + English term preservation quality
4. Confirm cost is in expected range

Invoke:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/test_extractor.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.collectors.arxiv_collector import ArxivCollector  # noqa: E402
from hh_research.extract.signal_extractor import SignalExtractor  # noqa: E402
from hh_research.storage.schemas import WhitelistEntry  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("EXTRACTOR SMOKE TEST (Bedrock Sonnet 4.6)")
    print("=" * 70)

    print("\n[1] Fetching 3 recent papers from active AI researchers ...")
    test_authors = [
        WhitelistEntry(record_id="t1", name="Tri Dao", arxiv_author_query='au:"Tri Dao"'),
        WhitelistEntry(record_id="t2", name="Percy Liang", arxiv_author_query='au:"Percy Liang"'),
        WhitelistEntry(record_id="t3", name="Chelsea Finn", arxiv_author_query='au:"Chelsea Finn"'),
    ]
    collector = ArxivCollector()
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=180)  # wider window to ensure we get papers
    signals = list(collector.collect(test_authors, since, now))
    signals = signals[:3]  # cap at 3 for cost
    print(f"    got {len(signals)} papers")
    for i, s in enumerate(signals):
        print(f"    [{i+1}] {s.author_name}: {s.raw_text.splitlines()[0][:80]}")

    if not signals:
        print("\n!!! No papers found, cannot run extraction. Try wider window.")
        return

    print(f"\n[2] Running extractor on {len(signals)} papers ...")
    extractor = SignalExtractor()
    extracted = extractor.extract_many(signals)

    print(f"\n[3] Cost summary:")
    print(f"    {extractor.cost.summary()}")
    print(f"    cache_read / cache_write / fresh-input: "
          f"{extractor.cost.cache_read_tokens} / "
          f"{extractor.cost.cache_write_tokens} / "
          f"{extractor.cost.input_tokens}")
    if extractor.cost.cache_read_tokens > 0:
        print(f"    ✅ Prompt caching is working (saved on calls 2+)")
    elif len(extracted) > 1:
        print(f"    ⚠️  No cache reads detected — caching may not have engaged")
    else:
        print(f"    (need 2+ calls to verify caching)")

    print(f"\n[4] Extracted output (per paper):")
    for i, s in enumerate(extracted):
        print(f"\n  --- [{i+1}] {s.author_name} ---")
        print(f"  title: {s.raw_text.splitlines()[0][:100]}")
        print(f"  category:    {s.category} / {s.subcategory}")
        print(f"  summary_zh:  {s.summary_zh}")
        if s.highlights_zh:
            print(f"  highlights:")
            for h in s.highlights_zh:
                print(f"    • {h}")
        print(f"  key_terms:   {s.key_terms}")
        print(f"  novelty:     {s.novelty_score}")
        if s.investment_relevance:
            print(f"  investment:  {s.investment_relevance}")
        print(f"  needs_review: {s.needs_human_review}")

    print("\n" + "=" * 70)
    print("EXTRACTOR SMOKE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
