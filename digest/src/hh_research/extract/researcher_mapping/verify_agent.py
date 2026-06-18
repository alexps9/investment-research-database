"""LLM 审查 agent：抓 URL → 提取 → match.py 判定。"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import httpx

from hh_research.utils.logger import get_logger

log = get_logger("verify_agent")

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126.0"}
URL_TIMEOUT_S = 8.0
HTML_CAP_BYTES = 200_000


def fetch_url_text(url: str) -> str | None:
    """同步抓 URL HTML，cap 200KB。失败 / 4xx/5xx 返回 None。"""
    if not url:
        return None
    try:
        with httpx.Client(headers=UA, timeout=URL_TIMEOUT_S, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            text = r.text
            if len(text) > HTML_CAP_BYTES:
                text = text[:HTML_CAP_BYTES]
            return text
    except Exception as e:  # noqa: BLE001
        log.info("fetch_url_text(%s): %s", url, e)
        return None


def fetch_all_urls(url_map: dict[str, str]) -> dict[str, str]:
    """{kind: url} → {kind: html_text}，并发抓取，失败的 kind 不出现。"""
    if not url_map:
        return {}
    out: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(len(url_map), 4)) as ex:
        futs = {ex.submit(fetch_url_text, url): kind for kind, url in url_map.items() if url}
        for fut in as_completed(futs):
            kind = futs[fut]
            try:
                html = fut.result()
                if html:
                    out[kind] = html
            except Exception as e:  # noqa: BLE001
                log.info("fetch failed for %s: %s", kind, e)
    return out


import re

from hh_research.extract.claude_client import make_client, resolve_model_id


_EXTRACT_SYSTEM = """你是数据提取助手。从下方 HTML 页面只提取以下事实，绝不推断：
- page_name: 页面 owner 的姓名（从 <title>/<h1>/profile section 提取）
- page_affiliations: 页面声明的机构列表（按出现顺序，最多 5 个）
- page_role: 例如 "PhD student" / "Assistant Professor"（看不出填 null）

输出严格 JSON。若信息不存在用 null，绝不编造。
输出格式: {"page_name": "...", "page_affiliations": ["..."], "page_role": "..."}"""


def _call_claude(model: str, system: str, user: str):
    """调用 Bedrock Claude，返回 (response, model_used)。"""
    client = make_client()
    bedrock_id = resolve_model_id(model)
    resp = client.messages.create(
        model=bedrock_id,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp, model


def _parse_extract_response(resp) -> dict[str, Any]:
    """解析 LLM JSON，失败返回空 schema。"""
    empty: dict[str, Any] = {"page_name": None, "page_affiliations": [], "page_role": None}
    if not resp or not resp.content:
        return empty
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    # 剥可能的 ```json ... ``` 栅栏
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return empty
    return {
        "page_name": data.get("page_name") or None,
        "page_affiliations": data.get("page_affiliations") or [],
        "page_role": data.get("page_role") or None,
    }


def _has_chinese_text(s: str) -> bool:
    return any("一" <= c <= "鿿" for c in (s or ""))


def should_upgrade_to_sonnet(
    haiku_out: dict[str, Any],
    html_has_chinese: bool,
    candidate_has_chinese: bool,
) -> bool:
    """升级到 Sonnet 4.6 的判定（spec §6.4）"""
    if haiku_out.get("page_name") is None or not haiku_out.get("page_affiliations"):
        return True
    if candidate_has_chinese:
        return True
    if html_has_chinese:
        page_name = haiku_out.get("page_name") or ""
        if page_name and all(ord(c) < 128 for c in page_name):
            return True
    return False


def extract_page_facts(
    url: str,
    html: str,
    candidate_name: str = "",
) -> tuple[dict[str, Any], str]:
    """从一页 HTML 提取 {page_name, page_affiliations, page_role}.

    Returns: (facts_dict, model_used)
    """
    user_msg = f"[URL]: {url}\n[HTML CONTENT]:\n{html}"

    # 注: Bedrock 上 claude-haiku-4-5 不可用（claude_client 注释明示）。
    # 主跑 Sonnet 4.6；不确定时升级 Opus 4.6。
    resp, _ = _call_claude("claude-sonnet-4-6", _EXTRACT_SYSTEM, user_msg)
    sonnet_out = _parse_extract_response(resp)

    if should_upgrade_to_sonnet(
        sonnet_out,
        html_has_chinese=_has_chinese_text(html),
        candidate_has_chinese=_has_chinese_text(candidate_name),
    ):
        try:
            resp2, _ = _call_claude("claude-opus-4-6", _EXTRACT_SYSTEM, user_msg)
            opus_out = _parse_extract_response(resp2)
            return opus_out, "claude-opus-4-6"
        except Exception as e:  # noqa: BLE001
            log.warning("opus upgrade failed (%s), falling back to sonnet output: %s", url, e)
            return sonnet_out, "claude-sonnet-4-6"

    return sonnet_out, "claude-sonnet-4-6"


from hh_research.extract.researcher_mapping.match import match_name, match_affiliation
from hh_research.storage.schemas import CoauthorInfo


def verify_coauthor(candidate: CoauthorInfo) -> "CoauthorInfo | None":
    """主入口：拉 URL → LLM 提取 → match.py 判定 → 不匹配字段填 None。

    返回 None 表示整位作者剔除（spec §6.5：name 验证全失败）。
    """
    url_map: dict[str, str] = {}
    if candidate.github:
        gh = candidate.github
        if not gh.startswith("http"):
            gh = f"https://github.com/{gh}"
        url_map["github"] = gh
    if candidate.homepage:
        url_map["homepage"] = candidate.homepage
    if candidate.scholar_id:
        url_map["scholar"] = f"https://scholar.google.com/citations?user={candidate.scholar_id}"

    if not url_map:
        # 没有任何 URL 可验证 → 保留 candidate 字段，verification 标 skipped
        verification: dict[str, str] = {}
        for f in ["affiliation", "github", "homepage", "scholar"]:
            attr = "scholar_id" if f == "scholar" else f
            if getattr(candidate, attr, None) is not None or f == "affiliation":
                verification[f] = "skipped:no_url"
        new_data = candidate.model_dump()
        new_data["verification"] = verification
        return CoauthorInfo(**new_data)

    htmls = fetch_all_urls(url_map)
    if not htmls:
        # 所有 URL fetch 失败 → 字段全部丢弃（最保守）
        new_data = candidate.model_dump()
        for field in ["affiliation", "github", "homepage", "scholar_id", "current_status"]:
            new_data[field] = None
        new_data["verification"] = {f: "rejected:fetch_failed"
                                    for f in ["affiliation", "github", "homepage", "scholar"]}
        return CoauthorInfo(**new_data)

    # 对每个抓到的 URL 跑 LLM 提取
    page_results: dict[str, dict] = {}
    for kind, html in htmls.items():
        facts, _model = extract_page_facts(
            url=url_map[kind],
            html=html,
            candidate_name=candidate.name,
        )
        page_results[kind] = facts

    verification = {}

    # 1. name 验证：任一 URL 的 page_name 跟候选 name 匹配
    name_matched_any = False
    for kind, facts in page_results.items():
        if facts.get("page_name") and match_name(candidate.name, facts["page_name"]):
            name_matched_any = True
            break
    if not name_matched_any:
        log.info("rm_v4 verify: REJECT whole author '%s' (no URL page_name matches)",
                 candidate.name)
        return None
    verification["name"] = "verified"

    # 2. 逐 URL 字段：github / homepage / scholar
    fields_to_verify = {
        "github": "github",
        "homepage": "homepage",
        "scholar": "scholar_id",
    }
    new_data = candidate.model_dump()
    for url_kind, attr_name in fields_to_verify.items():
        candidate_val = getattr(candidate, attr_name, None)
        if not candidate_val:
            continue
        if url_kind not in page_results:
            new_data[attr_name] = None
            verification[url_kind] = "rejected:fetch_failed"
            continue
        page_name = page_results[url_kind].get("page_name")
        if page_name and match_name(candidate.name, page_name):
            verification[url_kind] = "verified"
        else:
            new_data[attr_name] = None
            verification[url_kind] = "rejected:name_mismatch"

    # 3. affiliation 字段：跨所有 URL 的 page_affiliations 找匹配
    if candidate.affiliation:
        all_page_affs: list[str] = []
        for facts in page_results.values():
            all_page_affs.extend(facts.get("page_affiliations") or [])
        if match_affiliation(candidate.affiliation, all_page_affs):
            verification["affiliation"] = "verified"
        else:
            new_data["affiliation"] = None
            new_data["current_status"] = None
            verification["affiliation"] = "rejected:no_match"

    # 4. email 不验证（无 URL），advisor 不验证（无渠道）
    if candidate.email:
        verification["email"] = "skipped:no_url"

    new_data["verification"] = verification
    return CoauthorInfo(**new_data)
