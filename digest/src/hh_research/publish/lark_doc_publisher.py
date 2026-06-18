"""Publish a daily digest markdown to Feishu as a wiki docx, then notify the user.

Flow:
    1. Create wiki child node under HH_DIGEST_PARENT_NODE_TOKEN with given title
    2. Take the new node's obj_token (= docx token)
    3. lark-cli docs +update --mode overwrite with markdown content
    4. (optional) Download + insert paper figure images using signal.url as anchor
    5. Return the canonical wiki URL
    6. Send a chat notification to the user with the URL

Env vars used:
    HH_DIGEST_WIKI_SPACE_ID
    HH_DIGEST_PARENT_NODE_TOKEN
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from ..utils.logger import get_logger

log = get_logger("lark_doc_publisher")

UA = {"User-Agent": "Mozilla/5.0 (HH Research Pipeline)"}
IMG_CACHE_DIR = Path("data/img_cache")
ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class PublishError(RuntimeError):
    pass


def _lark_cli(*args: str, profile: str = "personal", timeout: int = 90) -> dict[str, Any]:
    """Run lark-cli with --profile and return parsed JSON. Raises on failure."""
    cmd = ["lark-cli", "--profile", profile, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if r.returncode != 0:
        raise PublishError(f"lark-cli failed: rc={r.returncode} stderr={r.stderr[:500]}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise PublishError(f"non-JSON response: {r.stdout[:300]}") from e


def _download_image(url: str, timeout: float = 20.0) -> Path | None:
    """Download remote image to data/img_cache/. Returns local Path or None.

    Supports both remote https:// URLs and local file:// URLs (the PyMuPDF
    PDF-fallback emits file:// URLs for cached images).
    """
    if url.startswith("file://"):
        from urllib.parse import unquote
        local_path = Path(unquote(url.removeprefix("file://")))
        if not (local_path.exists() and local_path.stat().st_size > 0):
            log.warning("file:// img not found: %s", url[:80])
            return None
        # lark-cli 要求 --file 是相对路径，转成相对 CWD
        try:
            rel = local_path.resolve().relative_to(Path.cwd().resolve())
            return Path(str(rel))
        except ValueError:
            # 不在 CWD 子树下，复制到 IMG_CACHE_DIR
            IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            dst = IMG_CACHE_DIR / local_path.name
            if not dst.exists():
                dst.write_bytes(local_path.read_bytes())
            return dst

    IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Stable filename from URL hash
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:14]
    ext = ".jpg"
    url_lower = url.lower()
    for e in ALLOWED_IMG_EXT:
        if e in url_lower:
            ext = e
            break
    local = IMG_CACHE_DIR / f"{h}{ext}"
    if local.exists() and local.stat().st_size > 0:
        return local
    try:
        with httpx.Client(headers=UA, timeout=timeout, follow_redirects=True) as c:
            resp = c.get(url)
            if resp.status_code != 200:
                log.warning("img download HTTP %d: %s", resp.status_code, url[:80])
                return None
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                log.warning("img download not image (%s): %s", content_type, url[:80])
                return None
            local.write_bytes(resp.content)
            return local
    except Exception as e:  # noqa: BLE001
        log.warning("img download failed: %s -> %s", url[:80], e)
        return None


def insert_signal_images(
    obj_token: str,
    signals: list[Any],
    max_per_signal: int = 1,
    sleep_between: float = 0.3,
) -> dict[str, int]:
    """Download each signal's images and insert them into the doc.

    v7.0 5-27 rewrite: 旧版用 --selection-with-ellipsis signal.url 在飞书 docx
    中查找 URL 文本作为锚点 → 飞书 <a href=URL>标题</a> block 显示的是"标题"
    文本不是 URL → 100% VALIDATION:1101 找不到匹配 → 0/N inserted。

    新版流程：
    1. fetch with-ids 一次拿带 block_id 的 docx XML
    2. 对每个 signal，用 href="signal.url" 定位 <li>/<a> block 位置
    3. 在所属卡片范围 (<h3 id> / <h4 id> 之间) 内找 RM <table id>
    4. target = table 之前最后一个 block（=解读最后一段，紧贴 RM 之前）
    5. media-insert 上传图（自动插末尾），从返回拿 temp_block_id
    6. block_move_after 把 temp_block_id 移到 target_id 之后 = 图插在解读后、RM 前

    Returns counts: {attempted, inserted, skipped, failed}.
    """
    counts = {"attempted": 0, "inserted": 0, "skipped": 0, "failed": 0}

    # Pre-flight: 收集所有有图待插的 signals
    pending = [
        s for s in signals
        if (getattr(s, "image_urls", None) or [])
        and getattr(s, "url", None) and len(getattr(s, "url", "")) >= 10
    ]
    if not pending:
        return counts

    # Step 1: fetch with-ids
    try:
        resp = _lark_cli(
            "docs", "+fetch", "--api-version", "v2",
            "--doc", obj_token, "--detail", "with-ids",
        )
        xml = resp["data"]["document"]["content"]
    except (PublishError, KeyError) as e:
        log.error("insert_signal_images: failed to fetch doc structure: %s", e)
        counts["failed"] = len(pending)
        return counts

    # Pre-compute: 所有 h3/h4/hr block 位置（卡片边界）
    card_boundary_re = re.compile(r'<(h3|h4|hr)\s+id="([^"]+)"')
    boundaries = [(m.start(), m.group(1), m.group(2)) for m in card_boundary_re.finditer(xml)]

    # Helper: fuzzy match arxiv URLs (signal.url 可能带 v1/v2 后缀，但 LLM 输出 href
    # 是无版本号的 abs URL → 直接字符串 find 会 0 match)
    def _arxiv_id(u: str) -> str | None:
        m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?', u)
        return m.group(1) if m else None

    # Step 2-3-4: 为每个 signal 计算 target_block_id
    url_to_target: dict[str, str] = {}
    for s in pending:
        anchor_url = s.url
        # 先尝试严格匹配
        href_idx = xml.find(f'href="{anchor_url}"')
        if href_idx < 0:
            # Fallback: arxiv id fuzzy match（去版本后缀）
            aid = _arxiv_id(anchor_url)
            if aid:
                # 用 regex 找含此 arxiv id 的 href（任何 v 后缀）
                fuzzy = re.search(
                    rf'href="https?://arxiv\.org/(?:abs|pdf)/{re.escape(aid)}(?:v\d+)?[^"]*"',
                    xml
                )
                if fuzzy:
                    href_idx = fuzzy.start()
        if href_idx < 0:
            log.warning("href not found in doc XML: %s", anchor_url[:80])
            continue

        # 找此 href 所属卡片：往前找最近的 h3/h4，往后找下一个 h3/h4/hr
        prev_card_starts = [b for b in boundaries if b[0] < href_idx and b[1] in ("h3", "h4")]
        next_card_starts = [b for b in boundaries if b[0] > href_idx]
        if not prev_card_starts:
            log.warning("no card header before href %s", anchor_url[:80])
            continue
        card_start = prev_card_starts[-1][0]
        card_end = next_card_starts[0][0] if next_card_starts else len(xml)
        card_xml = xml[card_start:card_end]

        # 找 RM <table id>
        table_m = re.search(r'<table\s+id="([^"]+)"', card_xml)
        if table_m:
            # target = table 之前最后一个 block
            blocks_before_table = list(re.finditer(
                r'<(\w+)\s+id="([^"]+)"', card_xml[:table_m.start()]
            ))
            # 跳过 h3/h4 本身（卡片标题），找之后的最后一个 block
            content_blocks = [
                m for m in blocks_before_table
                if m.group(1) not in ("h3", "h4", "hr")
            ]
            if not content_blocks:
                continue
            target_id = content_blocks[-1].group(2)
        else:
            # 无 RM 表格 → target = 卡片内最后一个非 h3/h4 block
            all_blocks = list(re.finditer(r'<(\w+)\s+id="([^"]+)"', card_xml))
            content_blocks = [
                m for m in all_blocks
                if m.group(1) not in ("h3", "h4", "hr")
            ]
            if not content_blocks:
                continue
            target_id = content_blocks[-1].group(2)

        url_to_target[anchor_url] = target_id

    log.info(
        "insert_signal_images: resolved %d/%d target block_ids",
        len(url_to_target), len(pending)
    )

    # Step 5-6: 对每个有 target 的 signal: upload + move
    for s in pending:
        anchor_url = s.url
        target_id = url_to_target.get(anchor_url)
        if not target_id:
            n = len(s.image_urls or [])
            counts["skipped"] += min(n, max_per_signal)
            continue

        for img_url in (s.image_urls or [])[:max_per_signal]:
            counts["attempted"] += 1
            local = _download_image(img_url)
            if not local:
                counts["failed"] += 1
                continue
            try:
                # Step 5: media-insert 上传图（自动插末尾），拿临时 block_id
                upload_resp = _lark_cli(
                    "docs", "+media-insert",
                    "--doc", obj_token,
                    "--type", "image",
                    "--file", str(local),
                    "--align", "center",
                )
                if not upload_resp.get("ok"):
                    counts["failed"] += 1
                    log.warning("media-insert upload failed: %s", upload_resp.get("error"))
                    continue
                temp_block_id = upload_resp.get("data", {}).get("block_id")
                if not temp_block_id:
                    counts["failed"] += 1
                    log.warning("no block_id in media-insert response")
                    continue

                # Step 6: block_move_after 把图块移到 target 之后
                move_resp = _lark_cli(
                    "docs", "+update",
                    "--api-version", "v2",
                    "--doc", obj_token,
                    "--command", "block_move_after",
                    "--block-id", target_id,
                    "--src-block-ids", temp_block_id,
                )
                if move_resp.get("ok"):
                    counts["inserted"] += 1
                    log.info(
                        "  ✓ inserted image after %s (anchor=%s...)",
                        target_id, anchor_url[:60]
                    )
                else:
                    counts["failed"] += 1
                    log.warning("block_move_after failed: %s", move_resp.get("error"))
            except PublishError as e:
                counts["failed"] += 1
                log.warning("image insert failed: %s", e)
            time.sleep(sleep_between)
    return counts


def set_public_access(obj_token: str, obj_type: str = "docx") -> bool:
    """把云文档链接共享设为「互联网上获得链接的人可阅读」(anyone_readable)。

    best-effort：失败只告警、不抛错（不阻断发布）。需 lark-cli 具备 `docs:permission.setting` scope。
    ⚠️ obj_type 必须用 **docx**（底层文档 obj_token）——wiki 节点类型不支持 anyone_readable/external_access。
    互联网可读 = external_access:true + link_share_entity:anyone_readable（见 drive permission.public patch schema）。
    """
    try:
        resp = _lark_cli(
            "drive", "permission.public", "patch",
            "--params", json.dumps({"token": obj_token, "type": obj_type}),
            "--data", json.dumps({"external_access": True, "link_share_entity": "anyone_readable"}),
            "--yes",
        )
    except Exception as e:  # noqa: BLE001
        log.warning("  set_public_access failed (non-blocking): %s", e)
        return False
    if resp.get("ok") or resp.get("code") == 0:
        log.info("  ✅ public access set: anyone_readable (%s)", obj_token)
        return True
    log.warning("  set_public_access non-ok: %s", resp.get("error") or resp.get("msg"))
    return False


def publish_digest(
    title: str,
    markdown: str,
    parent_node_token: str | None = None,
    space_id: str | None = None,
) -> dict[str, str]:
    """Create a new wiki docx under the parent node and write markdown to it.

    Returns dict with: node_token, obj_token, url, title.
    """
    space_id = space_id or os.environ["HH_DIGEST_WIKI_SPACE_ID"]
    parent_node_token = parent_node_token or os.environ["HH_DIGEST_PARENT_NODE_TOKEN"]

    # Step 1: create wiki child node
    log.info("creating wiki node: %s", title)
    resp = _lark_cli(
        "wiki", "+node-create",
        "--space-id", space_id,
        "--parent-node-token", parent_node_token,
        "--title", title,
        "--obj-type", "docx",
    )
    if not resp.get("ok"):
        raise PublishError(f"node-create failed: {resp.get('error')}")

    data = resp.get("data", {})
    node_token = data.get("node_token", "")
    obj_token = data.get("obj_token", "")
    if not obj_token or not node_token:
        raise PublishError(f"node-create missing tokens in response: {data}")
    log.info("  node_token=%s, obj_token=%s", node_token, obj_token)

    # Step 2: write content (overwrite mode replaces all content)
    # 自动检测格式：剥掉 LLM 可能套的 ```xml ... ``` 代码栅栏后，
    # 内容以 <title> 或 <h1>/<h2> 等 XML 标签开头 → 用 XML 模式
    # 否则用 markdown 模式（向后兼容）
    content_stripped = markdown.strip()
    if content_stripped.startswith("```"):
        # 去掉首行的 ```xml / ```markdown / ``` 等
        lines = content_stripped.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].rstrip() == "```":
            lines = lines[:-1]
        content_stripped = "\n".join(lines).strip()
        log.info("  stripped ``` code fence wrapper from LLM output")
        markdown = content_stripped
    is_xml = content_stripped.startswith("<title>") or content_stripped.startswith("<h")
    ext = ".xml" if is_xml else ".md"
    rel_path = f"./data/_tmp_digest_publish{ext}"
    Path(rel_path).parent.mkdir(parents=True, exist_ok=True)
    Path(rel_path).write_text(markdown, encoding="utf-8")
    try:
        log.info("  writing %s content (%d chars)", "XML" if is_xml else "markdown", len(markdown))
        if is_xml:
            resp = _lark_cli(
                "docs", "+update",
                "--api-version", "v2",
                "--doc", obj_token,
                "--command", "overwrite",
                "--content", f"@{rel_path}",
            )
        else:
            resp = _lark_cli(
                "docs", "+update",
                "--doc", obj_token,
                "--mode", "overwrite",
                "--markdown", f"@{rel_path}",
            )
        if not resp.get("ok"):
            raise PublishError(f"docs update failed: {resp.get('error')}")
    finally:
        try:
            Path(rel_path).unlink()
        except FileNotFoundError:
            pass

    url = f"https://my.feishu.cn/wiki/{node_token}"
    log.info("  published: %s", url)
    # v9 (2026-06-04): env HH_DIGEST_PUBLIC=1 → 发布后自动把链接设为「互联网可读」(anyone_readable)。
    # 默认关（避免意外公开投研内容）；需 lark-cli 具备 docs:permission.setting scope。
    if os.getenv("HH_DIGEST_PUBLIC", "0") == "1":
        set_public_access(obj_token, obj_type="docx")
    return {"node_token": node_token, "obj_token": obj_token, "url": url, "title": title}


def notify_digest_ready(
    user_open_id: str,
    title: str,
    doc_url: str,
    signal_count: int,
    headline_count: int = 0,
) -> bool:
    """Send a markdown chat message to the user about the new digest.

    Returns True on success.
    """
    md = (
        f"**HH Research Daily 已生成**\n\n"
        f"**{title}**\n\n"
        f"信号总数：{signal_count} 条 · 头条 {headline_count} 条\n\n"
        f"[点击查看完整日报]({doc_url})"
    )
    try:
        resp = _lark_cli(
            "im", "+messages-send",
            "--as", "user",
            "--user-id", user_open_id,
            "--markdown", md,
        )
        if resp.get("ok"):
            log.info("  notification sent to %s", user_open_id)
            return True
        log.warning("notification failed: %s", resp.get("error"))
        return False
    except PublishError as e:
        log.warning("notification command failed: %s", e)
        return False
