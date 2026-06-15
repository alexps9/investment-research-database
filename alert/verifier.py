"""Cross-verification: search for primary sources to validate Chinese media alerts.

Uses a lightweight LLM call to judge whether search results actually match
the alert event (not just the entity name).
"""

import json
import os
import re
import time
from datetime import datetime

import requests

BEDROCK_API_KEY = os.environ.get("BEDROCK_API_KEY", "")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
BEDROCK_MODEL_FAST = os.environ.get("BEDROCK_MODEL_FAST", "us.anthropic.claude-sonnet-4-6")

_PRIMARY_DOMAINS = [
    "about.fb.com", "blog.google", "openai.com", "anthropic.com",
    "nvidia.com", "microsoft.com", "apple.com", "amazon.com",
    "reuters.com", "bloomberg.com", "theinformation.com", "wsj.com",
    "ft.com", "techcrunch.com", "theverge.com", "arstechnica.com",
    "cnbc.com", "nytimes.com", "semafor.com", "wired.com",
    "ec.europa.eu", "gov.uk", "whitehouse.gov",
]

_CITED_SOURCE_MAP = {
    "路透社": "reuters.com",
    "路透": "reuters.com",
    "Reuters": "reuters.com",
    "彭博": "bloomberg.com",
    "彭博社": "bloomberg.com",
    "Bloomberg": "bloomberg.com",
    "华尔街日报": "wsj.com",
    "WSJ": "wsj.com",
    "金融时报": "ft.com",
    "FT": "ft.com",
    "The Information": "theinformation.com",
    "CNBC": "cnbc.com",
    "纽约时报": "nytimes.com",
    "TechCrunch": "techcrunch.com",
    "The Verge": "theverge.com",
}


_session = requests.Session()
_session.trust_env = False


def _ddg_search(query: str, max_results: int = 8) -> list:
    """DuckDuckGo HTML search (free, no API key)."""
    try:
        resp = _session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=10,
        )
        results = []
        for m in re.finditer(
            r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>',
            resp.text,
        ):
            link = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2))
            results.append({"title": title, "url": link})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


def _is_primary_source(url: str) -> bool:
    if not any(d in url for d in _PRIMARY_DOMAINS):
        return False
    path = re.sub(r"https?://[^/]+", "", url).rstrip("/")
    if not path or path in ("/", "/en-us", "/en"):
        return False
    return True


def _extract_cited_source(summary: str) -> str | None:
    """从 summary 中提取'据XX报道'的引述来源域名。"""
    pattern = r"据([^报]{1,20}?)报道|according to ([A-Za-z\s]+)"
    m = re.search(pattern, summary)
    if not m:
        return None
    cited = (m.group(1) or m.group(2) or "").strip()
    return _CITED_SOURCE_MAP.get(cited)


def _extract_date_from_url(url: str) -> str | None:
    """尝试从 URL 路径中提取日期。"""
    m = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"/(\d{4})(\d{2})(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _date_within_one_day(url_date_str: str, alert_date: str | None) -> bool:
    if not alert_date:
        return True
    try:
        url_dt = datetime.strptime(url_date_str, "%Y-%m-%d")
        alert_dt = datetime.strptime(alert_date[:10], "%Y-%m-%d")
        return abs((url_dt - alert_dt).days) <= 1
    except (ValueError, TypeError):
        return True


def _build_query(summary: str) -> str:
    """从中文 summary 提取英文关键词构建搜索 query。"""
    entities = re.findall(r"[A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)*", summary)
    numbers = re.findall(r"\d+[\.\d]*\s*(?:亿美元|万亿|亿|GW|MW|billion|million|%)", summary)
    key_cn = re.findall(r"(?:融资|收购|合作|数据中心|芯片|租赁|投资|发布|开放|量子|拨款|拒绝|IPO|上市|调查|离职|涨价)", summary)
    cn_to_en = {
        "融资": "funding", "收购": "acquisition", "合作": "partnership",
        "数据中心": "data center", "芯片": "chip", "租赁": "lease",
        "投资": "invest", "发布": "launch", "开放": "open",
        "量子": "quantum", "拨款": "funding", "拒绝": "reject",
        "IPO": "IPO", "上市": "IPO", "调查": "investigation",
        "离职": "resign", "涨价": "price increase",
    }
    parts = entities[:4]
    for cn in key_cn[:2]:
        parts.append(cn_to_en.get(cn, cn))
    for n in numbers[:2]:
        num_str = re.sub(r"[美元人民币\s]", "", n).strip()
        if "万亿" in num_str:
            digits = re.sub(r"[万亿]", "", num_str)
            parts.append(f"{digits} trillion")
        elif "亿" in num_str:
            digits = re.sub(r"[亿]", "", num_str)
            try:
                parts.append(f"{float(digits)/10:.1f} billion".replace(".0 ", " "))
            except ValueError:
                parts.append(digits)
        else:
            clean = re.sub(r"[亿万]", "", num_str).strip()
            if clean:
                parts.append(clean)
    if not parts:
        return ""
    return " ".join(parts)


def _llm_pick_source(summary: str, candidates: list[dict], alert_date: str | None) -> dict | None:
    """Use LLM to pick the best matching primary source from search candidates.

    Returns the best candidate dict or None if no match.
    """
    if not BEDROCK_API_KEY or not candidates:
        return None

    candidates_text = "\n".join(
        f"{i+1}. [{c['title']}] {c['url']}"
        for i, c in enumerate(candidates)
    )

    system_prompt = """你是一个新闻原始来源验证助手。给你一条新闻摘要和若干搜索结果，判断哪条搜索结果是这条新闻的真正原始报道来源。

规则：
- 必须是报道同一件具体事件的文章（同一公司+同一动作+同一时间）
- 仅公司名匹配但事件不同的，不算（如：都是OpenAI但一个是收购一个是产品发布）
- 首页、产品页、无关旧文不算
- 如果没有任何一条匹配，返回 {"pick": 0}
- 如果有匹配，返回 {"pick": N}（N是编号）"""

    user_msg = f"""新闻摘要：{summary}
Alert日期：{alert_date or '未知'}

搜索结果：
{candidates_text}

哪条是这条新闻的原始来源？返回JSON。"""

    base_url = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com"
    url = f"{base_url}/model/{BEDROCK_MODEL_FAST}/converse"

    payload = {
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_msg}]}],
        "inferenceConfig": {"maxTokens": 64},
    }

    try:
        resp = _session.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {BEDROCK_API_KEY}",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return None

        content = resp.json()["output"]["message"]["content"][0]["text"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        pick = result.get("pick", 0)
        if pick and 1 <= pick <= len(candidates):
            return candidates[pick - 1]
    except Exception:
        pass
    return None


def cross_verify(summary: str, alert_date: str | None = None) -> dict | None:
    """Search for primary/authoritative sources that reported this event.

    Uses DDG search + LLM judgment to find the correct original source.
    Returns {"url": str, "title": str, "domain": str} or None.
    """
    query = _build_query(summary)
    if not query or len(query.split()) < 3:
        return None

    cited_domain = _extract_cited_source(summary)
    results = _ddg_search(query)

    # Filter to primary-source domains only
    candidates = []
    for r in results:
        if not _is_primary_source(r["url"]):
            continue
        # Date pre-filter: reject if URL date is clearly wrong
        url_date = _extract_date_from_url(r["url"])
        if url_date and not _date_within_one_day(url_date, alert_date):
            continue
        # If a specific source is cited, only consider that domain
        if cited_domain and cited_domain not in r["url"]:
            continue
        candidates.append(r)

    if not candidates:
        return None

    # LLM picks the correct one (or none)
    picked = _llm_pick_source(summary, candidates, alert_date)
    if not picked:
        return None

    domain = re.search(r"https?://(?:www\.)?([^/]+)", picked["url"])
    return {
        "url": picked["url"],
        "title": picked["title"],
        "domain": domain.group(1) if domain else "",
    }
