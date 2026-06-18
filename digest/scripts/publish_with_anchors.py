"""Two-stage publisher with anchor link injection (v3 daily digest).

Flow:
    1. Pre-process markdown: rewrite (anchor:xxx) → (https://anchor.placeholder/xxx)
       so the link survives docx conversion as a valid URL.
    2. Call publish_digest() — get obj_token + node URL.
    3. Fetch doc with --detail with-ids → enumerate blocks.
    4. Identify anchor marker text blocks ({anchor:xxx}) and map each to the
       NEXT block (= the heading we want to jump to).
    5. For each anchor key, docs +update str_replace to swap the placeholder URL
       with https://my.feishu.cn/docx/<obj_token>?block_id=<target_id>.
    6. Delete the anchor marker text blocks (they served as markers only).
    7. Return final URL.

Usage:
    from publish_with_anchors import publish_with_anchors
    result = publish_with_anchors(title="HH Research Daily 2026-05-20", markdown=md)
    print(result["url"])

CLI:
    python scripts/publish_with_anchors.py --title "..." --markdown @data/digests/digest_2026-05-20.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.publish.lark_doc_publisher import (  # noqa: E402
    PublishError,
    _lark_cli,
    publish_digest,
)
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("publish_with_anchors")

PLACEHOLDER_HOST = "https://anchor.placeholder"
ANCHOR_TEXT_PATTERN = re.compile(r"^\{anchor:([A-Za-z0-9_一-鿿]+)\}$")
ANCHOR_URL_PATTERN = re.compile(r"\(anchor:([A-Za-z0-9_一-鿿]+)\)")


def preprocess_markdown(markdown: str) -> str:
    """Rewrite (anchor:xxx) link targets to a valid placeholder URL.

    Leave {anchor:xxx} text markers untouched — they'll appear as text blocks
    after publish and we use them to identify target blocks.
    """
    return ANCHOR_URL_PATTERN.sub(
        lambda m: f"({PLACEHOLDER_HOST}/{m.group(1)})", markdown
    )


def fetch_blocks_with_ids(obj_token: str) -> list[dict[str, Any]]:
    """Fetch doc content as flat list of blocks with their IDs and text content.

    Returns a list of dicts in document order. Each dict has at minimum:
      - block_id: the block id
      - text: stripped plain text content of the block (best-effort)
      - block_type: the type (heading1/heading2/heading3/text/etc.)
    """
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
    content_xml = (
        resp.get("data", {})
        .get("document", {})
        .get("content", "")
    )
    if not content_xml:
        raise PublishError("fetch returned empty content")

    # The with-ids format embeds block_id attributes inline as
    # <p data-block-id="blk_xxx">...</p>, similar for h1..h4. We scan top-level.
    # This is a regex-based parse — sufficient because we only need text + block_id
    # for marker matching.
    # 飞书 with-ids 格式：<tag id="doxcn...">...</tag>
    # 仅匹配带 id 属性的顶层 block 标签
    block_pattern = re.compile(
        r'<(?P<tag>p|h[1-9]|li|callout|table)\b[^>]*?\bid="(?P<bid>[^"]+)"[^>]*>(?P<inner>.*?)</(?P=tag)>',
        re.DOTALL,
    )
    blocks = []
    for m in block_pattern.finditer(content_xml):
        inner = m.group("inner")
        text = re.sub(r"<[^>]+>", "", inner).strip()
        blocks.append({
            "block_id": m.group("bid"),
            "block_type": m.group("tag"),
            "text": text,
        })
    return blocks


def build_anchor_map(blocks: list[dict[str, Any]]) -> tuple[dict[str, str], list[str]]:
    """Identify {anchor:xxx} text blocks and map each to the NEXT block's id.

    Returns:
        anchor_map: { 'headline_1': 'blk_target1', 'section_基础模型': 'blk_target2', ... }
        marker_block_ids: list of block_ids of the anchor marker text blocks (for cleanup)
    """
    anchor_map: dict[str, str] = {}
    marker_block_ids: list[str] = []
    for i, b in enumerate(blocks):
        m = ANCHOR_TEXT_PATTERN.match(b["text"])
        if not m:
            continue
        key = m.group(1)
        marker_block_ids.append(b["block_id"])
        # Target = next block's id (skip empty / marker blocks)
        for j in range(i + 1, len(blocks)):
            nxt = blocks[j]
            nxt_text = nxt["text"]
            if ANCHOR_TEXT_PATTERN.match(nxt_text):
                continue  # skip chained markers
            anchor_map[key] = nxt["block_id"]
            break
    return anchor_map, marker_block_ids


def replace_anchor_urls(obj_token: str, anchor_map: dict[str, str],
                        wiki_node_token: str | None = None) -> dict[str, bool]:
    """For each anchor key, str_replace the placeholder URL with the real share link.

    v3 (5.21): 调内部 API `partial_content_anchor/create` 为每个 block_id 生成
    真正的 anchor_id（27-char），URL 形式 `#share-<anchor_id>`，跟用户"复制选区
    链接"的行为完全一致。

    fallback: 若 anchor_id 生成失败（cookie 过期等），degrade 到 `?block_id=<id>` 旧格式。
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from hh_research.publish.feishu_anchor import (  # noqa: E402
        create_anchor, get_doc_revision, build_share_url, FeishuAnchorError,
    )

    # 先拿当前 doc revision (structure_version)
    try:
        revision = get_doc_revision(obj_token)
        log.info("  doc revision_id (structure_version): %d", revision)
    except FeishuAnchorError as e:
        log.warning("  cannot get doc revision (%s); using fallback URL format", e)
        revision = None

    results: dict[str, bool] = {}
    for key, target_id in anchor_map.items():
        placeholder = f"{PLACEHOLDER_HOST}/{key}"

        # v3: 调 partial_content_anchor/create 拿 anchor_id
        anchor_id = None
        if revision is not None:
            try:
                anchor_id = create_anchor(
                    page_id=obj_token,
                    block_id=target_id,
                    structure_version=revision,
                    src_end_idx=1,  # 最小值，对任何 block 通用
                    wiki_node_token=wiki_node_token,
                )
                log.info("  anchor %s: block %s → anchor_id %s",
                         key, target_id[:12], anchor_id[:12])
            except FeishuAnchorError as e:
                log.warning("  anchor_create failed for %s (%s)", target_id[:12], e)

        if anchor_id and wiki_node_token:
            real_url = build_share_url(wiki_node_token, anchor_id)
        elif anchor_id:
            real_url = f"https://my.feishu.cn/docx/{obj_token}#share-{anchor_id}"
        elif wiki_node_token:
            # fallback: 旧格式（点击会新建窗口）
            real_url = f"https://my.feishu.cn/wiki/{wiki_node_token}?block_id={target_id}"
        else:
            real_url = f"https://my.feishu.cn/docx/{obj_token}?block_id={target_id}"
        try:
            # markdown mode required — XML mode 在 <a href=""> 属性值上找不到匹配
            resp = _lark_cli(
                "docs", "+update",
                "--api-version", "v2",
                "--doc", obj_token,
                "--command", "str_replace",
                "--doc-format", "markdown",
                "--pattern", placeholder,
                "--content", real_url,
                timeout=60,
            )
            ok = resp.get("ok", False)
            data = resp.get("data", {})
            result_status = data.get("result", "ok")
            warnings = data.get("warnings", [])
            if ok and result_status != "failed":
                results[key] = True
                log.info("  anchor %s → %s", key, target_id[:16])
            else:
                results[key] = False
                log.warning("  anchor %s replace failed: result=%s warnings=%s",
                            key, result_status, warnings[:1] if warnings else None)
        except Exception as e:  # noqa: BLE001
            log.warning("  anchor %s replace exception: %s", key, e)
            results[key] = False
        time.sleep(0.3)
    return results


def delete_marker_blocks(obj_token: str, marker_block_ids: list[str]) -> int:
    """Delete the {anchor:xxx} placeholder text blocks. Returns count deleted."""
    if not marker_block_ids:
        return 0
    deleted = 0
    # Batch in groups of 10 to avoid overly long --block-id arg
    for i in range(0, len(marker_block_ids), 10):
        batch = marker_block_ids[i:i + 10]
        try:
            resp = _lark_cli(
                "docs", "+update",
                "--api-version", "v2",
                "--doc", obj_token,
                "--command", "block_delete",
                "--block-id", ",".join(batch),
                timeout=60,
            )
            if resp.get("ok"):
                deleted += len(batch)
            else:
                log.warning("  block_delete batch failed: %s", resp.get("error"))
        except Exception as e:  # noqa: BLE001
            log.warning("  block_delete exception: %s", e)
        time.sleep(0.3)
    return deleted


def inject_anchors_inplace(obj_token: str, wiki_node_token: str | None = None) -> dict[str, Any]:
    """Operate on an existing doc: resolve anchor placeholders + delete marker blocks.

    Args:
        obj_token: docx 对象 token
        wiki_node_token: 如果该 doc 是 wiki 子节点，传入 node_token → 锚点 URL 用
            `https://my.feishu.cn/wiki/{node}?block_id=…` 保持同节点跳转。
            否则 fallback 到 docx URL（用户点击会"新建窗口打开"）。
    """
    log.info("inject_anchors_inplace on doc %s (wiki_node=%s)", obj_token, wiki_node_token)
    blocks = fetch_blocks_with_ids(obj_token)
    log.info("  %d blocks fetched", len(blocks))
    anchor_map, marker_block_ids = build_anchor_map(blocks)
    log.info("  anchors found: %d, marker blocks: %d", len(anchor_map), len(marker_block_ids))

    replace_results = {}
    if anchor_map:
        replace_results = replace_anchor_urls(obj_token, anchor_map, wiki_node_token)
    deleted = 0
    if marker_block_ids:
        deleted = delete_marker_blocks(obj_token, marker_block_ids)
        log.info("  deleted %d marker blocks", deleted)

    return {
        "obj_token": obj_token,
        "anchor_map": anchor_map,
        "anchor_replace_results": replace_results,
        "markers_deleted": deleted,
    }


def publish_with_anchors(
    title: str,
    markdown: str,
    parent_node_token: str | None = None,
    space_id: str | None = None,
) -> dict[str, Any]:
    """Publish markdown with anchor placeholders → resolve anchors → cleanup.

    Returns dict with:
      - url, obj_token, node_token, title (from publish_digest)
      - anchor_map: { key: target_block_id }
      - anchor_replace_results: { key: bool }
      - markers_deleted: int
    """
    # Stage 1: pre-process markdown so anchor placeholders are valid URLs
    md = preprocess_markdown(markdown)

    # Stage 2: publish
    log.info("publishing doc: %s", title)
    pub = publish_digest(
        title=title,
        markdown=md,
        parent_node_token=parent_node_token,
        space_id=space_id,
    )
    obj_token = pub["obj_token"]

    # Stage 3: fetch with block IDs
    log.info("fetching doc with block IDs ...")
    blocks = fetch_blocks_with_ids(obj_token)
    log.info("  %d blocks fetched", len(blocks))

    # Stage 4: build anchor map
    anchor_map, marker_block_ids = build_anchor_map(blocks)
    log.info("  anchors found: %d", len(anchor_map))
    log.info("  marker blocks to delete: %d", len(marker_block_ids))

    # Stage 5: replace placeholder URLs with real block_id links
    if anchor_map:
        log.info("replacing %d anchor URLs ...", len(anchor_map))
        replace_results = replace_anchor_urls(obj_token, anchor_map)
    else:
        replace_results = {}

    # Stage 6: delete marker text blocks
    deleted = 0
    if marker_block_ids:
        log.info("deleting %d marker blocks ...", len(marker_block_ids))
        deleted = delete_marker_blocks(obj_token, marker_block_ids)
        log.info("  deleted %d", deleted)

    return {
        **pub,
        "anchor_map": anchor_map,
        "anchor_replace_results": replace_results,
        "markers_deleted": deleted,
    }


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument(
        "--markdown",
        required=True,
        help="markdown content; prefix with @ to read from file",
    )
    args = ap.parse_args()

    if args.markdown.startswith("@"):
        md = Path(args.markdown[1:]).read_text(encoding="utf-8")
    else:
        md = args.markdown

    result = publish_with_anchors(title=args.title, markdown=md)
    print(json.dumps(
        {
            "url": result["url"],
            "obj_token": result["obj_token"],
            "anchors_resolved": len(result["anchor_map"]),
            "markers_deleted": result["markers_deleted"],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
