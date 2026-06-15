from datetime import UTC, datetime

import httpx

from hh_research.collectors.rss_collector import RssCollector
from hh_research.storage.schemas import WhitelistEntry


def test_rss_collect_links_feed_to_whitelist_record_id_by_name(tmp_path, monkeypatch):
    feeds_path = tmp_path / "rss_feeds.yaml"
    feeds_path.write_text(
        """
feeds:
  - name: SemiAnalysis Blog
    whitelist_name: SemiAnalysis
    url: https://semianalysis.com/feed
    category: media
""".strip(),
        encoding="utf-8",
    )
    feed_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>SemiAnalysis</title>
  <entry>
    <title>GB200 supply chain update</title>
    <link href="https://semianalysis.com/example"/>
    <updated>2026-06-09T01:00:00Z</updated>
    <summary>Important accelerator market update.</summary>
  </entry>
</feed>
"""
    collector = RssCollector(feeds_path=feeds_path)
    monkeypatch.setattr(
        collector,
        "_fetch_feed_inner",
        lambda url: httpx.Response(200, content=feed_xml),
    )

    signals = list(
        collector.collect(
            [WhitelistEntry(record_id="rec_semi", name="SemiAnalysis", tier="P0+")],
            datetime(2026, 6, 9, tzinfo=UTC),
            datetime(2026, 6, 10, tzinfo=UTC),
        )
    )

    assert len(signals) == 1
    assert signals[0].author_name == "SemiAnalysis Blog"
    assert signals[0].author_record_id == "rec_semi"
