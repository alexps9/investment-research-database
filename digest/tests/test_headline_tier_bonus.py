"""(b) _headline_score 按白名单 tier 加权：P0+ +20 / P0 +10 / P1 +5 / P2 0。

要求：
- 通过可选 tier_lookup（record_id→tier）注入，默认 None 时零 bonus（向后兼容）；
- 叠加在现有 headline_priority*10 / arxiv-whitelist+40 / generic+15 / novelty*4 / candidate+5 之上，不改动现有逻辑。
"""
from datetime import UTC, datetime

from hh_research.extract.daily_writer import _headline_score, select_headlines
from hh_research.storage.schemas import Signal


def _sig(source="x", hp=3, rid="rec1"):
    return Signal(
        source=source, source_id="x:1", author_name="a",
        url="https://x.com/a/1", raw_text="t", lang="en",
        created_at=datetime.now(UTC), fetched_at=datetime.now(UTC),
        headline_priority=hp, author_record_id=rid,
    )


def test_tier_bonus_increments():
    s = _sig(rid="rec1")
    base = _headline_score(s)  # 无 tier_lookup
    assert _headline_score(s, tier_lookup={"rec1": "P0+"}) - base == 20
    assert _headline_score(s, tier_lookup={"rec1": "P0"}) - base == 10
    assert _headline_score(s, tier_lookup={"rec1": "P1"}) - base == 5
    assert _headline_score(s, tier_lookup={"rec1": "P2"}) - base == 0


def test_no_tier_lookup_is_backward_compatible():
    s = _sig(rid="rec1")
    # 不传 / 空 lookup / rid 不在 lookup → 均不加 tier bonus
    assert _headline_score(s) == _headline_score(s, tier_lookup={})
    assert _headline_score(s) == _headline_score(s, tier_lookup={"other": "P0+"})


def test_tier_bonus_stacks_on_arxiv_whitelist():
    # arxiv + whitelist author 现有 +40 仍保留，tier 在其之上叠加
    s = _sig(source="arxiv", hp=5, rid="rec1")
    base = _headline_score(s)
    assert _headline_score(s, tier_lookup={"rec1": "P0+"}) - base == 20


def test_no_author_record_id_no_bonus():
    s = _sig(rid=None)
    assert _headline_score(s, tier_lookup={"rec1": "P0+"}) == _headline_score(s)


def test_select_headlines_uses_tier_lookup():
    # 两个同基础分的 industry 信号，传 tier_lookup 后 P0+ 者应排在前
    a = _sig(source="x", hp=3, rid="recA")
    b = _sig(source="x", hp=3, rid="recB")
    headlines = select_headlines([], [a, b], tier_lookup={"recA": "P0+"})
    assert headlines[0].author_record_id == "recA"


def test_select_headlines_tier_lookup_optional():
    # 不传 tier_lookup 仍可调用（向后兼容）
    a = _sig(source="x", hp=5, rid="recA")
    assert select_headlines([], [a]) == [a]
