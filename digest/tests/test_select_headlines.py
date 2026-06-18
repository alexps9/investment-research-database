"""Task5: select_headlines helper + DailyDigest.headline_signal_ids 测试。

codex P1：图片裁剪到「头条 ∪ arxiv」需要抓手——把 headline 选择抽成可复用 helper，
并让 DailyDigest 暴露 headline_signal_ids，供图片提取范围裁剪使用。
"""
from datetime import datetime, timezone

from hh_research.extract.daily_writer import (
    HEADLINE_FRONTIER_QUOTA,
    HEADLINE_MAX,
    select_headlines,
)
from hh_research.storage.schemas import Signal


def _sig(source_id: str, source: str = "arxiv", headline_priority: int = 3,
         author_record_id: str | None = None) -> Signal:
    return Signal(
        source=source, source_id=source_id, author_name="x",
        url="https://arxiv.org/abs/x", raw_text="t", lang="en",
        created_at=datetime.now(timezone.utc), fetched_at=datetime.now(timezone.utc),
        headline_priority=headline_priority, author_record_id=author_record_id,
    )


def test_select_headlines_respects_max():
    frontier = [_sig(f"arxiv:{i}", "arxiv", 5, "rec") for i in range(5)]
    industry = [_sig(f"x:{i}", "x", 3) for i in range(5)]
    headlines = select_headlines(frontier, industry)
    assert len(headlines) == HEADLINE_MAX
    # frontier whitelist 论文高分，应占足配额
    assert sum(1 for h in headlines if h.source == "arxiv") >= HEADLINE_FRONTIER_QUOTA


def test_select_headlines_fallback_fill_when_one_bucket_sparse():
    frontier = [_sig("arxiv:1", "arxiv", 5, "rec")]  # 只 1 篇前沿
    industry = [_sig(f"x:{i}", "x", 3) for i in range(8)]
    headlines = select_headlines(frontier, industry)
    assert len(headlines) == HEADLINE_MAX  # 不足部分由 industry 回填
    assert any(h.source == "arxiv" for h in headlines)  # 那 1 篇前沿仍入选


def test_select_headlines_total_below_max():
    headlines = select_headlines([_sig("arxiv:1", "arxiv", 5, "rec")], [_sig("x:1", "x", 3)])
    assert len(headlines) == 2  # 总数不足 MAX，返回全部


def test_select_headlines_empty():
    assert select_headlines([], []) == []


def test_select_headlines_returns_signals_with_source_id():
    headlines = select_headlines([_sig("arxiv:42", "arxiv", 5, "rec")], [])
    assert headlines[0].source_id == "arxiv:42"
