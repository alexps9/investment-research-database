#!/usr/bin/env python3
"""Backtest: tier 加权对头条选择的影响（代表性场景，非完整历史重放）。

场景反映今日日报的头条竞争结构：arXiv 白名单论文（+40）主导 frontier，
X 行业信号 + 新补的公司官方/媒体（拟入 P0+/P0）竞争 industry 配额。
对比 select_headlines 改前(tier_lookup=None) / 改后(注入真实 tier) 的头条集合差异。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from datetime import UTC, datetime

from hh_research.extract.daily_writer import (
    HEADLINE_FRONTIER_QUOTA,
    HEADLINE_INDUSTRY_QUOTA,
    HEADLINE_MAX,
    _headline_score,
    select_headlines,
)
from hh_research.storage.schemas import Signal


def sig(sid, source, hp, rid, nov=None):
    kw = dict(source=source, source_id=sid, author_name=sid, url="https://x/" + sid,
              raw_text="t", lang="en", created_at=datetime.now(UTC),
              fetched_at=datetime.now(UTC), headline_priority=hp, author_record_id=rid)
    if nov is not None:
        kw["novelty_score"] = nov
    return Signal(**kw)


# frontier: arXiv 白名单论文（均 +40），tier 多为 P2（研究者个人长尾）
frontier = [
    sig("arxiv:论文a_P2", "arxiv", 5, "recA"),
    sig("arxiv:论文b_P2", "arxiv", 5, "recB"),
    sig("arxiv:论文c_P0", "arxiv", 4, "recC"),
    sig("arxiv:论文d_P2", "arxiv", 3, "recD"),
]
# industry: 配额边界竞争——普通信号 novelty 高(改前占配额)，新补公司官方/媒体 novelty 低但 tier 高
industry = [
    sig("x:普通行业A_P2", "x", 4, "recX1", 5),          # 40+20=60（改前占配额）
    sig("x:普通行业B_P2", "x", 4, "recX2", 4),          # 40+16=56（改前占配额）
    sig("x:SemiAnalysis媒体_P0+", "x", 3, "recMED", 3),  # 30+12=42 → +tier20=62（改后挤进）
    sig("x:NVIDIA官方_P0", "x", 3, "recNV", 3),         # 30+12=42 → +tier10=52
]
tier_lookup = {"recA": "P2", "recB": "P2", "recC": "P0", "recD": "P2",
               "recX1": "P2", "recX2": "P2", "recMED": "P0+", "recNV": "P0"}

before = select_headlines(list(frontier), list(industry))             # tier_lookup=None（改前）
after = select_headlines(list(frontier), list(industry), tier_lookup)  # 注入 tier（改后）

print(f"HEADLINE_MAX={HEADLINE_MAX} FRONTIER_QUOTA={HEADLINE_FRONTIER_QUOTA} INDUSTRY_QUOTA={HEADLINE_INDUSTRY_QUOTA}")
print()
print("各信号打分（改前 → 改后）:")
for s in frontier + industry:
    b, a = _headline_score(s), _headline_score(s, tier_lookup)
    flag = f"  ← tier+{a - b}" if a != b else ""
    print(f"  {s.source_id:24} {b:>3} → {a:>3}{flag}")
print()
print("改前头条:", [s.source_id for s in before])
print("改后头条:", [s.source_id for s in after])
bset = {s.source_id for s in before}
aset = {s.source_id for s in after}
print("✅ 因 tier 加权新进头条:", sorted(aset - bset) or "（无）")
print("⚠️ 被挤出头条:", sorted(bset - aset) or "（无）")
