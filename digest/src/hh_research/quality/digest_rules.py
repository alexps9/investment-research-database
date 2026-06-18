"""v7.0 digest quality rules — shared by digest_review_agent + pre-publish gate.

References plan: /Users/haolinguo/Desktop/2026-05-28-v7-quality-gates.md Task 2.

Two callers:
- scripts/digest_review_agent.py —审稿 agent (source="file" 或 "feishu")
- scripts/regenerate_digest.py — 发布前 gate (source="file")

source distinction:
- "file":   local generated XML; callout color attributes must be present
- "feishu": fetched from Feishu docx; color attributes may be normalized to rgb()
            string; missing color is warning only, not blocking
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

# ────────────────────────────────────────────────────────────────────
# Rule constants（v7.0 spec 5-28 用户钦定基线）
# ────────────────────────────────────────────────────────────────────

INSIGHTS_MIN_CHARS = 45   # 低于此仅警告（太短，可能漏了 takeaway）
INSIGHTS_MAX_CHARS = 120  # 严格上限，超出 blocking
EXPLAIN_MAX_CHARS = 320   # 解读 2 段总字数上限

# Insights 禁用的"技术细节数字"模式 — 这些数字应该进解读不进 Insights
# 注意：影响数字（监管 / 市场 / 客户 / 求职者 / 收入 / 良率）允许保留
TECH_NUMBER_PATTERNS = [
    # 模型参数规模 / 激活
    (r"\d+(?:\.\d+)?\s*[BMK]\s*(?:参数|激活|param|active|active params|activated)",
     "模型参数 / 激活规模"),
    (r"\d+(?:\.\d+)?\s*[BMK]\s+(?:total|activated)",
     "模型参数 / 激活规模"),
    # 训练环境 / 任务数
    (r"\d+\s*个\s*(?:真实)?(?:agent\s*)?(?:训练\s*)?(?:环境|任务|env|task)",
     "训练环境 / 任务数"),
    # benchmark 数 / 数据集规模
    (r"\d+\s*个\s*(?:benchmark|数据集|dataset)",
     "benchmark / 数据集数量"),
    (r"\d+(?:K|M)\s*(?:SFT|数据集|样本|sample)",
     "数据集规模"),
    # 训练步骤 / batch
    (r"\d+\s*个\s*(?:训练\s*)?(?:checkpoint|步骤|epoch|阶段)",
     "训练 checkpoint / 阶段数"),
]

# benchmark 名称（一旦 Insights 出现这些应该砍）
BENCHMARK_NAME_PATTERNS = [
    r"SWE-?Bench(?:\s+Verified)?", r"VSI-?Bench", r"MMLU", r"HumanEval",
    r"AIME(?:\s*\d{4})?", r"MindCube", r"ScanNet", r"VSTemporal-?Bench",
    r"GSM8K", r"BIG-?Bench", r"AGIEval", r"ARC-?AGI", r"BBH", r"GPQA",
]

# 训练 / 系统细节关键词（Insights 不应出现）
TRAINING_SYSTEM_PATTERNS = [
    r"三阶段级联验证", r"ForgeRL\s*\w*", r"CISPO\s*算法",
    r"batch\s*size", r"checkpoint\s*\d",
    r"windowed[- ]?FIFO", r"prefix[- ]?tree\s+merging",
]

# 影响数字白名单上下文 — 数字附近若有这些词，则不算技术细节
IMPACT_CONTEXT_WORDS = [
    "监管", "市场", "求职者", "客户", "用户", "收入", "成本", "良率",
    "PPA", "yield", "申请", "受损", "增长", "下降", "份额", "节点成本",
]


# ────────────────────────────────────────────────────────────────────
# Data classes
# ────────────────────────────────────────────────────────────────────

class ReviewSeverity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ReviewIssue:
    severity: ReviewSeverity
    card_label: str  # e.g. "卡片 1 · 头条 · h3"
    message: str


@dataclass
class ReviewReport:
    source: Literal["file", "feishu"]
    cards: list[dict] = field(default_factory=list)   # parsed card metadata
    issues: list[ReviewIssue] = field(default_factory=list)

    @property
    def blocking_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ReviewSeverity.BLOCKING)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ReviewSeverity.WARNING)

    @property
    def has_blocking(self) -> bool:
        return self.blocking_count > 0

    def to_markdown(self) -> str:
        """Render a human-readable markdown report."""
        lines = [
            f"# v7.0 Quality Review Report\n",
            f"- Source: {self.source}\n",
            f"- Cards parsed: {len(self.cards)}\n",
            f"- **Blocking issues: {self.blocking_count}**\n",
            f"- Warnings: {self.warning_count}\n",
            f"- **可发布**: {'❌ NO（有 blocking）' if self.has_blocking else '✅ YES'}\n",
            "\n---\n",
        ]
        # Group issues by card_label
        from collections import defaultdict
        by_card = defaultdict(list)
        for i in self.issues:
            by_card[i.card_label].append(i)
        for label in [c["label"] for c in self.cards]:
            issues = by_card.get(label, [])
            lines.append(f"\n## {label}\n")
            if not issues:
                lines.append("- ✅ 全部通过\n")
                continue
            for i in issues:
                icon = "⛔" if i.severity == ReviewSeverity.BLOCKING else "⚠️"
                lines.append(f"- {icon} **{i.severity.value}**: {i.message}\n")
        return "".join(lines)


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def text_len_zh(html: str) -> int:
    """Strip HTML tags + 折叠 whitespace, then return Chinese-friendly char count.

    Plan Step 5: text_len_zh('<p><b>判断</b> 123 </p>') == len('判断123')
    """
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", "", text)
    return len(text)


def _clean_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", "", text).strip()


def _section_chunk(xml: str, section_name: str) -> str:
    """Extract content between `<h2>section_name</h2>` and next `<h2>` (or EOF)."""
    m = re.search(
        rf"<h2[^>]*>{re.escape(section_name)}</h2>(.*)",
        xml, re.DOTALL,
    )
    if not m:
        return ""
    chunk = m.group(1)
    # Cut at next <h2 if any
    nm = re.search(r"<h2[^>]*>", chunk)
    if nm:
        chunk = chunk[:nm.start()]
    return chunk


def _parse_cards(xml: str) -> list[dict]:
    """Parse research-track cards (头条 h3 + 一、前沿研究 h4).

    Returns list of {label, h_tag, h_text, callout_attrs, callout_inner, body_xml}.
    """
    cards = []

    headline = _section_chunk(xml, "头条")
    if headline:
        for idx, m in enumerate(re.finditer(
            r"<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|<h2|<hr/?>|\Z)",
            headline, re.DOTALL,
        ), start=1):
            cards.append({
                "label": f"卡片 头条 #{idx} · h3 · {_clean_text(m.group(1))[:40]}",
                "h_tag": "h3",
                "section": "头条",
                "h_text": _clean_text(m.group(1)),
                "body_xml": m.group(2),
            })

    frontier = _section_chunk(xml, "一、前沿研究")
    if frontier:
        for idx, m in enumerate(re.finditer(
            r"<h4[^>]*>(.*?)</h4>(.*?)(?=<h4|<h3|<h2|<hr/?>|\Z)",
            frontier, re.DOTALL,
        ), start=1):
            cards.append({
                "label": f"卡片 前沿研究 #{idx} · h4 · {_clean_text(m.group(1))[:40]}",
                "h_tag": "h4",
                "section": "一、前沿研究",
                "h_text": _clean_text(m.group(1)),
                "body_xml": m.group(2),
            })

    for card in cards:
        body = card["body_xml"]
        m_callout = re.search(r"<callout([^>]*)>(.*?)</callout>", body, re.DOTALL)
        card["callout_attrs"] = m_callout.group(1) if m_callout else ""
        card["callout_inner"] = m_callout.group(2) if m_callout else ""
        card["has_callout"] = bool(m_callout)

    return cards


def _check_impact_context(text: str, number_match: str) -> bool:
    """Return True if the number is surrounded by impact context (allowed)."""
    idx = text.find(number_match)
    if idx < 0:
        return False
    # Check 30 chars window around
    window = text[max(0, idx - 30): idx + len(number_match) + 30]
    return any(w in window for w in IMPACT_CONTEXT_WORDS)


# ────────────────────────────────────────────────────────────────────
# Main API
# ────────────────────────────────────────────────────────────────────

def review_xml_text(xml: str, source: Literal["file", "feishu"] = "file") -> ReviewReport:
    """Run v7.0 quality rules on XML text, return ReviewReport.

    Args:
        xml:    full XML document text (raw LLM output or Feishu fetched content)
        source: "file"   — local generated XML; strict callout color check
                "feishu" — fetched from Feishu; color check is warning only
    """
    report = ReviewReport(source=source, cards=_parse_cards(xml))

    for card in report.cards:
        label = card["label"]

        if not card["has_callout"]:
            report.issues.append(ReviewIssue(
                ReviewSeverity.BLOCKING, label, "缺 <callout> Insights 框"
            ))
            continue

        attrs = card["callout_attrs"]
        callout_inner = card["callout_inner"]

        # ── callout 三属性检查 ──────────────────────────────
        # feishu source 渲染后 color attribute 可能变成 rgb(...) 数值或丢失
        # → 在 feishu 模式下只警告，不阻断
        callout_color_severity = (
            ReviewSeverity.BLOCKING if source == "file" else ReviewSeverity.WARNING
        )
        if 'emoji="💡"' not in attrs:
            report.issues.append(ReviewIssue(
                callout_color_severity, label, "callout 缺 emoji=💡"
            ))
        if 'background-color="light-orange"' not in attrs:
            report.issues.append(ReviewIssue(
                callout_color_severity, label,
                'callout 缺 background-color="light-orange"（Feishu 渲染后可能正常）'
            ))
        if 'border-color="orange"' not in attrs:
            report.issues.append(ReviewIssue(
                callout_color_severity, label,
                'callout 缺 border-color="orange"（Feishu 渲染后可能正常）'
            ))

        # ── Insights <p> 段数 ──────────────────────────────
        # 期望恰好 2 个 <p>: 标签段 + 1 个内容段
        ps_raw = re.findall(r"<p[^>]*>(.*?)</p>", callout_inner, re.DOTALL)
        if len(ps_raw) > 2:
            report.issues.append(ReviewIssue(
                ReviewSeverity.BLOCKING, label,
                f"Insights 段数 {len(ps_raw)}（应 =2 含标签段，多余段=v6.8 schema 残留）"
            ))
        elif len(ps_raw) < 2:
            report.issues.append(ReviewIssue(
                ReviewSeverity.BLOCKING, label,
                f"Insights 段数 {len(ps_raw)}（缺标签段或内容段）"
            ))
        else:
            content_raw = ps_raw[1]
            content_text = _clean_text(content_raw)
            n = text_len_zh(content_raw)

            # ── 字数 ──────────────────────────────────────
            if n > INSIGHTS_MAX_CHARS:
                report.issues.append(ReviewIssue(
                    ReviewSeverity.BLOCKING, label,
                    f"Insights 字数 {n} > {INSIGHTS_MAX_CHARS}（必须砍重写）"
                ))
            elif n < INSIGHTS_MIN_CHARS:
                report.issues.append(ReviewIssue(
                    ReviewSeverity.WARNING, label,
                    f"Insights 字数 {n} < {INSIGHTS_MIN_CHARS}（太短可能漏 takeaway）"
                ))

            # ── 加粗 takeaway ─────────────────────────────
            if "<b>" not in content_raw and "<strong>" not in content_raw:
                report.issues.append(ReviewIssue(
                    ReviewSeverity.BLOCKING, label,
                    "Insights 缺 <b> 加粗 takeaway 句"
                ))

            # ── 技术细节数字 ──────────────────────────────
            for pat, kind in TECH_NUMBER_PATTERNS:
                for m in re.finditer(pat, content_text, re.IGNORECASE):
                    matched = m.group(0)
                    if _check_impact_context(content_text, matched):
                        continue  # 在影响 context 中，豁免
                    report.issues.append(ReviewIssue(
                        ReviewSeverity.BLOCKING, label,
                        f"Insights 含技术细节数字 ({kind}): '{matched}' — 应放到解读正文"
                    ))

            # ── benchmark 名称堆叠 ────────────────────────
            for pat in BENCHMARK_NAME_PATTERNS:
                m = re.search(pat, content_text, re.IGNORECASE)
                if m:
                    report.issues.append(ReviewIssue(
                        ReviewSeverity.BLOCKING, label,
                        f"Insights 含 benchmark 名称: '{m.group(0)}' — 不应进 Insights"
                    ))

            # ── 训练 / 系统细节 ─────────────────────────
            for pat in TRAINING_SYSTEM_PATTERNS:
                m = re.search(pat, content_text, re.IGNORECASE)
                if m:
                    report.issues.append(ReviewIssue(
                        ReviewSeverity.BLOCKING, label,
                        f"Insights 含训练/系统细节: '{m.group(0)}' — 不应进 Insights"
                    ))

    return report
