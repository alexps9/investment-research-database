#!/usr/bin/env python3
"""审核 agent: 对照 v7.0 spec 审核日报 XML（来自飞书 URL 或本地文件）。

参考 plan /Users/haolinguo/Desktop/2026-05-28-v7-quality-gates.md Task 3.

执行 2 层审核:
1. Hard checks（规则）: 复用 hh_research.quality.digest_rules.review_xml_text
   - source="file"   严格 check callout color attribute
   - source="feishu" callout color 只警告（飞书渲染后 fall back rgb）
2. Soft checks（LLM）: 风格匹配（framework update / Why this matters）+ 改写建议
   只作为风格建议，**不影响 blocking status**

用法:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"

    # 审核飞书 URL
    .venv/bin/python scripts/digest_review_agent.py \\
        --doc "https://my.feishu.cn/wiki/XXX" \\
        --output data/logs/review_2026-05-28.md

    # 审核本地 generated XML/md
    .venv/bin/python scripts/digest_review_agent.py \\
        --file data/digests/digest_2026-05-28.md

可选 flag:
    --skip-llm  只跑规则审核（快，本地，~5 秒）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.extract.claude_client import make_client, resolve_model_id  # noqa: E402
from hh_research.quality.digest_rules import (  # noqa: E402
    ReviewSeverity,
    review_xml_text,
)
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("digest_review_agent")


# ────────────────────────────────────────────────────────────────────
# Fetch
# ────────────────────────────────────────────────────────────────────

def fetch_doc_xml(url: str) -> str:
    """Fetch 飞书 docx XML（带 block IDs）via lark-cli."""
    env = dict(os.environ)
    env["LARK_CLI_NO_PROXY"] = "1"
    r = subprocess.run(
        ["lark-cli", "docs", "+fetch", "--api-version", "v2",
         "--doc", url, "--detail", "with-ids"],
        capture_output=True, text=True, env=env,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"lark-cli fetch failed: rc={r.returncode} stderr={r.stderr[:400]}"
        )
    try:
        return json.loads(r.stdout)["data"]["document"]["content"]
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"failed parse fetch response: {e}; raw={r.stdout[:300]}")


def read_file_xml(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ────────────────────────────────────────────────────────────────────
# LLM soft check（optional · 风格建议 · 不影响 blocking）
# ────────────────────────────────────────────────────────────────────

LLM_REVIEWER_PROMPT = """你是 HH Research 投研日报审稿员。对照下面的"标杆 Insights 示例"，判断给定 Insights 是否符合 v7.0 spec。

## 标杆示例 1（Why this matters · 谢赛宁 Cambrian-P · 140 字）

> 这篇论文表明:让通用大模型"看懂"视频里的 3D 空间,不再需要外接一套专门的 3D 重建系统——训练时多加一个相机位姿(camera pose)token 就够了,推理时甚至这个 token 都不用。**这意味着原本专门做 3D 重建、SLAM(同步定位与建图)的技术路线,作为通用大模型之外的独立赛道,存在意义会被削弱**——它们正在变成通用大模型里的一个小模块。

## 标杆示例 2（framework update · 华为 τ 缩放 · 175 字）

> 华为正在尝试争夺**芯片性能上的话语权**——把进步的衡量标准从"制程节点走多远"换成 τ(一个跨所有层级的统一时间常数);论文中 "the next dollar should follow τ, not nodes" 一句基本明示了华为期待的资本配置方向。如果这套框架被业界部分接受,"先进制程是进步唯一锚点"的叙事会被稀释;3D 集成、互联、芯片整机栈(stack)协同设计等此前被视为辅助路径的方向,在叙事重要性上的权重可能上升。

## 待审 Insights

```
{insights_text}
```

## 请按以下格式输出（**只输出这 4 行**）

风格类型: <framework update / Why this matters / 混合 / 不明>
匹配度评分: <1-5>（5=完全匹配标杆，1=完全不像）
主要问题: <1-3 个最重要问题，每个 < 30 字>
改写建议: <1-2 句话>
"""


def llm_soft_check(callout_inner: str, client, model: str) -> str:
    ps_raw = re.findall(r"<p[^>]*>(.*?)</p>", callout_inner, re.DOTALL)
    if len(ps_raw) < 2:
        return "skip: Insights 段数不足"
    content = re.sub(r"<[^>]+>", "", ps_raw[1]).strip()
    if not content:
        return "skip: Insights 内容为空"
    prompt = LLM_REVIEWER_PROMPT.format(insights_text=content)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:  # noqa: BLE001
        return f"LLM 审稿失败: {e}"


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def review(xml: str, source: str, skip_llm: bool = False) -> str:
    """Run quality gate + optional LLM soft check, return markdown report."""
    report = review_xml_text(xml, source=source)

    lines = [report.to_markdown()]

    if not skip_llm and report.cards:
        log.info("running LLM soft check on %d cards ...", len(report.cards))
        client = make_client(max_retries=1, timeout=60.0)
        model = resolve_model_id("claude-sonnet-4-6")

        lines.append("\n---\n\n# LLM 风格评审（参考，不阻断发布）\n")
        # parse card body again to get callout_inner per card
        # we reuse the same _parse_cards by importing it
        from hh_research.quality.digest_rules import _parse_cards
        cards_with_body = _parse_cards(xml)
        for c in cards_with_body:
            lines.append(f"\n## {c['label']}\n\n")
            verdict = llm_soft_check(c.get("callout_inner", ""), client, model)
            lines.append("```\n")
            lines.append(verdict + "\n")
            lines.append("```\n")

    return "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    src_group = ap.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--doc", help="飞书文档 URL（含 /wiki/ 或 /docx/）")
    src_group.add_argument("--file", help="本地 generated XML/md 文件路径")
    ap.add_argument("--output", default=None, help="report output path（默认 stdout）")
    ap.add_argument("--skip-llm", action="store_true",
                    help="仅跑规则检查（不调 LLM）")
    args = ap.parse_args()

    if args.doc:
        log.info("fetching doc: %s", args.doc[:80])
        xml = fetch_doc_xml(args.doc)
        source = "feishu"
    else:
        path = Path(args.file)
        log.info("reading file: %s", path)
        xml = read_file_xml(path)
        source = "file"

    report_md = review(xml, source=source, skip_llm=args.skip_llm)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report_md, encoding="utf-8")
        log.info("report saved to %s", out)
    else:
        print(report_md)


if __name__ == "__main__":
    main()
