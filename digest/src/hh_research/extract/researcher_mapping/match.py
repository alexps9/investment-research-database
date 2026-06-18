"""姓名/机构 normalize + 中等严格度匹配规则。"""
from __future__ import annotations

import re
import unicodedata

from pypinyin import Style, lazy_pinyin

# Latin Extended 字符手工映射（NFKD 无法分解的带笔画字母）
_LATIN_STROKE_MAP: dict[str, str] = {
    "đ": "d", "Đ": "d",
    "ø": "o", "Ø": "o",
    "ł": "l", "Ł": "l",
    "ß": "ss",
    "æ": "ae", "Æ": "ae",
    "œ": "oe", "Œ": "oe",
    "ð": "d", "Ð": "d",
    "þ": "th", "Þ": "th",
}
_LATIN_STROKE_RE = re.compile("|".join(re.escape(k) for k in _LATIN_STROKE_MAP))


def normalize_name(s: str) -> str:
    """NFKD 去音符 + 小写 + 去标点（保留空格、连字符）。"""
    if not s:
        return ""
    # 先替换 NFKD 无法分解的带笔画拉丁字母
    s = _LATIN_STROKE_RE.sub(lambda m: _LATIN_STROKE_MAP[m.group()], s)
    nfkd = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    lowered = no_accents.lower()
    cleaned = re.sub(r"[^\w\s\-]", " ", lowered)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _has_chinese(s: str) -> bool:
    return any("一" <= c <= "鿿" for c in s)


def _chinese_to_pinyin(s: str) -> list[str]:
    """陈天奇 → ['chen tianqi', 'chen tian qi']（姓在前，名连写 + 全分开两种形式）"""
    parts = lazy_pinyin(s, style=Style.NORMAL)
    if not parts:
        return []
    results = []
    if len(parts) >= 2:
        # 连写形式：chen tianqi
        results.append(f"{parts[0]} {''.join(parts[1:])}")
        # 全分开形式：chen tian qi
        if len(parts) > 2:
            results.append(" ".join(parts))
    else:
        results.append(parts[0])
    return results


def _initial_match(short: str, long: str) -> bool:
    """short='t dao', long='tri dao' → True (首字母 t 匹配 tri)"""
    short_parts = short.split()
    long_parts = long.split()
    if len(short_parts) != len(long_parts):
        return False
    for sp, lp in zip(short_parts, long_parts):
        if sp == lp:
            continue
        if len(sp) == 1 and lp.startswith(sp):
            continue
        return False
    return True


def match_name(candidate: str, page: str) -> bool:
    """中等档：normalize + 首字母缩写 + 子串 + 中英文别名"""
    c = normalize_name(candidate)
    p = normalize_name(page)
    if not c or not p:
        return False

    if c == p:
        return True

    if _initial_match(c, p) or _initial_match(p, c):
        return True

    c_tokens = set(c.split())
    p_tokens = set(p.split())
    if c_tokens and p_tokens and (c_tokens <= p_tokens or p_tokens <= c_tokens):
        return True

    if _has_chinese(candidate):
        for c_py_raw in _chinese_to_pinyin(candidate):
            c_py = normalize_name(c_py_raw)
            if not c_py:
                continue
            if c_py == p or _initial_match(c_py, p) or _initial_match(p, c_py):
                return True
            c_py_tokens = set(c_py.split())
            if c_py_tokens and (c_py_tokens <= p_tokens or p_tokens <= c_py_tokens):
                return True

    if _has_chinese(page):
        for p_py_raw in _chinese_to_pinyin(page):
            p_py = normalize_name(p_py_raw)
            if not p_py:
                continue
            if p_py == c or _initial_match(p_py, c) or _initial_match(c, p_py):
                return True
            p_py_tokens = set(p_py.split())
            if p_py_tokens and (p_py_tokens <= c_tokens or c_tokens <= p_py_tokens):
                return True

    return False


# 机构缩写对应表（双向匹配；含显式排除以防歧义）
ABBREVIATIONS: dict[str, list[str]] = {
    # 美国学校
    "mit": ["massachusetts institute of technology"],
    "cmu": ["carnegie mellon"],
    "ucb": ["uc berkeley", "berkeley", "university of california berkeley"],
    "ucla": ["university of california los angeles"],
    "uw": ["university of washington"],
    "uiuc": ["university of illinois urbana-champaign"],
    "nyu": ["new york university"],
    "gatech": ["georgia tech", "georgia institute of technology"],
    "umich": ["university of michigan"],
    "ucsd": ["university of california san diego"],
    # 中国学校
    "清华": ["tsinghua university", "tsinghua"],
    "北大": ["peking university", "peking"],
    "中科院": ["chinese academy of sciences", "cas"],
    "上交": ["shanghai jiao tong university", "sjtu"],
    "浙大": ["zhejiang university"],
    "复旦": ["fudan university"],
    "南大": ["nanjing university"],
    "港中文": ["chinese university of hong kong", "cuhk"],
    "港科大": ["hong kong university of science and technology", "hkust"],
    # 国际
    "ethz": ["eth zurich", "eth"],
    "tum": ["technical university of munich"],
    # 业界
    "google": ["google research", "google deepmind", "google brain"],
    "msr": ["microsoft research"],
    "fair": ["meta ai", "facebook ai research"],
    "ai2": ["allen institute for ai", "allen ai"],
    "上海ai lab": ["shanghai ai laboratory", "shanghai ai lab"],
}

# 显式排除（即使 normalize 后子串包含也 reject）
_EXPLICIT_EXCLUSIONS: list[tuple[str, str]] = [
    ("mit", "massachusetts general hospital"),
    ("mit", "mit lincoln laboratory"),
]

_AFFILIATION_FILLERS = {
    "university", "institute", "school", "department", "dept",
    "of", "the", "and", "&", "lab", "laboratory", "college", "faculty",
}


def normalize_affiliation(s: str) -> str:
    """小写 + 去标点 + 去无信息词。"""
    if not s:
        return ""
    lowered = s.lower()
    cleaned = re.sub(r"[^\w\s一-鿿]", " ", lowered)
    tokens = cleaned.split()
    keep = [t for t in tokens if t not in _AFFILIATION_FILLERS]
    return " ".join(keep)


def _check_exclusion(candidate_norm: str, page_norm: str) -> bool:
    """True if (candidate, page) hits an explicit-exclusion pair."""
    for excl_a, excl_b in _EXPLICIT_EXCLUSIONS:
        a_norm = normalize_affiliation(excl_a)
        b_norm = normalize_affiliation(excl_b)
        if (candidate_norm == a_norm and b_norm in page_norm) or (
            candidate_norm == b_norm and a_norm in page_norm
        ):
            return True
    return False


def match_affiliation(candidate: str, page_list: list[str]) -> bool:
    """候选机构 vs 页面机构列表，任一通过即 True。"""
    if not candidate or not page_list:
        return False
    c_norm = normalize_affiliation(candidate)
    if not c_norm:
        return False

    for page in page_list:
        p_norm = normalize_affiliation(page)
        if not p_norm:
            continue
        if _check_exclusion(c_norm, p_norm):
            continue
        if c_norm in p_norm or p_norm in c_norm:
            return True
        # 缩写映射（双向）
        candidate_lower = candidate.strip().lower()
        page_lower = page.strip().lower()
        if candidate_lower in ABBREVIATIONS:
            for expansion in ABBREVIATIONS[candidate_lower]:
                if normalize_affiliation(expansion) in p_norm:
                    return True
        if page_lower in ABBREVIATIONS:
            for expansion in ABBREVIATIONS[page_lower]:
                if normalize_affiliation(expansion) in c_norm:
                    return True
    return False
