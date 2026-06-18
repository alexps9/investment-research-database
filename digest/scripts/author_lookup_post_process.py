"""Author Lookup Post-Process: 自动填充 Researcher Mapping 占位表

输入: 已发布日报的 obj_token
流程:
  1. 用 docs +fetch --detail with-ids 获取所有 block_id
  2. 解析每个 <table> block，找到对应的 arxiv URL（往前找 <a href="arxiv.org/...">）
  3. arxiv API 拿作者列表
  4. 每位作者：
     - 在 whitelist Bitable 查 'name' 字段（first_token+last_token 匹配）
     - 若命中：取 whitelist 的 github_url / scholar_url / personal_url / 简介
     - 若未命中：填名字 + "—" 表示未查
  5. 生成新 table XML
  6. docs +update --command block_replace --block-id <id> --content <new_xml>

CLI:
  .venv/bin/python scripts/author_lookup_post_process.py <obj_token>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.publish.lark_doc_publisher import _lark_cli, PublishError  # noqa: E402
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("author_lookup_post_process")

PLACEHOLDER_PATTERN = re.compile(r"占位\s*[—-]+\s*待\s*author\s*lookup", re.IGNORECASE)
# RM 表的表头特征：含「姓名」+「现状」+「GitHub」+「邮箱」字段
RM_HEADER_PATTERN = re.compile(r"姓名.*?现状.*?GitHub.*?邮箱", re.IGNORECASE | re.DOTALL)
ARXIV_URL_RE = re.compile(r"https?://arxiv\.org/abs/([0-9]+\.[0-9]+(?:v\d+)?)")


def _build_whitelist_index() -> dict[str, dict[str, Any]]:
    """从 Bitable whitelist 表建立 "first_token last_token" → record 的索引"""
    log.info("building whitelist name index from Bitable ...")
    index: dict[str, dict[str, Any]] = {}
    offset = 0
    fields_order: list[str] = []
    while True:
        cmd = [
            "lark-cli", "base", "+record-list",
            "--as", "user", "--profile", "personal",
            "--base-token", "UdwrbpCMoasCs3snCvbcKgbsnfc",
            "--table-id", "tblpVgQBAkPptnip",
            "--limit", "200", "--offset", str(offset),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log.warning("whitelist read rc=%d", r.returncode)
            break
        out = r.stdout
        if '"data":' not in out:
            break
        start = out.find('{')
        try:
            resp = json.loads(out[start:])
        except json.JSONDecodeError as e:
            log.warning("whitelist parse: %s", e)
            break
        data = resp.get("data", {})
        if not fields_order:
            fields_order = data.get("fields", [])
        records = data.get("data", [])
        if not records:
            break
        for r_arr in records:
            row = dict(zip(fields_order, r_arr))
            name = row.get("名字") or ""
            if not name or not isinstance(name, str):
                continue
            cleaned = re.sub(r"[一-鿿㐀-䶿()()\[\]【】]+", " ", name)
            tokens = [t for t in cleaned.split() if len(t) >= 2]
            if len(tokens) < 2:
                continue
            key = (tokens[0] + " " + tokens[-1]).lower()
            index[key] = row
        if not data.get("has_more"):
            break
        offset += 200
    log.info("  whitelist index size: %d", len(index))
    return index


def _clean_url(u: Any) -> str:
    """剥离 markdown 链接外层 [url](url) 包装"""
    if u is None:
        return ""
    if isinstance(u, list):
        u = u[0] if u else ""
    if not isinstance(u, str):
        u = str(u)
    # Strip markdown wrap
    m = re.match(r"^\[([^\]]+)\]\([^)]+\)$", u.strip())
    if m:
        u = m.group(1)
    return u.strip()


def _fetch_doc_blocks(obj_token: str) -> tuple[str, list[dict[str, Any]]]:
    """获取 doc XML（with-ids）并解析顶层 blocks"""
    resp = _lark_cli(
        "docs", "+fetch",
        "--api-version", "v2",
        "--doc", obj_token,
        "--scope", "full",
        "--detail", "with-ids",
        timeout=120,
    )
    if not resp.get("ok"):
        raise PublishError(f"fetch failed: {resp.get('error')}")
    content = (resp.get("data", {}).get("document", {}) or {}).get("content", "")
    # 解析每个含 id 的顶层 block
    block_pattern = re.compile(
        r'<(?P<tag>p|h[1-9]|li|callout|table|ul)\b[^>]*?\bid="(?P<bid>[^"]+)"[^>]*>(?P<inner>.*?)</(?P=tag)>',
        re.DOTALL,
    )
    blocks = []
    for m in block_pattern.finditer(content):
        inner = m.group("inner")
        text = re.sub(r"<[^>]+>", "", inner)
        blocks.append({
            "block_id": m.group("bid"),
            "block_type": m.group("tag"),
            "text": text,
            "raw": m.group(0),
        })
    return content, blocks


def _fetch_arxiv_authors(arxiv_id: str) -> list[str]:
    """用 arxiv API 拿作者列表（仅名字）"""
    import urllib.request
    import xml.etree.ElementTree as ET
    base_id = re.sub(r"v\d+$", "", arxiv_id)
    url = f"http://export.arxiv.org/api/query?id_list={base_id}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            xml_text = resp.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("arxiv API fetch %s: %s", arxiv_id, e)
        return []
    # Parse Atom XML
    try:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_text)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return []
        names = []
        for author in entry.findall("atom:author", ns):
            name_el = author.find("atom:name", ns)
            if name_el is not None and name_el.text:
                names.append(name_el.text.strip())
        return names
    except Exception as e:  # noqa: BLE001
        log.warning("arxiv API parse %s: %s", arxiv_id, e)
        return []


def _author_arxiv_search_url(name: str) -> str:
    """构造 arxiv 作者搜索 URL（兜底，让用户能一键查作者过往论文）"""
    import urllib.parse
    return f"https://arxiv.org/search/?searchtype=author&query={urllib.parse.quote(name)}"


def _select_authors_for_rm(authors: list[str], whitelist_index: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    """选取上 RM 表的作者（最多 6 位）：强制 ①一作 ②所有 whitelist 命中（不管位置）
    ③末位通讯（即使非白名单）④补合作位

    返回 [(name, role), ...]，role ∈ {一作, 通讯, 合作}
    """
    if not authors:
        return []
    selected: list[tuple[str, str]] = []
    seen_idx: set[int] = set()

    # ① 一作
    selected.append((authors[0], "一作"))
    seen_idx.add(0)

    # ② 所有 whitelist 命中
    for i, name in enumerate(authors):
        if i in seen_idx:
            continue
        tokens = name.split()
        if len(tokens) >= 2:
            key = (tokens[0] + " " + tokens[-1]).lower()
            if key in whitelist_index:
                role = "通讯" if i == len(authors) - 1 else "合作"
                selected.append((name, role))
                seen_idx.add(i)

    # ③ 末位（如果没被②选中）— 末位往往是 senior，即使非白名单也保留
    last_i = len(authors) - 1
    if last_i not in seen_idx and last_i > 0:
        selected.append((authors[last_i], "通讯"))
        seen_idx.add(last_i)

    # ④ 补到 6 位
    for i, name in enumerate(authors):
        if len(selected) >= 6:
            break
        if i in seen_idx:
            continue
        selected.append((name, "合作"))
        seen_idx.add(i)

    return selected[:6]


def _build_rm_table(authors: list[str], whitelist_index: dict[str, dict[str, Any]]) -> str:
    """构造新的 Researcher Mapping 表格 XML — v2：强制保留白名单 + 末位 senior"""
    rows = []
    for name, role in _select_authors_for_rm(authors, whitelist_index):
        # 在 whitelist 找
        tokens = name.split()
        if len(tokens) >= 2:
            key = (tokens[0] + " " + tokens[-1]).lower()
            wl = whitelist_index.get(key, {})
        else:
            wl = {}
        if wl:
            # whitelist matched
            org_field = wl.get("组织") or wl.get("机构")
            if isinstance(org_field, list):
                org = ", ".join(str(x) for x in org_field)
            else:
                org = str(org_field or "")
            scope_field = wl.get("业界/学界/其他")
            if isinstance(scope_field, list):
                scope = scope_field[0] if scope_field else ""
            else:
                scope = str(scope_field or "")
            bio_field = wl.get("简介") or wl.get("bio") or ""
            bio = str(bio_field or "")[:50]
            # 现状：org+scope，加 bio 摘要
            if org and scope:
                status = f"{org}（{scope}）"
            elif scope:
                status = scope
            elif org:
                status = org
            else:
                status = "—"
            if bio:
                status = f"{status} · {bio}"

            github = _clean_url(wl.get("github_url"))
            personal = _clean_url(wl.get("personal_url"))
            scholar = _clean_url(wl.get("scholar_url"))
            arxiv_home = _clean_url(wl.get("arxiv_homepage_url"))
            # 邮箱 fallback 链: personal → scholar → arxiv_homepage → arxiv search
            email_url = personal or scholar or arxiv_home or _author_arxiv_search_url(name)
            email_label = "主页" if (personal or scholar) else ("arxiv 主页" if arxiv_home else "arxiv 搜索")
            github_disp = (
                f'<a href="{github}">{github.replace("https://github.com/", "@")}</a>'
                if github else "—"
            )
            email_disp = f'<a href="{email_url}">{email_label}</a>'
            name_html = f"<b>{name}</b>（{role}·白名单）"
        else:
            # 非白名单：至少给 arxiv search 链接作兜底
            status = "—"
            github_disp = "—"
            email_disp = f'<a href="{_author_arxiv_search_url(name)}">arxiv 搜索</a>'
            name_html = f"{name}（{role}）"

        rows.append(
            f'<tr><td vertical-align="top"><p>{name_html}</p></td>'
            f'<td vertical-align="top"><p>{status}</p></td>'
            f'<td vertical-align="top"><p>{github_disp}</p></td>'
            f'<td vertical-align="top"><p>{email_disp}</p></td></tr>'
        )

    if not rows:
        return ""

    return (
        '<table>'
        '<colgroup><col width="180"/><col/><col width="130"/><col width="180"/></colgroup>'
        '<thead><tr>'
        '<th background-color="light-gray"><p><b>姓名（角色）</b></p></th>'
        '<th background-color="light-gray"><p><b>现状</b></p></th>'
        '<th background-color="light-gray"><p><b>GitHub</b></p></th>'
        '<th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table>'
    )


def run(obj_token: str, rebuild: bool = False) -> dict:
    """rebuild=False: 只填占位的 RM 表（首次填充）
       rebuild=True: 识别所有 RM 表（按表头匹配），全部重新生成"""
    log.info("=== author lookup post-process: %s (rebuild=%s) ===", obj_token, rebuild)
    content, blocks = _fetch_doc_blocks(obj_token)
    log.info("  %d top-level blocks fetched", len(blocks))

    wl_index = _build_whitelist_index()

    # 找 RM 表 + 往前找 arxiv URL
    rm_tables = []
    last_arxiv_url = None
    for b in blocks:
        m_url = ARXIV_URL_RE.search(b["raw"])
        if m_url:
            last_arxiv_url = m_url.group(0)
        if b["block_type"] != "table":
            continue
        matches = False
        if rebuild and RM_HEADER_PATTERN.search(b["text"]):
            matches = True
        elif (not rebuild) and PLACEHOLDER_PATTERN.search(b["text"]):
            matches = True
        if matches:
            rm_tables.append({"block_id": b["block_id"], "arxiv_url": last_arxiv_url})

    mode_label = "RM 表（rebuild 模式）" if rebuild else "占位 RM 表"
    log.info("  %s: %d (与 arxiv URL 匹配 %d)",
             mode_label, len(rm_tables), sum(1 for t in rm_tables if t["arxiv_url"]))

    results = {"total": len(rm_tables), "filled": 0, "skipped": 0, "errors": []}
    for t in rm_tables:
        url = t["arxiv_url"]
        if not url:
            log.info("  skip table %s (no arxiv URL)", t["block_id"][:16])
            results["skipped"] += 1
            continue
        arxiv_id = ARXIV_URL_RE.search(url).group(1)
        authors = _fetch_arxiv_authors(arxiv_id)
        if not authors:
            log.info("  skip %s (no authors)", arxiv_id)
            results["skipped"] += 1
            continue
        new_table = _build_rm_table(authors, wl_index)
        if not new_table:
            results["skipped"] += 1
            continue
        try:
            resp = _lark_cli(
                "docs", "+update",
                "--api-version", "v2",
                "--doc", obj_token,
                "--command", "block_replace",
                "--block-id", t["block_id"],
                "--content", new_table,
                timeout=60,
            )
            if resp.get("ok"):
                results["filled"] += 1
                log.info("  filled %s for %s (%d authors)", t["block_id"][:16], arxiv_id, len(authors))
            else:
                results["errors"].append((t["block_id"], str(resp.get("error"))))
        except Exception as e:  # noqa: BLE001
            results["errors"].append((t["block_id"], str(e)))
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("obj_token", help="飞书 docx obj_token")
    ap.add_argument("--rebuild", action="store_true",
                    help="重建模式：识别所有 RM 表（按表头）并全部重新生成，用于改进算法后重跑")
    args = ap.parse_args()
    result = run(args.obj_token, rebuild=args.rebuild)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
