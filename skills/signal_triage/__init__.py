"""Signal triage skill — deterministic scoring, triangulation & dedup.

Turns "should we surface this?" from a pure-LLM call into structured signal
engineering that runs *before* any model is involved:

  1. tier 分级    — who said it (first-hand source > analyst > relayer)
  2. engagement   — how hot (likes/retweets × tier × originality bonus)
  3. triangulate  — multi-source corroboration (same event across N sources)
  4. dedupe       — collapse a multi-source cluster to one representative

Ported from the alert pipeline's ``score.py``. The LLM dedup-escalation is
optional here (pass ``llm_same_event=callable``); by default clustering is fully
deterministic so the skill stays dependency-light (jieba is used when available,
otherwise a regex tokenizer is used as fallback).

Each signal is a dict with at least ``text``; optional ``username``, ``likes``,
``retweets``, ``source_tier`` (twitter/official/media/aggregator).
"""
from __future__ import annotations

import re
from typing import Any, Callable, Optional

# ── Tier weights ────────────────────────────────────────────
TIER_WEIGHT = {"tier_1a": 4, "tier_1b": 3, "tier_2": 2, "tier_3": 1}
TIER_RANK = {"tier_1a": 5, "tier_1b": 4, "tier_2": 3, "tier_3": 2}

TIER_1A_HANDLES = {
    "OpenAI", "OpenAIDevs", "AnthropicAI", "GoogleDeepMind", "GoogleAI",
    "googleaidevs", "Meta", "AIatMeta", "MistralAI", "xai",
    "sama", "gdb", "demishassabis", "JeffDean", "ylecun",
    "DrJimFan", "karpathy", "ilyasut", "NVIDIAAI", "nvidia",
}


def assign_tier(item: dict) -> str:
    """Assign a tier from source_tier + account handle."""
    st = item.get("source_tier", "twitter")
    if st == "official":
        return "tier_1a"
    if st == "media":
        return "tier_2"
    if st == "aggregator":
        return "tier_3"
    if item.get("username") in TIER_1A_HANDLES:
        return "tier_1a"
    return "tier_1b"


def engagement_score(item: dict) -> float:
    """Engagement × tier weight × originality. Retweets weigh more than likes."""
    tier_w = TIER_WEIGHT.get(item.get("tier") or assign_tier(item), 1)
    likes = item.get("likes") or 0
    retweets = item.get("retweets") or 0
    raw = likes * 1 + retweets * 3
    if raw == 0 and item.get("source_tier") in ("official", "media"):
        raw = 10  # baseline so RSS/media isn't zeroed out
    is_rt = item.get("text", "").startswith("RT @")
    originality = 0.3 if is_rt else 1.0
    return raw * tier_w * originality


# ── Tokenisation & same-event heuristics ────────────────────
_STOPWORDS = set(
    "的 了 在 是 我 有 和 就 不 人 都 一 上 也 很 到 说 要 去 你 会 这 那 他 它 们 "
    "the a an and or but in on at to of for with is are was be been have has new "
    "ai model models that this it its will from".split()
)

_CJK_ALIASES = {
    "谷歌": "google", "英伟达": "nvidia", "微软": "microsoft", "苹果": "apple",
    "亚马逊": "amazon", "英特尔": "intel", "特斯拉": "tesla", "三星": "samsung",
    "阿里": "alibaba", "阿里巴巴": "alibaba", "腾讯": "tencent", "字节": "bytedance",
    "百度": "baidu", "华为": "huawei", "小米": "xiaomi", "月之暗面": "kimi",
    "智谱": "zhipu", "通义": "qwen", "千问": "qwen", "黄仁勋": "huang",
    "实时": "realtime", "翻译": "translation", "语音": "speech", "模型": "model",
    "融资": "funding", "估值": "valuation", "收购": "acquisition", "上市": "ipo",
    "芯片": "chip", "算力": "compute", "数据中心": "datacenter", "机器人": "robot",
    "裁员": "layoff", "发布": "launch", "合作": "partnership", "投资": "invest",
}

# Core proper nouns (the event "subject"). Two signals sharing >=2 of these are
# almost certainly the same event regardless of each source's modifier words.
STRONG_ENTITIES = {
    "openai", "anthropic", "google", "deepmind", "meta", "microsoft", "nvidia",
    "apple", "intel", "tesla", "spacex", "databricks", "perplexity",
    "mistral", "xai", "amazon", "tsmc", "samsung",
    "gpt", "claude", "gemini", "llama", "grok", "qwen", "kimi", "deepseek",
    "glm", "minimax", "tpu", "gpu", "hbm",
    "通义", "千问", "月之暗面", "智谱", "英伟达", "黄仁勋", "阿里", "字节", "腾讯",
}

# Capital/business *action* words are event "types", not "subjects" — dropped
# from tokens so two unrelated funding stories don't collide on them.
_CAPITAL_ACTION_WORDS = {
    "融资", "估值", "收购", "并购", "上市", "代工", "投资", "轮", "美元", "亿美元",
    "万美元", "亿元", "万元", "完成", "公司", "旗下", "宣布", "据报道", "据悉",
    "初创", "初创公司", "完成融资", "轮融资",
    "funding", "valuation", "acquisition", "ipo", "invest", "billion", "million",
}


def _cjk_words(part: str) -> list[str]:
    """Segment a CJK run — jieba if installed, else contiguous-run fallback."""
    try:
        import jieba  # type: ignore
        return list(jieba.cut(part))
    except Exception:
        # Fallback: keep the whole run; downstream length filter handles it.
        return [part]


def tokens(text: str) -> set:
    """Keyword set: english words (>=3 letters) + CJK words (>=2 chars), minus
    stopwords/action-words, plus cross-language aliases for CJK entities."""
    low = re.sub(r"https?://\S+", "", text.lower())
    low = re.sub(r"@\w+", "", low)
    drop = _STOPWORDS | _CAPITAL_ACTION_WORDS
    toks = {t for t in re.findall(r"[a-z]{3,}", low) if t not in drop}
    for part in re.findall(r"[\u4e00-\u9fff]+", low):
        for word in _cjk_words(part):
            if len(word) >= 2 and word not in drop:
                toks.add(word)
    for cjk, en in _CJK_ALIASES.items():
        if cjk in text and en not in _CAPITAL_ACTION_WORDS:
            toks.add(en)
    return toks


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def same_event(a: set, b: set, threshold: float = 0.18) -> bool:
    """Same event if Jaccard passes, or >=2 shared strong entities, or
    >=1 strong entity + >=3 shared tokens (covers cross-language dilution)."""
    if _jaccard(a, b) >= threshold:
        return True
    shared = a & b
    shared_entities = shared & STRONG_ENTITIES
    if len(shared_entities) >= 2:
        return True
    return len(shared_entities) >= 1 and len(shared) >= 3


def maybe_same_event(a: set, b: set) -> bool:
    """Gray zone: not confidently same, but suspicious enough to escalate."""
    if same_event(a, b, 0.18):
        return False
    shared = a & b
    if len(shared & STRONG_ENTITIES) >= 1:
        return True
    if len(shared) >= 2:
        return True
    long_proper = {
        t for t in shared
        if (t.isascii() and len(t) >= 5) or (not t.isascii() and len(t) >= 3)
    }
    return len(long_proper) >= 1


def triangulate(
    items: list,
    threshold: float = 0.18,
    llm_same_event: Optional[Callable[[str, str], bool]] = None,
) -> None:
    """Cluster this batch by keyword overlap; annotate each item in place with
    ``cluster_id`` / ``source_count`` / ``verified`` / ``cluster_sources``.

    ``llm_same_event(text_a, text_b) -> bool`` (optional) resolves gray-zone
    pairs; without it gray-zone pairs stay separate (fully deterministic)."""
    token_sets = [tokens(it.get("text", "")) for it in items]
    cluster_of = [-1] * len(items)
    clusters: list[list[int]] = []

    order = sorted(range(len(items)), key=lambda i: engagement_score(items[i]), reverse=True)
    for i in order:
        if cluster_of[i] != -1 or not token_sets[i]:
            continue
        cid = len(clusters)
        group = [i]
        cluster_of[i] = cid
        for j in order:
            if cluster_of[j] != -1 or j == i or not token_sets[j]:
                continue
            if same_event(token_sets[i], token_sets[j], threshold):
                cluster_of[j] = cid
                group.append(j)
            elif llm_same_event and maybe_same_event(token_sets[i], token_sets[j]):
                if llm_same_event(items[i].get("text", "")[:300], items[j].get("text", "")[:300]):
                    cluster_of[j] = cid
                    group.append(j)
        clusters.append(group)

    for cid, group in enumerate(clusters):
        source_list = sorted({items[k].get("username", "") for k in group} - {""})
        n = len({items[k].get("username", "") for k in group})
        for k in group:
            items[k]["cluster_id"] = cid
            items[k]["source_count"] = n
            items[k]["verified"] = n >= 2
            items[k]["cluster_sources"] = source_list

    for it in items:
        it.setdefault("cluster_id", -1)
        it.setdefault("source_count", 1)
        it.setdefault("verified", False)
        it.setdefault("cluster_sources", [it.get("username", "")])


def dedupe_clusters(items: list) -> list:
    """Keep one representative per cluster (highest tier, then engagement).
    Unclustered items (cluster_id=-1) are all kept."""
    best_by_cluster: dict[int, dict] = {}
    singles: list[dict] = []
    for it in items:
        cid = it.get("cluster_id", -1)
        if cid == -1:
            singles.append(it)
            continue
        cur = best_by_cluster.get(cid)
        if cur is None:
            best_by_cluster[cid] = it
            continue
        key_new = (TIER_RANK.get(it.get("tier"), 0), it.get("score", 0))
        key_cur = (TIER_RANK.get(cur.get("tier"), 0), cur.get("score", 0))
        if key_new > key_cur:
            best_by_cluster[cid] = it
    return singles + list(best_by_cluster.values())


def triage_signals(
    signals: list[dict],
    dedupe: bool = True,
    llm_same_event: Optional[Callable[[str, str], bool]] = None,
) -> dict[str, Any]:
    """Score + triangulate (+ optionally dedupe) a batch of raw signals.

    Mutates each signal in place (adds tier/score/verified/cluster_*) and returns
    a summary:

        {
          "scored": [...all signals with tier/score/verified...],
          "deduped": [...one per event cluster...],   # only if dedupe=True
          "verified_count": int,
          "cluster_count": int,
        }
    """
    for it in signals:
        it["tier"] = assign_tier(it)
        it["score"] = round(engagement_score(it), 1)
    triangulate(signals, llm_same_event=llm_same_event)

    verified_count = sum(1 for it in signals if it.get("verified"))
    cluster_count = len({it.get("cluster_id", -1) for it in signals} - {-1})

    out: dict[str, Any] = {
        "scored": signals,
        "verified_count": verified_count,
        "cluster_count": cluster_count,
    }
    if dedupe:
        out["deduped"] = dedupe_clusters(signals)
    return out


__all__ = [
    "triage_signals", "triangulate", "dedupe_clusters",
    "assign_tier", "engagement_score",
    "tokens", "same_event", "maybe_same_event",
    "STRONG_ENTITIES", "TIER_RANK", "TIER_WEIGHT", "TIER_1A_HANDLES",
]
