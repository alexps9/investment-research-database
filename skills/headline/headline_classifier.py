"""v8.0 Two-stage headline classifier (Plan v3 §3.3).

For each Signal, decide:
  - event_type (① ~ ⑧)
  - m1-m5 scores (0-3)
  - constraint_pass (whether passes any of 8 strong constraints)
  - constraint_rule (which rule passed, if any)
  - primary_org, canonical_event_key (canonical entity)

Two-stage design:
  Stage 1 — Deterministic prefilter: use Bitable tier + heuristics
    (no LLM call, fast, auditable)
  Stage 2 — LLM-assisted labels: paradigm_level, first_in_industry, etc.
    (called only for signals that pass deterministic gate)

This module is OFFLINE-CAPABLE for backtest: pass tier_lookup as dict.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from .canonical_entity import CanonicalEntity, build_event_key, canonicalize
from .schemas import Signal

log = logging.getLogger("headline_classifier")

# ============================================================
# Top tier definitions (mirrors config/headline_constraints.yml)
# ============================================================

TOP_TIER_LABS = {
    "openai", "anthropic", "google", "google-deepmind", "meta", "microsoft",
    "xai", "apple", "nvidia", "alphabet", "deepseek", "mistral",
    "stanford", "mit", "ucb", "cmu", "princeton", "tsinghua",
}

TOP_TIER_LEADERBOARDS = {
    "chatbot arena", "swe-bench", "gaia", "arc-agi", "humaneval+",
}

TOP_TIER_VENUES = {
    "iclr", "icml", "neurips", "nature", "science",
}

# Number / magnitude pattern (for has_concrete_number check)
NUMBER_PATTERN = re.compile(
    r"(\d+(\.\d+)?[×x]|\d+(\.\d+)?\s*(亿|万|TB|GB|FLOPS|参数|tokens?)|\d{2,}\.?\d*\s*%|"
    r"SOTA|sota|首次|nm)",
    re.IGNORECASE,
)

# Paradigm-level keyword hints (LLM still confirms)
PARADIGM_HINTS = (
    "范式", "动摇", "首次", "突破", "新框架", "新定律", "重新定义",
    "scaling law", "证明", "theorem", "充要", "可识别",
)

# Industry-first keywords
INDUSTRY_FIRST_HINTS = (
    "行业首次", "全球首次", "首例", "首发", "首款",
)


@dataclass
class ClassificationResult:
    event_type: str | None
    m1: int
    m2: int
    m3: int
    m4: int
    m5: int
    constraint_pass: bool
    constraint_rule: str | None
    entity: CanonicalEntity
    canonical_event_key: str
    rationale: str  # 人类可读的判定理由


class HeadlineClassifier:
    """v8.0 headline strong-constraint classifier."""

    def __init__(
        self,
        tier_lookup: dict[str, str] | None = None,
        organization_lookup: dict[str, str] | None = None,
        cross_day_event_keys: set[str] | None = None,
    ) -> None:
        """
        Args:
            tier_lookup: {entity_name: "P0+"/"P0"/"P1"/"P2"} from p0_whitelist.yml
            organization_lookup: {entity_name: org from whitelist Bitable "组织"}
            cross_day_event_keys: set of canonical_event_keys already used in prior days
                (so cross-day resonance suppression works)
        """
        self.tier_lookup = tier_lookup or {}
        self.organization_lookup = organization_lookup or {}
        self.cross_day_event_keys = cross_day_event_keys or set()

    def classify_one(self, signal: Signal) -> ClassificationResult:
        # 1. Canonical entity
        org = self.organization_lookup.get(signal.author_name)
        entity = canonicalize(signal.author_name, organization=org)

        # 2. Determine event_type (heuristic + signal cues)
        event_type = self._guess_event_type(signal, entity)

        # 3. Compute 5-dim scores
        scores = self._score_dimensions(signal, entity, event_type)

        # 4. Build canonical_event_key (now uses raw_text-derived org for stability)
        significant_terms = self._extract_significant_terms(signal)
        event_key = build_event_key(entity, event_type, significant_terms,
                                      raw_text=signal.raw_text)

        # 5. Apply 8 strong-constraint rules
        passed, rule, rationale = self._evaluate_constraints(signal, entity, event_type, scores)

        # Cross-day suppression: if this event_key seen in prior days,
        # this signal is at best edge case enhancement, not new auto-headline
        if event_key in self.cross_day_event_keys and passed:
            passed = False
            rationale = f"(rule {rule} passed but cross-day resonance suppressed) | {rationale}"
            rule = None

        return ClassificationResult(
            event_type=event_type,
            m1=scores["m1"], m2=scores["m2"], m3=scores["m3"],
            m4=scores["m4"], m5=scores["m5"],
            constraint_pass=passed,
            constraint_rule=rule,
            entity=entity,
            canonical_event_key=event_key,
            rationale=rationale,
        )

    def apply_to_signal(self, signal: Signal) -> Signal:
        """Mutates Signal in place with classifier output."""
        result = self.classify_one(signal)
        signal.event_type = result.event_type
        signal.m1_score = result.m1
        signal.m2_score = result.m2
        signal.m3_score = result.m3
        signal.m4_score = result.m4
        signal.m5_score = result.m5
        signal.constraint_pass = result.constraint_pass
        signal.constraint_rule = result.constraint_rule
        signal.primary_org = result.entity.primary_org
        signal.canonical_event_key = result.canonical_event_key
        return signal

    def classify_many(self, signals: list[Signal]) -> list[Signal]:
        """Batch classify with cross-signal m4 resonance detection.

        Two-pass:
          Pass 1: classify each signal with default m4=1
          Pass 2: if event_key has ≥2 occurrences, boost m4 to ≥2 AND
                  RE-EVALUATE the strong-constraint rule with the new score dict
                  (rules ② / ⑤ depend on m4 ≥ 2)
        """
        # Pass 1
        results: list[tuple[Signal, ClassificationResult]] = []
        for sig in signals:
            r = self.classify_one(sig)
            results.append((sig, r))

        # Pass 2: count occurrences of each canonical_event_key
        from collections import Counter
        key_counts = Counter(r.canonical_event_key for _, r in results)

        for sig, r in results:
            if key_counts[r.canonical_event_key] >= 2 and r.m4 < 2:
                # Boost m4 due to in-batch resonance
                r.m4 = 2
                # Re-evaluate constraints with new score dict (rules ② / ⑤ use m4)
                new_scores = {
                    "m1": r.m1, "m2": r.m2, "m3": r.m3, "m4": r.m4, "m5": r.m5,
                }
                # Skip re-eval if already cross-day suppressed
                if r.constraint_rule != "_suppressed":
                    new_passed, new_rule, new_rationale = self._evaluate_constraints(
                        sig, r.entity, r.event_type, new_scores
                    )
                    # Only upgrade (don't downgrade an already-passing signal)
                    if new_passed and not r.constraint_pass:
                        r.constraint_pass = True
                        r.constraint_rule = new_rule
                        r.rationale = f"(m4 boost re-eval) {new_rationale}"

            # Apply final scores to signal
            sig.event_type = r.event_type
            sig.m1_score = r.m1
            sig.m2_score = r.m2
            sig.m3_score = r.m3
            sig.m4_score = r.m4
            sig.m5_score = r.m5
            sig.constraint_pass = r.constraint_pass
            sig.constraint_rule = r.constraint_rule
            sig.primary_org = r.entity.primary_org
            sig.canonical_event_key = r.canonical_event_key

        return [sig for sig, _ in results]

    # ====================================================
    # Stage 1: deterministic helpers
    # ====================================================

    def _tier_of(self, author_name: str) -> str:
        """Lookup tier. Defaults to P2."""
        return self.tier_lookup.get(author_name, "P2")

    def _is_p0_plus(self, author_name: str) -> bool:
        return self._tier_of(author_name) == "P0+"

    def _is_p0_or_above(self, author_name: str) -> bool:
        return self._tier_of(author_name) in ("P0+", "P0")

    def _is_top_tier_org(self, entity: CanonicalEntity) -> bool:
        return entity.primary_org in TOP_TIER_LABS

    def _has_concrete_number(self, signal: Signal) -> bool:
        text = " ".join(filter(None, [
            signal.raw_text, signal.summary_zh, signal.result_summary_zh,
            " ".join(signal.core_findings_zh or []),
        ]))
        return bool(NUMBER_PATTERN.search(text))

    def _has_paradigm_hint(self, signal: Signal) -> bool:
        text = " ".join(filter(None, [
            signal.raw_text, signal.summary_zh, signal.cognitive_takeaway_zh,
        ])).lower()
        return any(h.lower() in text for h in PARADIGM_HINTS)

    def _has_industry_first_hint(self, signal: Signal) -> bool:
        text = " ".join(filter(None, [
            signal.raw_text, signal.summary_zh,
        ]))
        return any(h in text for h in INDUSTRY_FIRST_HINTS)

    def _has_top_venue(self, signal: Signal) -> bool:
        text = (signal.raw_text or "").lower()
        return any(v in text for v in TOP_TIER_VENUES)

    def _has_top_leaderboard(self, signal: Signal) -> bool:
        text = (signal.raw_text or "").lower()
        return any(lb in text for lb in TOP_TIER_LEADERBOARDS)

    def _extract_significant_terms(self, signal: Signal) -> list[str]:
        """Extract key terms for canonical_event_key."""
        terms = list(signal.key_terms or [])
        # Add product/model names mentioned in text
        product_re = re.compile(r"(GPT-\d+(\.\d+)?|Claude\s+\d|Gemini\s+\d+(\.\d+)?|Llama\s+\d|"
                                r"Qwen[\d\.\-]*|DeepSeek\s*[VR]?\d*|Grok\s*\d*)", re.IGNORECASE)
        for m in product_re.finditer(signal.raw_text or ""):
            terms.append(m.group(0))
        return terms[:5]

    # ====================================================
    # Event-type guessing (heuristic; LLM can refine later)
    # ====================================================

    def _guess_event_type(self, signal: Signal, entity: CanonicalEntity) -> str | None:
        """Heuristic event type. Based on source / track / keywords.

        Order matters — check more specific events first.
        """
        if signal.source == "arxiv":
            return "②技术研究突破"

        text = (signal.raw_text or "")
        text_zh = text + " " + (signal.summary_zh or "")
        text_lower = text_zh.lower()

        # ⑦ Business action (priority before ⑧). Narrower keywords to avoid
        # catching opinion pieces that just mention "data centers" / "合作".
        if any(k in text_zh for k in ("收购", "acquire", "起诉", "lawsuit",
                                       "融资", "funding", "Series A", "Series B",
                                       "ipo", "运营利润", "盈利",
                                       "亿美元", "billion",
                                       "部署协议", "商业协议", "签署商业",
                                       "deployment deal", "rolled out at scale",
                                       "集成到", "integrated with",
                                       "营收同比", "营收增长", "operating profit")):
            return "⑦公司间商业动作"

        # ⑧ Personnel move (STRICTLY require move verb + person context)
        # 删除"founder"/"starting"等过宽词
        has_move_verb = any(k in text_zh for k in (
            "加入 Anthropic", "加入 OpenAI", "加入 Google", "加入 Meta",
            "joined Anthropic", "joined OpenAI", "joined Google", "joined Meta",
            "leaves OpenAI", "leaves Anthropic", "leaves Google",
            "离开 OpenAI", "离开 Anthropic", "离开 Google",
            "founded a new", "founding new lab", "starts new company",
            "宣布加入", "宣布离职", "co-founder of"
        ))
        if has_move_verb and entity.primary_person:
            return "⑧顶级人员变动"

        # ⑤ Benchmark / leaderboard
        if self._has_top_leaderboard(signal) or any(
            k in text_zh for k in ("榜单", "leaderboard", "arena", "rank ", "排名")
        ):
            return "⑤评测/榜单"

        # ⑥ Demo
        if any(k in text_zh for k in ("demo 视频", "演示视频", "连续运行",
                                       "real world demo", "连续 24")):
            return "⑥Demo/演示"

        # ③ Hardware/Infra
        if any(k in text_lower for k in ("scaling law", "hbm", "tflops", "晶体管",
                                          "transistor", "封装", "package", "光刻",
                                          "lithography", "ssd", "chip design")):
            return "③硬件/Infra突破"

        # ④ Executive commentary (P0+ person + comment verb)
        if entity.primary_person and self._is_p0_or_above(signal.author_name):
            if any(k in text_zh for k in ("评论", "表态", "提及", "预告", "comment",
                                           "stated", "milestone", "里程碑",
                                           "回应", "评价")):
                return "④大佬评论/观点"

        # ① Default for non-arxiv signals with product-like content
        # 必须含明确的 release verb — version pattern alone 不够 (避免误判 paper)
        if any(k in text_zh for k in ("发布", "release", "launch", "推出", "上线",
                                       "now available", "rolled out", "首发",
                                       "available now", "已上线")):
            return "①模型/产品发布"

        return None

    # ====================================================
    # 5-dim scoring (each 0-3)
    # ====================================================

    def _score_dimensions(
        self,
        signal: Signal,
        entity: CanonicalEntity,
        event_type: str | None,
    ) -> dict[str, int]:
        """Compute m1-m5 scores."""
        scores = {"m1": 0, "m2": 0, "m3": 0, "m4": 0, "m5": 0}

        # M1: 投研可操作性 (action-driving event types boost)
        if event_type in ("⑦公司间商业动作", "⑧顶级人员变动", "③硬件/Infra突破"):
            scores["m1"] = 3
        elif event_type == "①模型/产品发布":
            scores["m1"] = 2
        elif event_type in ("⑤评测/榜单", "④大佬评论/观点"):
            scores["m1"] = 1

        # M2: 实体级别 (P0+ company > P0 person > others)
        tier = self._tier_of(signal.author_name)
        if tier == "P0+":
            scores["m2"] = 3
        elif tier == "P0":
            scores["m2"] = 2
        elif tier == "P1":
            scores["m2"] = 1

        # M3: 数字震撼度
        if self._has_concrete_number(signal):
            scores["m3"] = 2
            # Boost if has "≥10x" or absolute records
            text = (signal.raw_text or "") + " " + (signal.summary_zh or "")
            if re.search(r"\d{2,}[×x]|\d{3,}\s*%", text):
                scores["m3"] = 3

        # M4: 跨信号共识 (computed in classify_many; default 1 for now)
        scores["m4"] = 1

        # M5: 范式动摇
        if self._has_paradigm_hint(signal):
            scores["m5"] = 2
            if event_type == "②技术研究突破" and self._has_top_venue(signal):
                scores["m5"] = 3

        return scores

    # ====================================================
    # Stage 2: 8 strong-constraint rules
    # ====================================================

    def _evaluate_constraints(
        self,
        signal: Signal,
        entity: CanonicalEntity,
        event_type: str | None,
        scores: dict[str, int],
    ) -> tuple[bool, str | None, str]:
        """Apply 8 constraint rules. Returns (passed, rule_id, rationale).

        Note: Some LLM-assisted labels are heuristically approximated here.
        In production, Stage 2 LLM would refine paradigm_level/strategy_shift etc.
        """
        author = signal.author_name

        # ① Model/Product release
        if event_type == "①模型/产品发布":
            text = signal.raw_text or ""
            # Author = P0+ official, OR raw_text 含顶级公司 + 旗舰版本号
            top_company_in_text = any(k in text for k in [
                "OpenAI", "Anthropic", "Google", "GoogleAI", "DeepMind",
                "Meta", "Microsoft", "xAI", "NVIDIA", "Apple",
                "DeepSeek", "Mistral", "Alibaba", "Qwen",
                "Hugging Face", "Sakana"
            ])
            has_flagship_version = bool(re.search(
                r"(GPT-\d+(\.\d+)?|Claude\s*\d|Gemini\s*\d+(\.\d+)?|"
                r"Llama\s*\d|Qwen[\d\.\-]*Max|DeepSeek\s*[VR]?\d*)",
                text, re.IGNORECASE,
            ))
            if (self._is_p0_plus(author)
                or (top_company_in_text and has_flagship_version)):
                if self._has_concrete_number(signal):
                    has_version_or_first = bool(re.search(r"\d+\.\d+|首次|首发", text))
                    if has_version_or_first:
                        return True, "①_model_product_release", \
                            f"P0+ (author or in-text) + version + concrete number"

        # ② Research breakthrough
        if event_type == "②技术研究突破":
            text = signal.raw_text or ""
            top_lab_in_text = any(k in text for k in [
                "OpenAI", "Anthropic", "Google", "DeepMind", "Meta",
                "Microsoft", "MSR", "NVIDIA", "Apple", "xAI", "Cerebras",
                "Sakana", "Stanford", "MIT", "CMU", "Princeton", "Berkeley",
            ])
            if ((self._is_p0_or_above(author) or top_lab_in_text)
                and self._has_paradigm_hint(signal)
                and (self._has_top_venue(signal) or scores["m4"] >= 2 or top_lab_in_text)):
                return True, "②_research_breakthrough", \
                    "P0 lab (author or in-text) + paradigm hint + evidence"

        # ③ Hardware/Infra breakthrough
        if event_type == "③硬件/Infra突破":
            text = signal.raw_text or ""
            text_lower = text.lower()
            # raw_text 提到顶级硬件公司 → 即使 author 不是 P0+ 也可考虑
            top_hw_in_text = any(k in text for k in (
                "Huawei", "华为", "NVIDIA", "AMD", "Intel", "TSMC", "Apple",
                "Cerebras", "Groq", "Tesla", "寒武纪", "摩尔线程"
            ))
            new_metric_signal = any(k in text_lower for k in (
                "scaling law", "新指标", "新衡量", "出口管制", "记录", "纪录",
                "首次", "突破", "新范式"
            ))
            if top_hw_in_text and new_metric_signal:
                return True, "③_hardware_infra_breakthrough", \
                    f"top hardware company in text + new metric/record signal"

        # ④ Executive commentary
        if event_type == "④大佬评论/观点":
            if self._is_p0_plus(author) or self._is_p0_or_above(author):
                text = (signal.raw_text or "")
                # 加 "里程碑/突破" 让 Greg Brockman 评论数学突破能 catch
                if any(k in text for k in ("即将", "未发布", "预告", "战略",
                                            "首次表态", "里程碑", "milestone",
                                            "突破", "联合创始人")):
                    return True, "④_executive_commentary", \
                        "P0 exec + new info OR milestone commentary"

        # ⑤ Leaderboard
        if event_type == "⑤评测/榜单":
            if self._has_top_leaderboard(signal) and self._is_p0_or_above(author):
                text = signal.raw_text or ""
                if "top 3" in text.lower() or "前 3" in text or "第一" in text \
                   or re.search(r"\d{2,}\s*%.*升至", text):
                    return True, "⑤_benchmark_leaderboard", \
                        "Top-tier leaderboard + P0+ model + first top-3 / 15pp jump"

        # ⑥ Demo
        if event_type == "⑥Demo/演示":
            if self._is_p0_plus(author) and self._is_top_tier_org(entity) \
               and self._has_industry_first_hint(signal):
                return True, "⑥_demo_showcase", \
                    "P0+ official + industry-first claim"

        # ⑦ Business action — STRICT to avoid catching opinion pieces
        if event_type == "⑦公司间商业动作":
            text = signal.raw_text or ""
            top_orgs_in_text = sum(
                1 for k in ["OpenAI", "Anthropic", "Google", "Meta", "Microsoft",
                            "xAI", "NVIDIA", "Apple", "DeepSeek", "Mistral",
                            "Alibaba", "Figure", "Tesla", "Hark", "GDM",
                            "DeepMind", "ElevenLabs"]
                if k in text
            )
            # 明确的财务数字 (dollar amount with units)
            has_concrete_dollar = bool(re.search(
                r"\$\s*\d+(\.\d+)?\s*[BMKbn]|"
                r"\d+(\.\d+)?\s*亿\s*美元|"
                r"\d+(\.\d+)?\s*亿\s*元|"
                r"\d+(\.\d+)?\s*billion|"
                r"Series\s*[ABCD]\b|"
                r"\d{3,}\s*million",
                text, re.IGNORECASE
            ))
            # 严格 deal verb (排除 "数据中心" / "合作" 等过宽词)
            strict_deal_verbs = ("洽谈", "收购", "融资 ", "签署商业协议",
                                  "部署协议", "rolled out at scale",
                                  "集成到", "integrated with",
                                  "营收同比", "运营利润", "operating profit",
                                  "Series A", "Series B")
            has_strict_deal_verb = any(k in text for k in strict_deal_verbs)

            # ⑦a: ≥2 P0+ companies + deal verb
            # ⑦b: ≥1 P0+ company + concrete dollar AND deal verb
            if (top_orgs_in_text >= 2 and has_strict_deal_verb) or \
               (top_orgs_in_text >= 1 and has_concrete_dollar and has_strict_deal_verb):
                return True, "⑦_business_action_between_companies", \
                    f"P0+ company + strict deal verb + (multi-party OR concrete $)"

        # ⑧ Personnel move
        if event_type == "⑧顶级人员变动":
            text = signal.raw_text or ""
            # 允许 raw_text 提到 P0 公司高管 + 移动动作
            has_p0_exec_in_text = any(k in text for k in (
                "OpenAI", "Anthropic", "Google", "Meta", "Microsoft", "DeepMind",
                "Karpathy", "联合创始人", "首席科学家", "Chief Scientist",
                "Co-founder", "Founder of"
            ))
            has_move = any(k in text for k in ("加入", "joined", "left", "离开",
                                                 "创立", "founded", "starting"))
            if (self._is_p0_plus(author) or has_p0_exec_in_text) and has_move:
                return True, "⑧_top_personnel_move", \
                    "P0+ exec (author or in text) + move action"

        # No constraint passed
        return False, None, "no constraint matched"
