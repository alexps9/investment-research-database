from __future__ import annotations

from datetime import datetime, timezone

from hh_research.collectors.arxiv_collector import (
    ArxivCollector,
    _html_announced_datetime,
    _parse_arxiv_abs_html,
    _parse_arxiv_list_html,
)
from hh_research.storage.schemas import WhitelistEntry


LIST_HTML = """
<html>
  <body>
    <h3>Wed, 20 May 2026 (showing 312 of 312 entries )</h3>
    <dl id="articles">
      <dt>
        <a href="/abs/2605.12345" title="Abstract">arXiv:2605.12345</a>
      </dt>
      <dd>
        <div class="meta">
          <div class="list-title mathjax">
            <span class="descriptor">Title:</span>
            A Careful Agent Benchmark
          </div>
          <div class="list-authors">
            <span class="descriptor">Authors:</span>
            <a href="/search/cs?searchtype=author&amp;query=Li%2C+Ada">Ada Li</a>,
            <a href="/search/cs?searchtype=author&amp;query=Chen%2C+Bo">Bo Chen</a>
          </div>
          <div class="list-subjects">
            <span class="descriptor">Subjects:</span> Artificial Intelligence (cs.AI)
          </div>
        </div>
      </dd>
    </dl>
  </body>
</html>
"""


ABS_HTML = """
<html>
  <body>
    <h1 class="title mathjax"><span class="descriptor">Title:</span>A Careful Agent Benchmark</h1>
    <blockquote class="abstract mathjax">
      <span class="descriptor">Abstract:</span>
      We introduce a benchmark for long-horizon agent reliability.
    </blockquote>
  </body>
</html>
"""


def test_parse_arxiv_list_html_extracts_paper_metadata() -> None:
    papers = _parse_arxiv_list_html(LIST_HTML)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2605.12345"
    assert paper.title == "A Careful Agent Benchmark"
    assert paper.authors == ["Ada Li", "Bo Chen"]
    assert paper.announced_date == datetime(2026, 5, 20, tzinfo=timezone.utc).date()


def test_parse_arxiv_abs_html_extracts_title_and_abstract() -> None:
    title, abstract = _parse_arxiv_abs_html(ABS_HTML)

    assert title == "A Careful Agent Benchmark"
    assert abstract == "We introduce a benchmark for long-horizon agent reliability."


def test_html_list_paper_matching_yields_signal_with_whitelist_author() -> None:
    collector = ArxivCollector(categories=["cs.AI"])
    whitelist = [
        WhitelistEntry(record_id="rec1", name="Ada Li"),
        WhitelistEntry(record_id="rec2", name="Other Person"),
    ]
    paper = _parse_arxiv_list_html(LIST_HTML)[0]
    # HTML date "Wed, 20 May 2026" maps to real announce time
    # = EDT 5-20 20:00 = UTC 5-21 00:00 (see _html_announced_datetime).
    # Window must include UTC 5-21 00:00.
    since = datetime(2026, 5, 20, 0, tzinfo=timezone.utc)
    until = datetime(2026, 5, 21, 16, tzinfo=timezone.utc)

    signals = list(
        collector._html_papers_to_signals(
            [paper],
            whitelist,
            since,
            until,
            fetched_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
            seen_ids=set(),
            abstracts={"2605.12345": ("A Careful Agent Benchmark", "Abstract body.")},
        )
    )

    assert len(signals) == 1
    assert signals[0].source_id == "arxiv:2605.12345"
    assert signals[0].author_name == "Ada Li"
    assert signals[0].author_record_id == "rec1"
    assert signals[0].url == "https://arxiv.org/abs/2605.12345"
    assert signals[0].raw_text == "A Careful Agent Benchmark\n\nAbstract body."


def test_collect_by_window_uses_html_announcement_list_before_export_api(monkeypatch) -> None:
    collector = ArxivCollector(categories=["cs.AI"])
    whitelist = [WhitelistEntry(record_id="rec1", name="Ada Li")]

    # Window 必须包含 mapped UTC announce (HTML 5-20 → UTC 5-21 00:00).
    since = datetime(2026, 5, 20, 0, tzinfo=timezone.utc)
    until = datetime(2026, 5, 21, 16, tzinfo=timezone.utc)

    # 固定 now 接近 until，确保走 HTML 公告分支（use_html_announcement_list=True）。
    # 否则随真实时间推移（until 超过 now-8day）会误走 export API，导致此用例漂移失败。
    monkeypatch.setattr(
        "hh_research.collectors.arxiv_collector._utcnow",
        lambda: datetime(2026, 5, 21, 20, tzinfo=timezone.utc),
    )

    def fake_collect_category_from_html(*args, **kwargs):
        yield from collector._html_papers_to_signals(
            _parse_arxiv_list_html(LIST_HTML),
            whitelist,
            since,
            until,
            fetched_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
            seen_ids=set(),
            abstracts={"2605.12345": ("A Careful Agent Benchmark", "Abstract body.")},
        )

    export_api_called = False

    def fail_if_export_api_is_called(*args, **kwargs):
        nonlocal export_api_called
        export_api_called = True
        return []

    monkeypatch.setattr(collector, "_collect_category_from_html", fake_collect_category_from_html)
    monkeypatch.setattr(collector._client, "results", fail_if_export_api_is_called)

    signals = list(
        collector.collect_by_window(
            whitelist,
            since,
            until,
        )
    )

    assert [s.source_id for s in signals] == ["arxiv:2605.12345"]
    assert export_api_called is False


def test_html_announced_datetime_maps_to_html_date_plus_one_day_utc() -> None:
    """Lock in the +1 day UTC mapping.

    arxiv HTML 显示的是 "EDT 当日 date"（如 "Wed, 20 May 2026"），
    实际 announce 时刻是 EDT 当日 20:00 = UTC 次日 00:00.
    所以 _html_announced_datetime 必须返回 HTML date + 1 day @ UTC 00:00.
    """
    paper = _parse_arxiv_list_html(LIST_HTML)[0]
    assert paper.announced_date == datetime(2026, 5, 20, tzinfo=timezone.utc).date()

    fallback = datetime(2026, 5, 28, tzinfo=timezone.utc)
    mapped = _html_announced_datetime(paper, fallback)

    # HTML date 2026-05-20 → UTC 2026-05-21 00:00:00
    assert mapped == datetime(2026, 5, 21, 0, 0, tzinfo=timezone.utc)
