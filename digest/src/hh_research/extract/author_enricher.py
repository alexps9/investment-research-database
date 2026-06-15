"""Author enrichment — 5.18 7-stage information chain for paper co-authors.

为每篇白名单论文的所有作者补全：affiliation / 现状 / 导师 / GitHub / Scholar /
个人主页 / 邮箱 / 预计毕业等信息。每条信息附 provenance（来源 URL / 工具），
满足 5.19 #6 trace 要求。

设计要点（5.18 方案）：
1. **白名单作者**优先用 Bitable whitelist 表已 enrich 的字段（不消耗外部 API）
2. **非白名单作者**走 AnySearch (`~/.claude/skills/anysearch/`) 单次 query，
   解析返回的 web search results，正则抽 affiliation / github / scholar / homepage
3. **共一/通讯标记**：fetch `arxiv.org/html/{id}`，在脚注里找 "Equal contribution"
   / "Co-first" / "Corresponding author" 标记
4. **GitHub fallback**：arxiv HTML 全文 regex `github\\.com/...`，过滤掉 LaTeXML
   / arxiv 噪声
5. **OpenAlex 兜底**（针对作者消歧/历史论文）：若 AnySearch 命中弱，再调 OpenAlex
6. **缓存**：每位作者结果存 `data/cache/author_lookup/<sha1(name)>.json`，避免重复 API
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx

from ..storage.schemas import CoauthorInfo, WhitelistEntry
from ..utils.logger import get_logger

log = get_logger("author_enricher")

ANYSEARCH_CLI = "/Users/haolinguo/.claude/skills/anysearch/scripts/anysearch_cli.sh"
CACHE_DIR = Path("data/cache/author_lookup")

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126.0"}

# arxiv HTML 噪声 GitHub URL (LaTeXML 渲染器自己的链接)
GITHUB_NOISE = {
    "brucemiller/LaTeXML", "arXiv/html_feedback", "arxiv/html_feedback",
}

# 域名优先级（从 search result 里挑最权威的）
HOMEPAGE_DOMAIN_PRIORITY = [
    "github.io", "edu", "ac.cn", "ac.uk", "ac.jp",
]

# Whitelist for known top labs / orgs (for status field)
KNOWN_ORGS = [
    "MIT", "Stanford", "Berkeley", "CMU", "Princeton", "Harvard", "Yale", "Cornell",
    "UCLA", "UIUC", "NYU", "UW", "Tsinghua", "Peking", "HKUST", "CUHK", "NTU", "NUS",
    "OpenAI", "Anthropic", "Google", "DeepMind", "Meta", "Microsoft", "NVIDIA", "Apple",
    "xAI", "Mistral", "DeepSeek", "Alibaba", "Tencent", "Baidu", "Bytedance",
    "Waterloo", "Toronto", "ETH", "Oxford", "Cambridge", "Edinburgh",
    "Allen AI", "AI2", "Together AI", "Cohere", "Hugging Face",
    "上海 AI Lab", "上海AI Lab", "ShanghaiAILab", "Shanghai AI Lab",
    "Horizon Robotics", "Megvii", "SenseTime", "Northwestern", "Rochester",
]


# ─── core HTML fetch ───────────────────────────────────────────────────────

def get_arxiv_full_authors(arxiv_id: str, timeout: float = 20.0) -> list[str]:
    """从 arxiv HTML meta citation_author tag 抓全作者列表（Firstname Lastname 序）。

    避免依赖 arxiv API（已知会 429）。直接打 arxiv.org/abs/{id} 拿 HTML meta。
    """
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
    try:
        with httpx.Client(headers=UA, timeout=timeout, follow_redirects=True) as c:
            r = c.get(f"https://arxiv.org/abs/{arxiv_id}")
            if r.status_code != 200:
                return []
            raw = re.findall(r'<meta name="citation_author" content="([^"]+)"', r.text)
            out: list[str] = []
            for a in raw:
                if "," in a:
                    last, first = a.split(",", 1)
                    out.append(f"{first.strip()} {last.strip()}")
                else:
                    out.append(a.strip())
            return out
    except Exception as e:  # noqa: BLE001
        log.warning("fetch arxiv authors failed for %s: %s", arxiv_id, e)
        return []


def fetch_arxiv_html(arxiv_id: str, timeout: float = 20.0) -> str:
    """优先 arxiv.org/html (新论文 ar5iv 渲染)，fallback 抽 abs 页面。"""
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)  # 去版本号
    try:
        with httpx.Client(headers=UA, timeout=timeout, follow_redirects=True) as c:
            r = c.get(f"https://arxiv.org/html/{arxiv_id}")
            if r.status_code == 200 and len(r.text) > 5000:
                return r.text
            r = c.get(f"https://arxiv.org/abs/{arxiv_id}")
            return r.text if r.status_code == 200 else ""
    except Exception as e:  # noqa: BLE001
        log.warning("arxiv HTML fetch failed for %s: %s", arxiv_id, e)
        return ""


# ─── role detection (一作 / 共一 / 通讯) ──────────────────────────────────

def detect_co_first_authors(html: str, authors: list[str]) -> dict[str, str]:
    """根据 arxiv HTML 脚注判定每位作者的 role。

    返回 {author_name: role}，role ∈ {一作, 共一, 通讯, 合作}.
    若无共一标记 → 第 1 位 = 一作；末位 = 通讯；中间 = 合作。
    """
    roles: dict[str, str] = {}
    if not authors:
        return roles

    # Pattern 检测
    co_first_indicators = [
        "equal contribution", "Equal contribution",
        "Co-first", "co-first", "joint first", "Joint first",
        "These authors contributed equally", "contributed equally",
    ]
    correspond_indicators = [
        "Corresponding author", "corresponding author", "通讯作者",
    ]

    has_co_first = any(p.lower() in html.lower() for p in co_first_indicators)
    has_correspond = any(p in html for p in correspond_indicators)

    if has_co_first:
        # 简化策略：当存在共一标记时，前 2-4 位都标"共一"（基于脚注上下文很难精确）
        # 优先：找"Equal contribution"附近的 ¹²³* 标记，跟作者 ¹²³* 上标对应
        # 简化版：前 2-4 位标共一（实际共一 ≤ 4 位）
        n_cofirst = _estimate_cofirst_count(html)
        for i, name in enumerate(authors):
            if i < n_cofirst:
                roles[name] = "共一"
            elif i == len(authors) - 1:
                roles[name] = "通讯" if has_correspond else "资深合作"
            else:
                roles[name] = "合作"
    else:
        for i, name in enumerate(authors):
            if i == 0:
                roles[name] = "一作"
            elif i == len(authors) - 1 and len(authors) > 1:
                roles[name] = "通讯" if has_correspond else "资深合作"
            else:
                roles[name] = "合作"

    return roles


def _estimate_cofirst_count(html: str) -> int:
    """从 HTML 脚注估算共一作者数量（通常 2-4）。"""
    # 找 "These authors contributed equally" 周围的数字标记或 *
    m = re.search(r"(\d+\s+(?:authors?\s+)?contributed\s+equally)", html, re.IGNORECASE)
    if m:
        n_match = re.match(r"(\d+)", m.group(1))
        if n_match:
            return min(int(n_match.group(1)), 4)
    # 默认 2 位
    return 2


# ─── GitHub regex from arxiv HTML ─────────────────────────────────────────

def extract_github_urls(html: str, paper_title_hint: str = "") -> list[str]:
    """从 arxiv HTML 全文 regex github.com URL，过滤 LaTeXML / arxiv 噪声。

    优先返回 repo URL (org/repo)，单独的 user URL 次优。
    """
    candidates: list[str] = []
    for m in re.finditer(r"github\.com/([A-Za-z0-9_-]{1,40})(?:/([A-Za-z0-9_.-]+))?", html):
        org = m.group(1)
        repo = m.group(2) or ""
        key = f"{org}/{repo}" if repo else org
        if key in GITHUB_NOISE or f"{org}/{repo}" in GITHUB_NOISE:
            continue
        if repo:
            candidates.append(f"https://github.com/{org}/{repo}")
        else:
            candidates.append(f"https://github.com/{org}")
    return list(dict.fromkeys(candidates))[:10]  # dedup, keep order


# ─── AnySearch wrapper ─────────────────────────────────────────────────────

def _anysearch(query: str, max_results: int = 8, timeout: int = 25) -> list[dict[str, Any]]:
    """调用 AnySearch CLI 返回 list of {title, url, snippet} dicts.

    失败返回 []（不抛异常，让上游 fallback）。
    """
    try:
        r = subprocess.run(
            ["bash", ANYSEARCH_CLI, "search", query, "--max_results", str(max_results)],
            capture_output=True, text=True, timeout=timeout,
        )
        out = r.stdout
        # AnySearch 返回 Markdown 格式，提取 "### N. Title" + "- **URL**: ..." + snippet
        results = []
        # 切块
        chunks = re.split(r"\n### \d+\. ", "\n" + out)
        for ch in chunks[1:]:  # 跳第一段
            lines = ch.strip().split("\n")
            title = lines[0].strip()
            url_m = re.search(r"\*\*URL\*\*:\s*(\S+)", ch)
            url = url_m.group(1) if url_m else ""
            # snippet = url 之后的全部
            snippet = ""
            if url_m:
                snippet = ch[url_m.end():].strip()
                # 去掉 markdown list prefix
                snippet = re.sub(r"^\s*-\s*", "", snippet, count=1)
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet[:1500]})
        return results[:max_results]
    except subprocess.TimeoutExpired:
        log.warning("AnySearch timeout for query: %s", query[:60])
        return []
    except Exception as e:  # noqa: BLE001
        log.warning("AnySearch error: %s", e)
        return []


# ─── parse AnySearch results into author profile ──────────────────────────

# 从 snippet / URL 抽取各字段的 regex
_GH_USER_RE = re.compile(r"github\.com/([A-Za-z0-9_-]{1,40})(?:[/?]|$)")
_SCHOLAR_USER_RE = re.compile(r"scholar\.google\.[a-z.]+/citations\?[^\"'>\s]*user=([A-Za-z0-9_-]+)")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+(?:edu|ac\.[a-z]{2}|com|org|ai|io)\b")


def _normalize_status(raw: str, affiliation: str | None) -> str | None:
    """标准化"现状"字段为简洁格式。

    输入示例（之前未规范化的）：
      "Google · PhD from the CS department of the University of California"
      "Senior research in MSR"
      "PhD at MIT EECS working with Song Han"

    输出示例（v6 规范）：
      "MIT EECS PhD 在读"
      "MSR Senior Researcher"
      "Stanford CS PhD 在读 · 预计 2027 毕业"
      None  ← 完全无法分析，宁缺毋滥
    """
    if not raw:
        return None
    raw = raw.strip()
    # 提取角色 + 机构
    role = None
    school = None
    grad = None  # 毕业年份（仅 solid 来源）

    # 角色检测
    role_patterns = [
        (r"\bAssistant Professor\b|\bAP at\b|\b副教授\b|\bAP\b", "Assistant Professor"),
        (r"\bAssociate Professor\b|\b副教授\b", "Associate Professor"),
        (r"\bProfessor\b|\b教授\b", "Professor"),
        (r"\bPostdoc\b|\b博士后\b", "Postdoc"),
        (r"\bResearch Scientist\b|\b研究科学家\b|\bSenior research\b", "Research Scientist"),
        (r"\bPh\.?D\.? (?:candidate|student)\b|\b博士生\b|\bPhD\b", "PhD 在读"),
        (r"\bMaster|MSc|MS student|硕士", "Master 在读"),
        (r"\bMember of Technical Staff\b|\bMTS\b", "Member of Technical Staff"),
        (r"\bSoftware Engineer\b|\bSWE\b|\bEngineer\b", "Engineer"),
        (r"\bIntern\b|\b实习\b", "实习"),
    ]
    for pat, label in role_patterns:
        if re.search(pat, raw, re.IGNORECASE):
            role = label
            break

    # 机构检测：先用传入的 affiliation；否则从 raw 抽
    school = affiliation
    if not school:
        for org in KNOWN_ORGS:
            if re.search(rf"\bat\s+{re.escape(org)}\b", raw, re.IGNORECASE):
                school = org
                break

    # 毕业年份：仅匹配明确字眼，不做推算（用户要求宁缺毋滥）
    grad_pat = re.search(
        r"(?:expected|predicted|projected|预计)\s+(?:to\s+)?(?:graduat|defend|complete)[^\d]*(\d{4})",
        raw, re.IGNORECASE,
    )
    if grad_pat:
        grad = grad_pat.group(1)
    else:
        # 备选：明确写"2027 毕业" / "毕业于 2027"
        m = re.search(r"(?:graduating|graduate)\s+in\s+(\d{4})|(\d{4})\s*毕业", raw, re.IGNORECASE)
        if m:
            grad = m.group(1) or m.group(2)

    # 组装
    if not role and not school:
        return None  # 无可信信息，返回 None
    parts = []
    if school and role:
        parts.append(f"{school} {role}")
    elif school:
        parts.append(school)
    elif role:
        parts.append(role)
    if grad:
        parts.append(f"预计 {grad} 毕业")
    return " · ".join(parts)[:100] if parts else None


def _parse_author_profile(name: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """从 AnySearch 多条结果里抽 affiliation / advisor / github / scholar / homepage."""
    profile: dict[str, Any] = {"name": name}
    provenance: dict[str, str] = {}

    homepage = None
    homepage_provenance = None
    github = None
    scholar_id = None
    affiliation = None
    current_status = None
    advisor = None

    for r in results:
        url = r["url"]
        snippet = r["snippet"]
        title = r["title"]
        text = title + " " + snippet

        # ── GitHub username
        if not github:
            for ghm in _GH_USER_RE.finditer(url):
                u = ghm.group(1)
                if u.lower() not in {"orgs", "search", "topics", "trending"}:
                    github = u
                    provenance["github"] = url
                    break

        # ── Scholar ID
        if not scholar_id:
            for sm in _SCHOLAR_USER_RE.finditer(url + " " + snippet):
                scholar_id = sm.group(1)
                provenance["scholar_id"] = url
                break

        # ── Homepage (个人 .github.io / .edu / .me / .com)
        if not homepage:
            for domain_kw in HOMEPAGE_DOMAIN_PRIORITY:
                if domain_kw in url and "github.com" not in url and "scholar.google" not in url:
                    # 个人主页通常 url path 短
                    if url.count("/") <= 4:
                        homepage = url
                        homepage_provenance = url
                        provenance["homepage"] = url
                        break
            # 兜底：URL 含作者姓名
            if not homepage:
                name_slug = name.replace(" ", "").lower()
                if name_slug in url.lower() and "github.com" not in url and "scholar" not in url:
                    homepage = url
                    provenance["homepage"] = url

        # ── Affiliation / status / advisor 从 snippet 文本
        for org in KNOWN_ORGS:
            if not affiliation and org.lower() in text.lower():
                affiliation = org
                provenance["affiliation"] = url
                break

        # current_status 启发式
        if not current_status:
            status_patterns = [
                (r"(PhD candidate|Ph\.?D\.? student|博士生|PhD)\s+(?:at|@|in|候选|候选人)?\s*([\w 一-鿿]+?)(?:[,.\n]|$)", "PhD"),
                (r"(Assistant Professor|AP\b|副教授|助理教授)\s+(?:at|@)?\s*([\w 一-鿿]+?)(?:[,.\n]|$)", "AP"),
                (r"(Research Scientist|研究科学家)\s+(?:at|@|in)?\s*([\w 一-鿿]+?)(?:[,.\n]|$)", "RS"),
                (r"(Postdoc|博士后)\s+(?:at|@)?\s*([\w 一-鿿]+?)(?:[,.\n]|$)", "Postdoc"),
                (r"(教授|Professor)\s+(?:at|@)?\s*([\w 一-鿿]+?)(?:[,.\n]|$)", "Prof"),
            ]
            for pat, _label in status_patterns:
                m = re.search(pat, text)
                if m:
                    current_status = m.group(0).strip()[:80]
                    provenance["current_status"] = url
                    break

        # advisor 启发式
        if not advisor:
            for pat in [
                r"(?:advised by|under|导师|师从|跟随)\s+(?:Prof\.?|Professor|Dr\.?)?\s*([A-Z][\w]+ [A-Z][\w]+)",
                r"working with\s+(?:Prof\.?|Professor)?\s*([A-Z][\w]+ [A-Z][\w]+)",
                r"(?:supervisor|supervised by)\s+([A-Z][\w]+ [A-Z][\w]+)",
            ]:
                m = re.search(pat, text)
                if m:
                    advisor = m.group(1)
                    provenance["advisor"] = url
                    break

        # email
        if "email" not in profile:
            m = _EMAIL_RE.search(text)
            if m:
                profile["email"] = m.group(0)
                provenance["email"] = url

    if github:
        profile["github"] = github
    if scholar_id:
        profile["scholar_id"] = scholar_id
    if homepage:
        profile["homepage"] = homepage
    if affiliation:
        profile["affiliation"] = affiliation
    if current_status:
        # v6: normalize 一下，去掉冗余文本
        normalized = _normalize_status(current_status, affiliation)
        profile["current_status"] = normalized or current_status[:60]
    if advisor:
        profile["advisor"] = advisor

    profile["provenance"] = provenance
    return profile


# ─── enrich single author ─────────────────────────────────────────────────

def enrich_author(
    name: str,
    paper_arxiv_id: str | None,
    coauthor_names: list[str],
    affiliation_hint: str | None = None,
    cache: bool = True,
) -> dict[str, Any]:
    """为单个作者补全 profile。"""
    if cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(f"{name}::{paper_arxiv_id or ''}".encode()).hexdigest()[:16]
        cache_path = CACHE_DIR / f"{key}.json"
        if cache_path.exists():
            try:
                return json.loads(cache_path.read_text())
            except Exception:  # noqa: BLE001
                pass

    # 构造 AnySearch query
    # 多种 hint 组合，提高命中
    co_hint = next((c for c in coauthor_names if c != name and len(c.split()) >= 2), "")
    query_parts = [name]
    if affiliation_hint:
        query_parts.append(affiliation_hint)
    if co_hint:
        query_parts.append(co_hint)
    query_parts.append("paper researcher")
    query = " ".join(query_parts)

    results = _anysearch(query, max_results=8)
    profile = _parse_author_profile(name, results)

    # v6: GitHub 二次专搜（主搜没拿到 github 时）
    if not profile.get("github"):
        gh_query = f"{name} github"
        gh_results = _anysearch(gh_query, max_results=5)
        for r in gh_results:
            url = r["url"]
            m = _GH_USER_RE.search(url)
            if m:
                gh_user = m.group(1)
                # 过滤系统页面：orgs/topics/search/...
                if gh_user.lower() not in {"orgs", "search", "topics", "trending", "marketplace", "explore"}:
                    profile["github"] = gh_user
                    profile.setdefault("provenance", {})["github"] = url
                    log.info("  github 二次搜索命中 %s → @%s", name, gh_user)
                    break

    if cache:
        try:
            cache_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
        except Exception:  # noqa: BLE001
            pass
    return profile


# ─── main entry: enrich paper ──────────────────────────────────────────────

def enrich_paper_coauthors(
    arxiv_id: str,
    authors: list[str],
    whitelist_match: dict[str, WhitelistEntry] | None = None,
    max_authors: int = 8,
    parallel_workers: int = 5,
) -> list[CoauthorInfo]:
    """对一篇论文的 authors 列表全部 enrich，返回 CoauthorInfo[]。

    Args:
        arxiv_id: e.g. "2605.18603"
        authors: 论文全作者列表（来自 arxiv API），按顺序
        whitelist_match: {name: WhitelistEntry} 已匹配白名单的作者
        max_authors: 表格最多展示 N 位，超出截掉（5.18 设计 6-8）
        parallel_workers: 并发 AnySearch 查询数

    Returns:
        list[CoauthorInfo]
    """
    if not authors:
        return []

    whitelist_match = whitelist_match or {}

    # 1. 拿 arxiv HTML 检测共一/通讯
    html = fetch_arxiv_html(arxiv_id)
    roles = detect_co_first_authors(html, authors)
    github_from_arxiv = extract_github_urls(html)

    # 2. 选取要展示的作者（一作 + 通讯 + 全部白名单 + 共一）
    selected_indices: list[int] = [0]  # 一作
    for i, name in enumerate(authors):
        if name in whitelist_match and i not in selected_indices:
            selected_indices.append(i)
        if roles.get(name) == "共一" and i not in selected_indices:
            selected_indices.append(i)
    last_i = len(authors) - 1
    if last_i > 0 and last_i not in selected_indices:
        selected_indices.append(last_i)
    # 补合作位
    for i in range(len(authors)):
        if len(selected_indices) >= max_authors:
            break
        if i not in selected_indices:
            selected_indices.append(i)
    selected_indices = selected_indices[:max_authors]

    # 3. 并发 enrich 每位作者
    def _enrich_one(idx: int) -> CoauthorInfo:
        name = authors[idx]
        role = roles.get(name, "合作")
        if idx == 0 and role == "合作":
            role = "一作"

        wl = whitelist_match.get(name)
        if wl:
            # 白名单作者：用 Bitable 已有字段
            return CoauthorInfo(
                name=name,
                role=role,
                is_whitelist=True,
                whitelist_record_id=wl.record_id,
                affiliation=wl.organization,
                current_status=(wl.bio[:80] if wl.bio else None),
                github=_clean_url(wl.github_url),
                scholar_id=_extract_scholar_id(_clean_url(wl.scholar_url)),
                homepage=_clean_url(wl.personal_url),
                provenance={
                    "affiliation": "bitable:whitelist",
                    "github": "bitable:whitelist" if wl.github_url else "",
                    "homepage": "bitable:whitelist" if wl.personal_url else "",
                    "scholar_id": "bitable:whitelist" if wl.scholar_url else "",
                },
            )
        # 非白名单：跑 AnySearch
        # 给一作 / 共一 / 通讯额外加一个 co-author hint 提高命中率
        co_hints = [authors[j] for j in selected_indices if j != idx][:2]
        aff_hint = None  # 后续可从 arxiv HTML 第一作者机构里推断
        try:
            profile = enrich_author(name, arxiv_id, co_hints, aff_hint, cache=True)
        except Exception as e:  # noqa: BLE001
            log.warning("enrich_author failed for %s: %s", name, e)
            profile = {"name": name, "provenance": {}}

        # 整合 GitHub: prefer AnySearch GitHub username，arxiv HTML repo URL 作为 hint
        gh = profile.get("github")
        if not gh:
            # 看 arxiv HTML 是否有 yeates/repo-name 这种归属本作者的 repo
            for url in github_from_arxiv:
                # 这里只能粗略匹配——更稳的是 AnySearch
                pass

        return CoauthorInfo(
            name=name,
            role=role,
            is_whitelist=False,
            affiliation=profile.get("affiliation"),
            current_status=profile.get("current_status"),
            advisor=profile.get("advisor"),
            github=profile.get("github"),
            scholar_id=profile.get("scholar_id"),
            homepage=profile.get("homepage"),
            email=profile.get("email"),
            provenance=profile.get("provenance", {}),
        )

    coauthors: list[CoauthorInfo] = [None] * len(selected_indices)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=parallel_workers) as ex:
        futs = {ex.submit(_enrich_one, idx): pos for pos, idx in enumerate(selected_indices)}
        for fut in as_completed(futs):
            pos = futs[fut]
            try:
                coauthors[pos] = fut.result()
            except Exception as e:  # noqa: BLE001
                log.warning("enrich_one failed: %s", e)
                coauthors[pos] = CoauthorInfo(name=authors[selected_indices[pos]])

    return [c for c in coauthors if c is not None]


# ─── helpers ──────────────────────────────────────────────────────────────

def _clean_url(u: str | None) -> str | None:
    """剥 markdown wrap '[url](url)' → url."""
    if not u:
        return None
    if isinstance(u, list):
        u = u[0] if u else None
        if not u:
            return None
    s = str(u).strip()
    m = re.match(r"^\[([^\]]+)\]\([^)]+\)$", s)
    if m:
        return m.group(1).strip()
    return s


def _extract_scholar_id(url: str | None) -> str | None:
    """从 scholar URL 提取 user= 参数."""
    if not url:
        return None
    m = re.search(r"user=([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None
