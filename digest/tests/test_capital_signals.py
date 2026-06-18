"""资本动向栏目：_is_capital_signal 识别 + select_capital_signals 筛选。

要求：
- 保守关键词识别投融资/收购/IPO/估值（中英）；普通发布/论文/benchmark 不误识别；
- 只收 X/RSS/other；排除已入头条的信号；created_at desc；cap=CAPITAL_CAP。
"""
from datetime import UTC, datetime, timedelta

from hh_research.extract.daily_writer import (
    CAPITAL_CAP,
    _is_capital_signal,
    select_capital_signals,
)
from hh_research.storage.schemas import Signal


def _sig(sid, source="x", raw="t", zh=None, rid=None, days_ago=0):
    return Signal(
        source=source, source_id=sid, author_name="a", url="https://x/" + sid,
        raw_text=raw, lang="en",
        created_at=datetime.now(UTC) - timedelta(days=days_ago),
        fetched_at=datetime.now(UTC), summary_zh=zh, author_record_id=rid,
    )


def test_is_capital_signal_detects_english():
    assert _is_capital_signal(_sig("x:1", raw="Anysphere raised $900M Series C at $9B valuation"))
    assert _is_capital_signal(_sig("x:2", raw="OpenAI announces acquisition of a robotics startup"))
    assert _is_capital_signal(_sig("x:3", raw="The company files for IPO next quarter"))
    assert _is_capital_signal(_sig("x:4", raw="seed round led by a16z, total investment $20M"))


def test_is_capital_signal_detects_chinese():
    assert _is_capital_signal(_sig("x:5", raw="t", zh="某公司完成 5 亿美元 B 轮融资"))
    assert _is_capital_signal(_sig("x:6", raw="t", zh="谷歌对该团队进行战略投资"))
    assert _is_capital_signal(_sig("x:7", raw="t", zh="该独角兽估值达到 100 亿美元"))
    assert _is_capital_signal(_sig("x:8", raw="t", zh="宣布收购一家芯片公司"))


def test_is_capital_signal_ignores_non_capital():
    assert not _is_capital_signal(_sig("x:9", raw="New model release with SOTA benchmark results"))
    assert not _is_capital_signal(_sig("x:10", raw="t", zh="发布新论文，提出一种新的训练方法"))
    assert not _is_capital_signal(_sig("x:11", raw="Researchers demonstrate a new robot manipulation demo"))


def test_select_capital_excludes_headlines():
    sigs = [_sig("x:1", raw="raised Series A funding"), _sig("x:2", raw="acquisition deal closed")]
    pool = select_capital_signals(sigs, headline_ids={"x:1"})
    ids = [s.source_id for s in pool]
    assert "x:1" not in ids
    assert "x:2" in ids


def test_select_capital_source_filter():
    # arxiv/openalex 不进资本动向（只收 X/RSS/other）
    sigs = [_sig("arxiv:1", source="arxiv", raw="funding raised"), _sig("x:1", raw="funding raised")]
    ids = [s.source_id for s in select_capital_signals(sigs, headline_ids=set())]
    assert "arxiv:1" not in ids
    assert "x:1" in ids


def test_select_capital_cap_and_recency():
    # 超过 cap 截断，且按 created_at desc（最新在前）
    sigs = [_sig("x:" + str(i), raw="funding round announced", days_ago=i) for i in range(20)]
    pool = select_capital_signals(sigs, headline_ids=set())
    assert len(pool) == CAPITAL_CAP
    assert pool[0].source_id == "x:0"  # 最新（days_ago=0）排第一


def test_select_capital_empty_when_none():
    sigs = [_sig("x:1", raw="model release"), _sig("x:2", raw="benchmark update")]
    assert select_capital_signals(sigs, headline_ids=set()) == []


def test_payload_capital_between_headline_and_frontier():
    from hh_research.extract.daily_writer import _build_user_payload
    cap = [_sig("x:cap", raw="Anysphere raised $900M Series C")]
    p = _build_user_payload(datetime.now(UTC), [], cap, [], [])
    assert "CAPITAL_SIGNALS" in p
    assert p.index("HEADLINE_CANDIDATES") < p.index("CAPITAL_SIGNALS") < p.index("FRONTIER_RESEARCH_SIGNALS")
    assert "x:cap" in p


def test_payload_capital_empty_array_when_none():
    from hh_research.extract.daily_writer import _build_user_payload
    p = _build_user_payload(datetime.now(UTC), [], [], [], [])
    # 空 capital：保留标签 + 空数组，由 prompt 指示 LLM 为空则不输出栏目
    assert "CAPITAL_SIGNALS" in p


def test_payload_dedupes_capital_from_industry():
    # 同一 capital 信号同时在 capital_pool 与 industry_pool：payload 只应在 CAPITAL_SIGNALS、不在 INDUSTRY
    from hh_research.extract.daily_writer import _build_user_payload
    dup = _sig("x:capdup", raw="raised $100M Series B funding")
    other = _sig("x:plain", raw="model release benchmark")
    p = _build_user_payload(datetime.now(UTC), [], [dup], [], [dup, other])
    cap_seg = p[p.index("CAPITAL_SIGNALS"):p.index("FRONTIER_RESEARCH_SIGNALS")]
    ind_seg = p[p.index("INDUSTRY_APPLICATION_SIGNALS"):]
    assert "x:capdup" in cap_seg
    assert "x:capdup" not in ind_seg
    assert "x:plain" in ind_seg  # 非 capital 的 industry 信号仍保留
