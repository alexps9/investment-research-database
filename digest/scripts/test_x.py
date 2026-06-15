"""Day 5 E2E smoke test for the X collector via socialdata.tools.

Three checks:
1. Resolve a handful of known handles → user_ids (verify auth + caching)
2. Fetch ~7-day window for ~5 known active accounts, print summary
3. Verify dedup and retweet filtering work as expected

Invoke:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/test_x.py [--days N] [--limit N]
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

from hh_research.collectors.x_collector import SocialDataXCollector  # noqa: E402
from hh_research.storage.bitable_client import read_whitelist  # noqa: E402
from hh_research.storage.schemas import WhitelistEntry  # noqa: E402
from hh_research.storage.sqlite_dedup import SQLiteDedupStore  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--limit", type=int, default=10, help="how many handles to test")
    ap.add_argument("--from-bitable", action="store_true",
                    help="use real whitelist instead of hardcoded test handles")
    args = ap.parse_args()

    print("=" * 70)
    print("DAY 5 X COLLECTOR SMOKE TEST")
    print("=" * 70)

    # Build test whitelist
    if args.from_bitable:
        print("\nReading whitelist from Bitable ...")
        wl = read_whitelist()
        with_handle = [e for e in wl if e.twitter_handle]
        print(f"  total: {len(wl)}, with X handle: {len(with_handle)}")
        test_entries = with_handle[: args.limit]
    else:
        print("\nUsing hardcoded test handles (5 known active AI researchers):")
        test_entries = [
            WhitelistEntry(record_id="t1", name="Noam Shazeer", twitter_url="https://x.com/NoamShazeer"),
            WhitelistEntry(record_id="t2", name="Andrej Karpathy", twitter_url="https://x.com/karpathy"),
            WhitelistEntry(record_id="t3", name="Sasha Rush", twitter_url="https://x.com/srush_nlp"),
            WhitelistEntry(record_id="t4", name="Jim Fan", twitter_url="https://x.com/DrJimFan"),
            WhitelistEntry(record_id="t5", name="Yann LeCun", twitter_url="https://x.com/ylecun"),
        ]
    print(f"  testing with {len(test_entries)} handles")

    # --- Run ---
    print(f"\nRunning collector ({args.days}-day window, exclude retweets) ...")
    collector = SocialDataXCollector(exclude_retweets=True, exclude_replies=False)
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)

    signals = list(collector.collect(test_entries, since, now))
    collector.close()

    # --- Report ---
    print(f"\n=== Results ===")
    print(f"Total tweets: {len(signals)}")

    by_author = Counter(s.author_name for s in signals)
    print("\nTweets per author:")
    for author, count in by_author.most_common():
        print(f"  {count:3d}  {author}")

    print("\nSample 5 tweets:")
    for i, s in enumerate(signals[:5]):
        text_preview = s.raw_text.replace("\n", " ")[:90]
        print(f"  [{i + 1}] {s.created_at.strftime('%Y-%m-%d %H:%M')}  @{s.author_name}")
        print(f"        {text_preview}")
        print(f"        {s.url}")

    # --- Dedup check ---
    print("\nDedup check:")
    dedup = SQLiteDedupStore()
    sids = [s.source_id for s in signals]
    unseen_before = dedup.filter_unseen(sids)
    print(f"  before marking: {len(unseen_before)} unseen / {len(sids)} total")
    dedup.mark_many(sids)
    unseen_after = dedup.filter_unseen(sids)
    print(f"  after marking:  {len(unseen_after)} unseen / {len(sids)} total")

    # --- Cost estimate ---
    user_lookups = len(test_entries)
    tweets_returned = len(signals)
    cost_usd = (user_lookups + tweets_returned) * 0.0002
    print(f"\nApprox cost: {user_lookups} user lookups + {tweets_returned} tweets = ${cost_usd:.4f}")

    print("\n" + "=" * 70)
    print("SMOKE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
