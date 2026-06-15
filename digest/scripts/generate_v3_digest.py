"""基于 V4 batch enrich 数据，生成 v3 日报（v2 + V4 RM 表）。

输入：
  - data/digests/digest_2026-05-21.md（v2，含 v2 RM 表的 XML）
  - data/state/rm_v4_batch/2026-05-21.json（V4 batch 结果）

输出：
  - data/digests/digest_2026-05-21_v3.md（同 v2 + RM 表替换）
  - data/digests/digest_2026-05-21_v3_compare.md（对比报告，含 v2 vs v3 RM 表 + 通过率）

Usage:
  .venv/bin/python scripts/generate_v3_digest.py
  .venv/bin/python scripts/generate_v3_digest.py --date 2026-05-21
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
V2_PATH_TEMPLATE = REPO_ROOT / "data/digests/digest_{date}.md"
V4_BATCH_TEMPLATE = REPO_ROOT / "data/state/rm_v4_batch/{date}.json"
V3_OUT_TEMPLATE = REPO_ROOT / "data/digests/digest_{date}_v3.md"
COMPARE_OUT_TEMPLATE = REPO_ROOT / "data/digests/digest_{date}_v3_compare.md"

# arxiv URL pattern
ARXIV_URL_RE = re.compile(r"https?://arxiv\.org/abs/([0-9]+\.[0-9]+)")

# 一个 RM 表的整体 pattern（含 <h5>Researcher Mapping</h5> 前的换行）
RM_BLOCK_RE = re.compile(
    r"<h5>Researcher Mapping</h5>\s*<table>.*?</table>",
    re.DOTALL,
)


def _gh_link(github: str | None, name: str) -> str:
    """构造 GitHub 单元格内容。"""
    if not github:
        return "—"
    # 兼容存的就是 username 或 https://github.com/...
    if github.startswith("http"):
        username = github.rstrip("/").rsplit("/", 1)[-1]
        url = github
    else:
        username = github
        url = f"https://github.com/{github}"
    return f'<a href="{url}">@{username}</a>'


def _home_link(homepage: str | None, scholar_id: str | None, email: str | None) -> str:
    """构造主页/Scholar/邮箱 单元格内容（按优先级）。"""
    if email:
        return email
    if homepage:
        return f'<a href="{homepage}">主页</a>'
    if scholar_id:
        return f'<a href="https://scholar.google.com/citations?user={scholar_id}">Scholar</a>'
    return "—"


def _role_with_whitelist(c: dict[str, Any]) -> str:
    role = c.get("role") or "合作"
    if c.get("is_whitelist"):
        return f"{role}·白名单"
    return role


def build_rm_table_xml(coauthors: list[dict[str, Any]]) -> str:
    """V4 数据 → RM 表 XML（match v2 格式：4 列）。"""
    if not coauthors:
        # 空 RM 表（V4 整位剔除导致无作者上表）
        rows = (
            '<tr><td vertical-align="top"><p>—</p></td>'
            '<td vertical-align="top"><p>占位 — V4 审查 agent 未保留任何作者数据</p></td>'
            '<td vertical-align="top"><p>—</p></td>'
            '<td vertical-align="top"><p>—</p></td></tr>'
        )
    else:
        row_list = []
        for c in coauthors:
            name = c.get("name") or ""
            role_label = _role_with_whitelist(c)
            # 白名单作者姓名加 <b>
            if c.get("is_whitelist"):
                name_html = f"<b>{name}</b>（{role_label}）"
            else:
                name_html = f"{name}（{role_label}）"
            # 现状
            aff = c.get("affiliation") or ""
            cur = c.get("current_status") or ""
            adv = c.get("advisor") or ""
            status_parts = []
            if aff:
                status_parts.append(aff)
            if cur and cur != aff:
                status_parts.append(cur)
            status = " · ".join(status_parts) if status_parts else "—"
            if adv:
                status += f"（导师 {adv}）"
            # github / 邮箱主页
            gh_cell = _gh_link(c.get("github"), name)
            home_cell = _home_link(c.get("homepage"), c.get("scholar_id"), c.get("email"))
            row_list.append(
                f'<tr><td vertical-align="top"><p>{name_html}</p></td>'
                f'<td vertical-align="top"><p>{status}</p></td>'
                f'<td vertical-align="top"><p>{gh_cell}</p></td>'
                f'<td vertical-align="top"><p>{home_cell}</p></td></tr>'
            )
        rows = "".join(row_list)
    return (
        '<table>\n'
        '  <colgroup><col width="180"/><col/><col width="130"/><col width="180"/></colgroup>\n'
        '  <thead>\n'
        '    <tr>\n'
        '      <th background-color="light-gray"><p><b>姓名（角色）</b></p></th>\n'
        '      <th background-color="light-gray"><p><b>现状</b></p></th>\n'
        '      <th background-color="light-gray"><p><b>GitHub</b></p></th>\n'
        '      <th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>\n'
        '    </tr>\n'
        '  </thead>\n'
        f'  <tbody>{rows}</tbody>\n'
        '</table>'
    )


def replace_rm_tables(v2_content: str, arxiv_to_coauthors: dict[str, list[dict]]) -> tuple[str, list[dict]]:
    """扫 v2 content，把每个 arxiv 论文对应的 RM 表替换。

    返回:
      - 新 content
      - 替换报告 list: [{arxiv_id, n_v4_authors, status: replaced/no_data/no_rm_table}, ...]
    """
    # 把内容按"段落"切：找每个 arxiv URL → 在它之后的下一个 RM 表 → 替换
    report: list[dict] = []
    seen_arxiv: set[str] = set()
    new_content = v2_content
    # 多次遍历：每次找下一个未处理的 arxiv，找之后的 RM 表
    while True:
        # 找下一个未处理的 arxiv URL
        next_match = None
        for m in ARXIV_URL_RE.finditer(new_content):
            arxiv_id = m.group(1)
            key = f"{arxiv_id}@{m.start()}"
            if key in seen_arxiv:
                continue
            next_match = (m, arxiv_id, key)
            break
        if not next_match:
            break
        m, arxiv_id, key = next_match
        seen_arxiv.add(key)

        # 在 arxiv URL 之后找下一个 RM 表
        rm_match = RM_BLOCK_RE.search(new_content, pos=m.end())
        if not rm_match:
            report.append({"arxiv_id": arxiv_id, "status": "no_rm_table"})
            continue

        # 检查：这个 RM 表是不是属于这个 arxiv？
        # 看 arxiv URL 和 RM 表之间是否还有另一个 arxiv URL
        between = new_content[m.end():rm_match.start()]
        if ARXIV_URL_RE.search(between):
            report.append({"arxiv_id": arxiv_id, "status": "no_rm_table"})
            continue

        # 拿 V4 数据
        v4_coauthors = arxiv_to_coauthors.get(arxiv_id)
        if v4_coauthors is None:
            report.append({
                "arxiv_id": arxiv_id,
                "status": "no_v4_data",
                "rm_pos": rm_match.start(),
            })
            continue

        # 构造新 RM 表
        new_table = build_rm_table_xml(v4_coauthors)
        new_block = f"<h5>Researcher Mapping</h5>\n{new_table}"
        new_content = new_content[:rm_match.start()] + new_block + new_content[rm_match.end():]
        report.append({
            "arxiv_id": arxiv_id,
            "status": "replaced",
            "n_v4_authors": len(v4_coauthors),
        })
        # 不更新 seen 因为 new_content 已变更，下次循环重新扫描

    return new_content, report


def write_compare_md(date: str, report: list[dict], batch_data: list[dict]) -> str:
    """生成 v2 vs v3 对比 markdown。"""
    lines: list[str] = []
    lines.append(f"# 5.21 日报 v2 → v3 对比报告（V4 RM enrich）\n")
    lines.append(f"生成时间：基于 `data/state/rm_v4_batch/{date}.json` 的 V4 enrich 数据\n")
    lines.append("---\n")

    # 替换统计
    n_replaced = sum(1 for r in report if r["status"] == "replaced")
    n_no_data = sum(1 for r in report if r["status"] == "no_v4_data")
    n_no_rm = sum(1 for r in report if r["status"] == "no_rm_table")
    lines.append(f"## 替换概览\n")
    lines.append(f"- 总 arxiv 引用数：{len(report)}")
    lines.append(f"- 已替换 RM 表：{n_replaced}")
    lines.append(f"- 无 V4 数据（非 whitelist arxiv，保留 v2 原表）：{n_no_data}")
    lines.append(f"- 无 RM 表（折叠区等）：{n_no_rm}\n")

    # 每篇详情
    arxiv_to_v4 = {b["arxiv_id"]: b for b in batch_data}
    lines.append("## 每篇详情\n")
    for r in report:
        if r["status"] != "replaced":
            continue
        arxiv_id = r["arxiv_id"]
        v4 = arxiv_to_v4.get(arxiv_id, {})
        coauthors = v4.get("coauthors", [])
        total = v4.get("n_authors_total", "?")
        wl = v4.get("n_authors_whitelist", "?")
        lines.append(f"### arxiv {arxiv_id}（v4 选 {len(coauthors)} 位，原始 {total} 位，白名单 {wl} 位）\n")
        if not coauthors:
            lines.append("> ⚠ V4 审查 agent 整位剔除所有候选作者\n")
            continue
        lines.append("| 姓名 | 角色 | 白名单 | 现状 | GitHub | Homepage | 字段验证 |")
        lines.append("|---|---|---|---|---|---|---|")
        for c in coauthors:
            v = c.get("verification") or {}
            v_str = " ".join(f"{k}={v[k][:8]}" for k in sorted(v.keys()) if k != "email")
            wl_mark = "★" if c.get("is_whitelist") else ""
            lines.append(
                f"| {c.get('name','')} | {c.get('role','')} | {wl_mark} | "
                f"{c.get('affiliation') or '—'} | {c.get('github') or '—'} | "
                f"{c.get('homepage') or '—'} | `{v_str}` |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-05-21")
    args = ap.parse_args()

    v2_path = Path(str(V2_PATH_TEMPLATE).format(date=args.date))
    batch_path = Path(str(V4_BATCH_TEMPLATE).format(date=args.date))
    v3_out = Path(str(V3_OUT_TEMPLATE).format(date=args.date))
    cmp_out = Path(str(COMPARE_OUT_TEMPLATE).format(date=args.date))

    if not v2_path.exists():
        print(f"! v2 not found: {v2_path}")
        return 1
    if not batch_path.exists():
        print(f"! batch data not found: {batch_path}")
        return 1

    v2_content = v2_path.read_text()
    batch_data = json.loads(batch_path.read_text())

    arxiv_to_coauthors = {b["arxiv_id"]: b["coauthors"] for b in batch_data}
    print(f"loaded v2 ({len(v2_content)} chars) + V4 batch ({len(batch_data)} papers)")

    new_content, report = replace_rm_tables(v2_content, arxiv_to_coauthors)

    v3_out.write_text(new_content)
    cmp_md = write_compare_md(args.date, report, batch_data)
    cmp_out.write_text(cmp_md)

    n_replaced = sum(1 for r in report if r["status"] == "replaced")
    n_no_data = sum(1 for r in report if r["status"] == "no_v4_data")
    n_no_rm = sum(1 for r in report if r["status"] == "no_rm_table")
    print(f"\n=== generation done ===")
    print(f"  v3 markdown: {v3_out}  ({len(new_content)} chars)")
    print(f"  compare md:  {cmp_out}")
    print(f"  RM 表替换: {n_replaced} 个")
    print(f"  无 V4 数据保留 v2:  {n_no_data} 个")
    print(f"  无 RM 表（折叠区等）: {n_no_rm} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
