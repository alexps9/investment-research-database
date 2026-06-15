"""Daily digest writer.

Aggregates all extracted signals for one day into a readable markdown report
using Claude Opus 4.7 with adaptive thinking. Called once per pipeline run.

v5 (post 5.20): source-based bucket routing (no longer novelty-filtered globally).
- arxiv / openalex / X-tweets-citing-arxiv → 前沿研究 bucket (全展示)
- other X / RSS → 行业应用 bucket (全展示)
- Headlines selected via weighted score: whitelist research > industry, 3+2 quota.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Literal

import anthropic
import httpx

from ..storage.schemas import DailyDigest, Signal
from ..utils.logger import get_logger
from .claude_client import CostTracker, build_digest_system, make_client, resolve_model_id

log = get_logger("daily_writer")

# Logical name. Bedrock falls back to Opus 4.6; native Anthropic uses Opus 4.7.
# Override via env var HH_DIGEST_MODEL (e.g. "claude-sonnet-4-6" to avoid Opus throttle).
import os as _os
MODEL_LOGICAL = _os.getenv("HH_DIGEST_MODEL", "claude-opus-4-7")
MAX_TOKENS = 64000  # v6.2 (5.21): 32K 仍打满（V2.1 行业应用 + 折叠区被压）→ 拉到 Sonnet 上限 64K，给充足空间

# v5 per-bucket caps: 替代旧的全局 MAX_SIGNALS_FOR_DIGEST=60
FRONTIER_CAP = 40   # 一、前沿研究：arxiv / OpenAlex / X-引用论文
INDUSTRY_CAP = 50   # 二、行业应用：X 推文 / RSS。30→50：让 LLM 看到完整 novelty 分布（低 novelty 信号会被 LLM 按 v6 prompt 分级归折叠区，不进正文）
TOTAL_CARD_BUDGET = 15    # v7.0 精选制：全文信号卡总数上限（Top3 + 赛道卡），与 daily_digest.md 同步
TRACK_CARD_BUDGET = 12    # v7.0: 赛道正文 h4 卡上限（= TOTAL - Top3）
HEADLINE_FRONTIER_QUOTA = 2  # 头条研究类配额（v7.0 行业资讯为主，2:3）
HEADLINE_INDUSTRY_QUOTA = 3  # 头条应用类配额
HEADLINE_MAX = 5             # 头条上限


def _classify_section(signal: Signal) -> Literal["frontier", "industry"]:
    """Route a signal to frontier-research or industry-application section.

    Per user rule (2026-05-20): arxiv/OpenAlex/RSS 全部展示，novelty 只限制头条选择，
    不限制正文呈现。
    - source==arxiv / openalex → frontier
    - source==x but URL/text references arxiv.org → frontier (推文介绍论文)
    - source==x other / source==rss / source==other → industry
    """
    if signal.source in ("arxiv", "openalex"):
        return "frontier"
    blob = ((signal.url or "") + " " + (signal.raw_text or "")).lower()
    if "arxiv.org" in blob:
        return "frontier"
    return "industry"


def _is_whitelist_author(signal: Signal) -> bool:
    """A signal is from a whitelist author iff author_record_id is set
    (matched during collection / extraction step)."""
    return signal.author_record_id is not None


TIER_BONUS = {"P0+": 20, "P0": 10, "P1": 5, "P2": 0}


def _headline_score(signal: Signal, tier_lookup: dict[str, str] | None = None) -> int:
    """Score signal for headline selection. Higher = more likely a headline.

    Per user rule: 重点实验室/大厂 (whitelist) 论文 > 重要行业应用。
    - base = headline_priority * 10 (range 10-50)
    - arxiv/openalex + whitelist author: +40 (strongest boost)
    - arxiv/openalex generic: +15
    - x / rss industry: + novelty * 4 (range 4-20)
    - is_headline_candidate flag: +5 bonus
    - whitelist tier bonus (6-09): P0+ +20 / P0 +10 / P1 +5 / P2 0
      （让公司官方/行业资讯类高 tier 源更易上头条；tier_lookup 为 None 时不加，向后兼容）
    """
    score = (signal.headline_priority or 0) * 10
    if signal.source in ("arxiv", "openalex"):
        if _is_whitelist_author(signal):
            score += 40
        else:
            score += 15
    else:
        score += (signal.novelty_score or 0) * 4
    if signal.is_headline_candidate:
        score += 5
    if tier_lookup and signal.author_record_id:
        score += TIER_BONUS.get(tier_lookup.get(signal.author_record_id), 0)
    return score


class DailyWriter:
    def __init__(
        self,
        client=None,
        cost: CostTracker | None = None,
    ) -> None:
        # 5.20 教训：默认 client max_retries=4 timeout=300s → 最长 25 min 才 fail。
        # daily_writer 用专用短 client：max_retries=1 timeout=180s → 最长 6 min 切 fallback。
        self.client = client or make_client(max_retries=1, timeout=180.0)
        self.cost = cost or CostTracker()
        self.system = build_digest_system()
        self.model = resolve_model_id(MODEL_LOGICAL)
        # Sonnet 4.6 fallback model (不同 Bedrock TPM 桶，便宜 5x，速度快 2-3x)
        try:
            self.fallback_model = resolve_model_id("claude-sonnet-4-6")
        except Exception:  # noqa: BLE001
            self.fallback_model = None

    def _call_with_fallback(self, user_payload: str):
        """Streaming LLM call。

        5.20-5.21 教训：Bedrock non-streaming 模式在拥塞时整段 hang。
        改用 streaming → 每个 token 单独返回，不会被 SDK idle timeout kill。
        总耗时仍可能 5-10 min（Bedrock 实际生成速度），但不会假死。
        """
        log.info("  streaming from model: %s", self.model)
        text = ""
        usage = None
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=self.system,
                messages=[{"role": "user", "content": user_payload}],
            ) as stream:
                for chunk in stream.text_stream:
                    text += chunk
                final = stream.get_final_message()
                usage = final.usage
            return _StreamResponseShim(text=text, usage=usage)
        except (anthropic.APITimeoutError, anthropic.RateLimitError,
                anthropic.APIStatusError, anthropic.APIConnectionError,
                # v7.0 5-28: anthropic SDK 不包装这些底层 httpx 异常，
                # streaming 中途断开 (peer closed / read timeout) 时直接
                # raise 出来，原 except 抓不到导致整次 LLM call 浪费。
                httpx.ReadTimeout, httpx.RemoteProtocolError,
                httpx.ConnectError, httpx.ReadError) as e:
            log.warning("Primary model failed (%s: %s); trying fallback %s",
                       type(e).__name__, str(e)[:120], self.fallback_model)
            if not self.fallback_model or self.fallback_model == self.model:
                # v7.0 5-28: primary == fallback 时也至少 retry 一次
                # （Bedrock 流式 streaming 中断常常是瞬时网络问题，retry 即可恢复）
                log.warning("primary == fallback; retrying same model once")
                self.fallback_model = self.model
            text = ""
            with self.client.messages.stream(
                model=self.fallback_model,
                max_tokens=MAX_TOKENS,
                system=self.system,
                messages=[{"role": "user", "content": user_payload}],
            ) as stream:
                for chunk in stream.text_stream:
                    text += chunk
                final = stream.get_final_message()
                usage = final.usage
            return _StreamResponseShim(text=text, usage=usage)

    def write(self, digest_date: datetime, signals: list[Signal],
              tier_lookup: dict[str, str] | None = None) -> DailyDigest:
        """Generate the daily digest XML.

        v5 routing (post 5.20):
        0. Eligibility filter: arxiv/openalex MUST have whitelist author to enter
           body (per user 2026-05-20 rule "这些才可以进入日报正文"). X/RSS pass through.
        1. Classify each signal → frontier (一、前沿研究) or industry (二、行业应用).
        2. Sort within bucket by novelty desc; cap each bucket separately.
        3. Pick headlines via weighted _headline_score: 3 frontier + 2 industry,
           with fallback if either bucket is sparse.
        4. Pass three JSON arrays to LLM: HEADLINE_CANDIDATES / FRONTIER / INDUSTRY.
        """
        # Step 0: eligibility filter
        def _is_eligible(s: Signal) -> bool:
            if s.source in ("arxiv", "openalex"):
                return _is_whitelist_author(s)
            return True  # X / RSS / other are not whitelist-gated
        eligible = [s for s in signals if _is_eligible(s)]
        n_dropped = len(signals) - len(eligible)
        if n_dropped:
            log.info(
                "  eligibility filter: dropped %d non-whitelist arxiv/openalex signals",
                n_dropped,
            )

        # Step 1: classify into two buckets
        frontier_pool = [s for s in eligible if _classify_section(s) == "frontier"]
        industry_pool = [s for s in eligible if _classify_section(s) == "industry"]

        # Step 2: within-bucket sort by (novelty desc, headline_priority desc)
        def _body_key(s: Signal) -> tuple[int, int]:
            return (s.novelty_score or 0, s.headline_priority or 0)
        frontier_pool.sort(key=_body_key, reverse=True)
        industry_pool.sort(key=_body_key, reverse=True)

        # Cap each bucket separately (避免 prompt 超 32K 输出预算)
        if len(frontier_pool) > FRONTIER_CAP:
            log.info(
                "  capping frontier %d → %d signals (top by novelty)",
                len(frontier_pool), FRONTIER_CAP,
            )
            frontier_pool = frontier_pool[:FRONTIER_CAP]
        if len(industry_pool) > INDUSTRY_CAP:
            log.info(
                "  capping industry %d → %d signals (top by novelty)",
                len(industry_pool), INDUSTRY_CAP,
            )
            industry_pool = industry_pool[:INDUSTRY_CAP]

        # Step 3: headline selection (weighted score + diversity quota + tier 加权)
        headlines = select_headlines(frontier_pool, industry_pool, tier_lookup)

        log.info(
            "  bucket sizes: frontier=%d industry=%d | headlines=%d (frontier=%d industry=%d)",
            len(frontier_pool), len(industry_pool), len(headlines),
            sum(1 for h in headlines if _classify_section(h) == "frontier"),
            sum(1 for h in headlines if _classify_section(h) == "industry"),
        )

        # Step 4: serialize to JSON for prompt（含资本动向栏目；不改 frontier/industry pool）
        headline_ids = {h.source_id for h in headlines}
        capital_pool = select_capital_signals(eligible, headline_ids)
        log.info("  capital signals: %d (导览后/赛道正文前)", len(capital_pool))
        user_payload = _build_user_payload(
            digest_date, headlines, capital_pool, frontier_pool, industry_pool
        )

        log.info(
            "writing daily digest for %s: frontier=%d + industry=%d + headlines=%d (~%d chars)",
            digest_date.date(),
            len(frontier_pool), len(industry_pool), len(headlines),
            len(user_payload),
        )

        # Opus first, Sonnet fallback on timeout / throttle
        # (5.20 Bedrock Opus 限流踩坑教训：单次调用挂死 22 min 后才 timeout)
        # 策略：Opus 单次 timeout 120s，失败直接切 Sonnet（不同 TPM 桶）
        response = self._call_with_fallback(user_payload)

        self.cost.record(self.model, response.usage)

        # Extract markdown text (there may be thinking blocks before/after)
        markdown = ""
        for block in response.content:
            if block.type == "text":
                markdown += block.text

        if not markdown.strip():
            log.warning("digest came back empty")

        # 输出结构自检（log-only）：v7.0 精选格式关键栏目 + 卡片预算
        if "Top 3 大新闻" not in markdown:
            log.warning("  digest missing 「Top 3 大新闻」 section")
        if "今日导览" not in markdown:
            log.warning("  digest missing 「今日导览」 section")
        if capital_pool and "资本动向" not in markdown:
            log.warning("  digest missing 资本动向 section (capital_pool=%d)", len(capital_pool))
        n_track_cards = markdown.count("<h4")
        if n_track_cards > TRACK_CARD_BUDGET:
            log.warning(
                "  digest track cards %d > budget %d (v7.0 精选上限)",
                n_track_cards, TRACK_CARD_BUDGET,
            )

        return DailyDigest(
            digest_date=digest_date,
            markdown=markdown.strip(),
            signal_ids=[s.source_id for s in signals],
            headline_signal_ids=[s.source_id for s in headlines],
            signal_count=len(signals),
            llm_cost_usd=self.cost.usd,
        )


def select_headlines(frontier_pool: list[Signal], industry_pool: list[Signal],
                     tier_lookup: dict[str, str] | None = None) -> list[Signal]:
    """从已 cap 的 frontier/industry pool 选头条（weighted score + diversity quota）。

    抽自 DailyWriter.write Step 3，供图片提取按「头条 ∪ arxiv」裁剪范围复用（Task5）。
    tier_lookup（record_id→tier）注入白名单 tier 加权（6-09）；None 时与旧行为一致。
    """
    def _score(s: Signal) -> int:
        return _headline_score(s, tier_lookup)
    frontier_ranked = sorted(frontier_pool, key=_score, reverse=True)
    industry_ranked = sorted(industry_pool, key=_score, reverse=True)
    headlines = (frontier_ranked[:HEADLINE_FRONTIER_QUOTA]
                 + industry_ranked[:HEADLINE_INDUSTRY_QUOTA])
    if len(headlines) < HEADLINE_MAX:
        short = HEADLINE_MAX - len(headlines)
        extra_pool = (frontier_ranked[HEADLINE_FRONTIER_QUOTA:]
                      + industry_ranked[HEADLINE_INDUSTRY_QUOTA:])
        extra_pool.sort(key=_score, reverse=True)
        headlines += extra_pool[:short]
    return headlines[:HEADLINE_MAX]


CAPITAL_CAP = 8

# 资本动向关键词（保守，2026-06-09）。匹配 raw_text + summary_zh（已 lower）。
_CAPITAL_KW_EN = [
    "funding", "raised", "raises", "raise", "valuation", "valued at",
    "series a", "series b", "series c", "seed round",
    "investment", "invests", "acquisition", "acquires", "acquired", "merger", "ipo",
]
_CAPITAL_KW_ZH = ["融资", "投资", "估值", "收购", "并购", "上市", "ipo", "战略投资"]


def _is_capital_signal(signal: Signal) -> bool:
    """保守关键词识别投融资 / 收购 / IPO / 估值类信号（用 raw_text + summary_zh）。

    英文单词用词边界（避免 raise 误伤 praise 等），多词短语与中文用子串匹配。
    """
    text = ((signal.raw_text or "") + " " + (signal.summary_zh or "")).lower()
    for kw in _CAPITAL_KW_EN:
        if " " in kw:
            if kw in text:
                return True
        elif re.search(r"\b" + re.escape(kw) + r"\b", text):
            return True
    return any(kw in text for kw in _CAPITAL_KW_ZH)


def select_capital_signals(signals: list[Signal], headline_ids: set[str],
                           cap: int = CAPITAL_CAP) -> list[Signal]:
    """筛非头条投融资信号供「资本动向」栏目（导览后、赛道正文前呈现）。

    只收 X/RSS/other；排除已入头条的信号；按 created_at 降序；cap 截断。
    额外视图，不修改 frontier_pool / industry_pool 原逻辑。
    """
    pool = [s for s in signals
            if s.source in ("x", "rss", "other")
            and s.source_id not in headline_ids
            and _is_capital_signal(s)]
    pool.sort(key=lambda s: s.created_at, reverse=True)
    return pool[:cap]


def _build_user_payload(digest_date, headlines, capital_pool, frontier_pool, industry_pool) -> str:
    """组装 LLM user payload：HEADLINE → CAPITAL → FRONTIER → INDUSTRY（资本动向在导览后、赛道前）。

    资本动向已单独成栏，从 frontier/industry payload 去除同 source_id，避免同一投融资信号重复展示。
    """
    capital_ids = {s.source_id for s in capital_pool}
    headline_dicts = [_signal_to_dict(s) for s in headlines]
    capital_dicts = [_signal_to_dict(s) for s in capital_pool]
    frontier_dicts = [_signal_to_dict(s) for s in frontier_pool if s.source_id not in capital_ids]
    industry_dicts = [_signal_to_dict(s) for s in industry_pool if s.source_id not in capital_ids]
    return (
        f"DIGEST_DATE: {digest_date.date().isoformat()}\n\n"
        f"HEADLINE_CANDIDATES (pipeline 已挑选 top {HEADLINE_MAX} 头条候选；"
        f"按 v7.0 规则从中选 3 条写「Top 3 大新闻」，行业重大事件优先，可调序):\n"
        f"{json.dumps(headline_dicts, ensure_ascii=False, indent=2)}\n\n"
        f"CAPITAL_SIGNALS (资本动向；在「今日导览」之后、赛道正文之前；只收 AI/科技产业相关投融资，"
        f"无关条目丢弃；中性陈述事实 + 一句产业含义，不做投资判断；为空或全部无关则整节省略):\n"
        f"{json.dumps(capital_dicts, ensure_ascii=False, indent=2)}\n\n"
        f"FRONTIER_RESEARCH_SIGNALS (论文候选池，sorted by novelty desc；"
        f"按 v7.0 准入门槛精选 3-6 篇进赛道正文，未入选直接不呈现):\n"
        f"{json.dumps(frontier_dicts, ensure_ascii=False, indent=2)}\n\n"
        f"INDUSTRY_APPLICATION_SIGNALS (行业资讯候选池，sorted by novelty desc；"
        f"赛道正文以此为主体精选，行业占比 >= 60%，与论文混编在同一赛道下):\n"
        f"{json.dumps(industry_dicts, ensure_ascii=False, indent=2)}"
    )


def should_enrich_authors(*, publish: bool, skip_flag: bool) -> bool:
    """Task5: author coauthor enrich 是 regenerate 最慢步。预览(不发布)默认跳过提速；
    正式发布默认做(保署名质量)；--skip-author-enrich 显式强制跳过。"""
    return publish and not skip_flag


def _signal_to_dict(signal: Signal) -> dict[str, Any]:
    """Convert Signal to compact JSON for the digest prompt — HH 5-track schema."""
    return {
        "source": signal.source,
        "source_id": signal.source_id,
        "author_name": signal.author_name,
        "is_whitelist_author": _is_whitelist_author(signal),  # v5: 让 prompt 决定加粗
        "section": _classify_section(signal),                  # v5: frontier/industry 提示
        "url": signal.url,
        "created_at": signal.created_at.date().isoformat(),
        "track": signal.track,
        "is_headline_candidate": signal.is_headline_candidate,
        "headline_priority": signal.headline_priority,
        "summary_zh": signal.summary_zh,
        "cognitive_takeaway_zh": signal.cognitive_takeaway_zh,
        "core_findings_zh": signal.core_findings_zh,
        "method_framework_zh": signal.method_framework_zh,
        "method_detail_zh": signal.method_detail_zh,
        "result_summary_zh": signal.result_summary_zh,
        "key_terms": signal.key_terms,
        "signal_source_zh": signal.signal_source_zh,
        "novelty_score": signal.novelty_score,
        "needs_human_review": signal.needs_human_review,
        "image_urls": signal.image_urls,
        # v6 (post 5.21): coauthors 数据用于直接渲染 RM 表
        # 精简：只给 LLM 渲染需要的字段，剔除 provenance（trace 文档用，prompt 不需要）
        "coauthors": [
            {k: v for k, v in c.model_dump(exclude_none=True).items() if k != "provenance"}
            for c in (signal.coauthors or [])
        ],
    }


class _StreamResponseShim:
    """让 streaming 返回的 text 装得像 messages.create() 的 response 对象（兼容外部 .content 迭代）"""
    def __init__(self, text: str, usage):
        self.usage = usage
        self.content = [_TextBlock(text)]


class _TextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text
