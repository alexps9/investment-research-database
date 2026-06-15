"""Pydantic models for signals, whitelist entries, and daily digest."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

_X_HANDLE_RE = re.compile(r"https?://(?:x|twitter|www\.x|www\.twitter)\.com/([A-Za-z0-9_]+)")


class WhitelistEntry(BaseModel):
    """One row from the `whitelist` table in Bitable."""

    record_id: str = Field(..., description="Feishu record_id")
    name: str = Field(..., description="Display name (mostly English)")
    twitter_url: str | None = None
    organization: str | None = None
    category: str | None = Field(None, description="业界 / 学界 / 其他")
    tier: str | None = Field(None, description="P0+ / P0 / P1 / P2（Bitable 真相源，6-09 接入运行时）")
    entity_type: str | None = Field(None, description="company / person / lab / university / media / investor / benchmark_org")
    source_authority: str | None = Field(None, description="official / founder / employee / third_party / media / unknown")
    research_tags: list[str] = Field(default_factory=list)
    active_levels: list[str] = Field(default_factory=list, description="活跃情况 multi-select")
    bio: str | None = None
    notes: str | None = None

    # Scheduling / disambiguation fields (may be empty at MVP start)
    arxiv_author_query: str | None = None
    orcid: str | None = None
    affiliation_regex: str | None = None
    last_tweet_at: datetime | None = None
    avg_interval_days: float | None = None

    # Enriched URLs (populated by enrich_whitelist_urls.py + enrich_arxiv_validation.py)
    personal_url: str | None = None
    scholar_url: str | None = None
    github_url: str | None = None
    arxiv_homepage_url: str | None = None
    openalex_url: str | None = Field(
        None, description="OpenAlex author profile URL, e.g. https://openalex.org/A5001226970",
    )

    @property
    def openalex_id(self) -> str | None:
        """Extract OpenAlex author ID, e.g. 'A5001226970'.

        Bitable URL fields store as markdown '[url](url)', so we regex-extract
        the trailing 'A...' identifier from the openalex.org URL.
        """
        if not self.openalex_url:
            return None
        m = re.search(r"openalex\.org/(A\d+)", self.openalex_url)
        return m.group(1) if m else None

    @property
    def twitter_handle(self) -> str | None:
        """Extract @handle from the Twitter URL field.

        Bitable URL-style fields wrap content as markdown ('[label](url)'), so we
        regex-extract the handle from any embedded x.com / twitter.com URL.
        """
        if not self.twitter_url:
            return None
        m = _X_HANDLE_RE.search(self.twitter_url)
        return m.group(1) if m else None


class Signal(BaseModel):
    """One signal (tweet, arXiv paper, OpenAlex work, RSS post, ...) collected upstream."""

    source: Literal["x", "arxiv", "openalex", "rss", "other"]
    source_id: str = Field(..., description="Globally unique: 'x:<tweet_id>' or 'arxiv:<paper_id>'")
    author_name: str = Field(..., description="For matching to whitelist")
    author_record_id: str | None = Field(
        None, description="Whitelist record_id once matched; None if unmatched"
    )
    url: str
    raw_text: str
    lang: str = "en"
    created_at: datetime
    fetched_at: datetime

    # LLM-extracted fields (filled by signal_extractor — HH 5-track schema)
    summary_zh: str | None = None
    cognitive_takeaway_zh: str | None = None
    track: Literal["基础模型", "认知模型", "多模态智能", "世界模型", "AI infra", "ai4s", "其他"] | None = None
    # 5.22: "基础模型" replaces "认知模型" in new digests; "认知模型" kept for back-compat with historical Bitable records.
    is_headline_candidate: bool = False
    headline_priority: int = Field(1, ge=1, le=5)
    # arXiv-paper deep fields (empty for tweets / RSS)
    core_findings_zh: list[str] = Field(default_factory=list)
    method_framework_zh: str | None = None
    method_detail_zh: str | None = None
    result_summary_zh: str | None = None
    # generic fields
    key_terms: list[str] = Field(default_factory=list)
    novelty_score: int | None = Field(None, ge=1, le=5)
    signal_source_zh: str | None = None
    needs_human_review: bool = False

    # Raw JSON from LLM for debugging / forward compat
    extract_json: str | None = None

    # Image URLs (paper figures or RSS media); used by digest renderer
    image_urls: list[str] = Field(default_factory=list)

    # Co-author info (filled by author_enricher when source=arxiv;
    # used by daily_writer to render Researcher Mapping table)
    coauthors: list["CoauthorInfo"] = Field(default_factory=list)

    # =========================================================
    # v8.0 fields (Plan v3 §3.2 + §3.3 + §3.4)
    # All optional/default to keep v7.0 pipeline back-compat.
    # =========================================================
    event_type: Literal[
        "①模型/产品发布",
        "②技术研究突破",
        "③硬件/Infra突破",
        "④大佬评论/观点",
        "⑤评测/榜单",
        "⑥Demo/演示",
        "⑦公司间商业动作",
        "⑧顶级人员变动",
    ] | None = None
    m1_score: int | None = Field(None, ge=0, le=3, description="M1 投研可操作性")
    m2_score: int | None = Field(None, ge=0, le=3, description="M2 实体级别")
    m3_score: int | None = Field(None, ge=0, le=3, description="M3 数字震撼度")
    m4_score: int | None = Field(None, ge=0, le=3, description="M4 跨信号共识")
    m5_score: int | None = Field(None, ge=0, le=3, description="M5 范式动摇")
    constraint_pass: bool = Field(False, description="v8 是否通过强约束")
    constraint_rule: str | None = Field(None, description="通过的规则 ID, e.g. ①_model_product_release")
    auto_headline: bool = Field(False, description="强约束自动头条")
    edge_case: bool = Field(False, description="边缘 case 候选 (等 G0 评论)")
    final_selected: bool = Field(False, description="经用户 final list 选中")
    primary_org: str | None = Field(None, description="canonical 公司名 (lowercase)")
    canonical_event_key: str | None = Field(None, description="事件 cluster key")


class CoauthorInfo(BaseModel):
    """One co-author of a paper, with enriched profile data and provenance.

    Populated by `author_enricher.py` after a paper passes whitelist filter.
    `provenance` field records which tool / URL each datum came from, so
    the standalone RM trace document can show the search trail (用户 5.19 需求 #6).
    """
    name: str
    role: Literal["一作", "共一", "通讯", "资深合作", "合作"] = "合作"
    is_whitelist: bool = False
    whitelist_record_id: str | None = None
    affiliation: str | None = None
    current_status: str | None = None  # "PhD candidate" / "AP at MIT" 等
    advisor: str | None = None
    github: str | None = None  # username 或 full URL
    scholar_id: str | None = None
    homepage: str | None = None
    email: str | None = None
    expected_graduation: str | None = None  # "2027-2028"
    # provenance: {field_name: "anysearch:<url>" 或 "bitable:whitelist" 或 "arxiv:html" 等}
    provenance: dict[str, str] = Field(default_factory=dict)

    # V4 新增（runtime + 日志用，不写 Bitable）
    verification: dict[str, str] = Field(default_factory=dict)
    # 例: {"affiliation": "verified", "github": "rejected:name_mismatch",
    #      "homepage": "verified", "email": "skipped:no_url"}

    enrich_sources: dict[str, list[str]] = Field(default_factory=dict)
    # 例: {"affiliation": ["anysearch", "openalex"], "github": ["anysearch"]}


class DailyDigest(BaseModel):
    """One day's aggregated digest."""

    digest_date: datetime  # date at 00:00 local
    markdown: str
    signal_ids: list[str] = Field(default_factory=list)
    headline_signal_ids: list[str] = Field(default_factory=list)
    signal_count: int = 0
    llm_cost_usd: float = 0.0
    published_to_doc_url: str | None = None
    published_to_chat_at: datetime | None = None
