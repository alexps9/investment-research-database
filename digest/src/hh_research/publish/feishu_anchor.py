"""Feishu docx anchor_id generator — wraps the internal web API
`POST my.feishu.cn/space/api/docx/partial_content_anchor/create`.

This is NOT part of feishu's open OpenAPI (open.feishu.cn). It is the
endpoint the web UI uses for "复制选区链接". The only way to programmatically
generate a working `#share-<token>` URL fragment for a docx block.

Auth: requires user's browser session Cookie + X-CSRFToken (set in .env as
HH_FEISHU_WEB_COOKIE / HH_FEISHU_CSRF_TOKEN). Cookies typically last 1-7
days; on 401/403 the user must refresh from Network panel.

Usage:
    from hh_research.publish.feishu_anchor import create_anchor
    anchor_id = create_anchor(
        page_id="<docx obj_token>",
        block_id="<doxcn...>",
        structure_version=<doc revision>,
    )
    url = f"https://my.feishu.cn/wiki/<node>#share-{anchor_id}"
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from ..utils.logger import get_logger

log = get_logger("feishu_anchor")

ENDPOINT = "https://my.feishu.cn/space/api/docx/partial_content_anchor/create"

# Browser-like headers (Safari to match user's session)
_BASE_HEADERS = {
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://my.feishu.cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3 Safari/605.1.15",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
}


class FeishuAnchorError(RuntimeError):
    """Raised when partial_content_anchor/create fails (auth expired, invalid params, etc.)."""


def create_anchor(
    page_id: str,
    block_id: str,
    structure_version: int,
    src_end_idx: int = 1,
    wiki_node_token: str | None = None,
    timeout: float = 15.0,
) -> str:
    """Create a share anchor for one block and return its anchor_id.

    Args:
        page_id: docx obj_token
        block_id: target block id (e.g. doxcn...)
        structure_version: current revision_id of the doc (get from
            `GET /open-apis/docx/v1/documents/<id>`)
        src_end_idx: 选区结束 index. 1 is the minimum valid value and works for
            any block regardless of text length. **Must be <= block text length**;
            larger values return code=4000002 invalid param.
        wiki_node_token: optional; if provided, used as Referer for cleaner
            audit trail (飞书后端可能根据 referer 上下文有差异行为).
        timeout: HTTP timeout seconds

    Returns:
        anchor_id (27-char token, e.g. "Lo4mdiojXo29JRx2WrLcopknnCf")

    Raises:
        FeishuAnchorError: cookie expired / invalid params / network failure
    """
    cookie = os.getenv("HH_FEISHU_WEB_COOKIE")
    csrf = os.getenv("HH_FEISHU_CSRF_TOKEN")
    if not cookie or not csrf:
        raise FeishuAnchorError(
            "HH_FEISHU_WEB_COOKIE / HH_FEISHU_CSRF_TOKEN not set in .env. "
            "登录飞书 web → F12 Network 面板 → 找任意 my.feishu.cn 请求 → "
            "复制 Cookie header 完整串和 X-CSRFToken 值。"
        )

    referer = (
        f"https://my.feishu.cn/wiki/{wiki_node_token}"
        if wiki_node_token else f"https://my.feishu.cn/docx/{page_id}"
    )

    payload = {
        "page_id": page_id,
        "structure_version": structure_version,
        "selected_blocks": [{
            "block_id": block_id,
            "src_version": 1,
            "selected_text": {"src_start_idx": 0, "src_end_idx": src_end_idx},
        }],
        "subtype": "textCard",
    }

    headers = {
        **_BASE_HEADERS,
        "Cookie": cookie,
        "X-CSRFToken": csrf,
        "Referer": referer,
    }

    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.post(ENDPOINT, json=payload, headers=headers)
    except httpx.HTTPError as e:
        raise FeishuAnchorError(f"HTTP error: {e}") from e

    if r.status_code in (401, 403):
        raise FeishuAnchorError(
            f"鉴权失败 (HTTP {r.status_code})——Cookie 过期了。需重新从浏览器抓 Cookie 更新 .env"
        )

    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise FeishuAnchorError(f"non-JSON response (HTTP {r.status_code}): {r.text[:200]}") from e

    code = data.get("code")
    if code != 0:
        msg = data.get("msg", "?")
        raise FeishuAnchorError(
            f"API returned code={code} msg={msg}; payload={payload}"
        )

    anchor_id = data.get("data", {}).get("anchor_id")
    if not anchor_id:
        raise FeishuAnchorError(f"missing anchor_id in response: {data}")

    return anchor_id


def get_doc_revision(obj_token: str) -> int:
    """Helper: 拿当前文档 revision_id (用作 structure_version)."""
    import json
    import subprocess
    r = subprocess.run(
        ["lark-cli", "--profile", "personal", "api", "GET",
         f"/open-apis/docx/v1/documents/{obj_token}"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if r.returncode != 0:
        raise FeishuAnchorError(f"docx info fetch failed: {r.stderr[:200]}")
    out = r.stdout
    info = json.loads(out[out.find('{'):])
    rev = info.get("data", {}).get("document", {}).get("revision_id")
    if rev is None:
        raise FeishuAnchorError(f"no revision_id in doc info: {info}")
    return int(rev)


def build_share_url(node_token: str, anchor_id: str) -> str:
    """构造飞书 wiki 跳转 URL."""
    return f"https://my.feishu.cn/wiki/{node_token}#share-{anchor_id}"
