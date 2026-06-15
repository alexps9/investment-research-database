"""Send daily digest summary to enterprise Feishu group via custom webhook bot.

Reads a generated digest XML from data/digests/digest_<date>.xml, extracts
title + overview + top 3 headlines, builds a Feishu interactive card, and
posts it to a custom group bot webhook (with HMAC-SHA256 signing).

Env vars (required for --send, optional for --preview):
    HH_LARK_ENTERPRISE_WEBHOOK_URL
    HH_LARK_ENTERPRISE_WEBHOOK_SECRET

Usage:
    # Preview only (no network call):
    python scripts/send_digest_to_enterprise.py 2026-05-13

    # Actually send:
    python scripts/send_digest_to_enterprise.py 2026-05-13 --send

    # With explicit XML path:
    python scripts/send_digest_to_enterprise.py --xml data/digests/digest_2026-05-13.xml --send
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / ".env")


# ---------- XML extraction ----------

HEADLINE_BOLD_LINK = re.compile(
    r"<p><b>(?P<title>.*?)</b>\s*·\s*<a href=\"(?P<url>[^\"]+)\">(?P<linktext>.*?)</a></p>",
    re.DOTALL,
)
H4_PATTERN = re.compile(r"<h4>(?P<title>.*?)</h4>", re.DOTALL)
LINK_LI_PATTERN = re.compile(
    r"<li><b>链接</b>：<a href=\"(?P<url>[^\"]+)\">(?P<linktext>.*?)</a></li>",
    re.DOTALL,
)


def _strip_tags(s: str) -> str:
    """Strip XML/HTML tags for plain-text rendering."""
    return re.sub(r"<[^>]+>", "", s).strip()


def _xml_to_feishu_md(s: str) -> str:
    """Convert inline XML tags to Feishu lark_md syntax (preserve emphasis + links).

    Used by build_card so that organization names, key numbers, and ↗ jump
    links stay bold/clickable when rendered in the IM card.

    Rules:
      <b>xxx</b>            → **xxx**            (markdown bold)
      <i>xxx</i>            → *xxx*              (markdown italic)
      <a href="URL">xxx</a> → [xxx](URL)         (markdown link · 飞书 lark_md 支持点击跳转)
      <a> 无 href           → xxx                (drop tag, 保留内文)
      other tags            → strip (keep inner text)

    历史: 2026-05-26 修复 — 之前丢 URL 导致 TLDR ↗ 链接在卡片里不可点
    """
    if not s:
        return s
    s = re.sub(r"<b>(.*?)</b>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s, flags=re.DOTALL)
    # <a href="URL">text</a> → [text](URL) 保留可点跳转
    s = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.DOTALL)
    # 兜底: 无 href 的 <a> 标签去掉 (理论上不应出现)
    s = re.sub(r'<a[^>]*>(.*?)</a>', r"\1", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


# Card grouping order — keep aligned with prompt's 5+1 track list.
# After 5.22 rename, "基础模型" replaces "认知模型"; both kept here for
# transition compatibility (old XML may still emit 认知模型 during rename window).
_TRACK_ORDER = [
    "基础模型",
    "认知模型",          # back-compat during 5.22 rename rollout
    "多模态智能",
    "世界模型",
    "AI infra",
    "ai4s",
    "商业进展",          # 5.22 new sub-track under 行业应用
    "行业应用",
]


def _extract_track(bullet_md: str) -> str | None:
    """Extract 【track】 tag prefix from a TL;DR bullet."""
    m = re.match(r"\s*【([^】]+)】", bullet_md)
    return m.group(1).strip() if m else None


def _strip_track_prefix(bullet_md: str) -> str:
    """Drop the 【track】 prefix (we surface it via section header instead)."""
    return re.sub(r"^\s*【[^】]+】\s*", "", bullet_md)


def _render_grouped_tldr(bullets_md: list[str]) -> str:
    """Group bullets by 赛道 + render as Feishu lark_md.

    Layout (5.22 design A):
      ━━ **基础模型**（3）━━
      ⭐ **OpenAI** ... — **+15.30%**     ← top of first track marked ⭐
      · **Yejin Choi** ...
      · ...

      ━━ **AI infra**（1）━━
      · **Alibaba Cloud** ...

    Groups appear in the order their first bullet appeared in the input
    (preserves LLM's intended importance ranking). Per-track count in ()
    helps users glance the day's distribution.
    """
    if not bullets_md:
        return ""

    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for b in bullets_md:
        track = _extract_track(b) or "其他"
        text = _strip_track_prefix(b)
        if track not in grouped:
            grouped[track] = []
            order.append(track)
        grouped[track].append(text)

    lines: list[str] = []
    is_first_group = True
    for track in order:
        items = grouped[track]
        # User 5-29 feedback (Option D): keep ━━ decoration, drop blank line
        # between tracks for tighter visual density.
        lines.append(f"━━ **{track}**（{len(items)}）━━")
        for i, item in enumerate(items):
            marker = "⭐ " if (is_first_group and i == 0) else "· "
            lines.append(f"{marker}{item}")
        is_first_group = False

    return "\n".join(lines).strip()


def _tldr_to_bullets(tldr: str) -> tuple[str, list[str]]:
    """Split '<intro>：<a>；<b>；<c>。' into (intro, [a, b, c])."""
    text = tldr.strip().rstrip("。")
    if "：" in text:
        intro, rest = text.split("：", 1)
    else:
        intro, rest = "", text
    items = [s.strip().rstrip("。").rstrip("；") for s in re.split(r"[；;]", rest) if s.strip()]
    return intro.strip(), items


def extract(xml_text: str) -> dict:
    """Pull out the pieces we need for the card."""
    # Title
    title_match = re.search(r"<title>(.*?)</title>", xml_text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "HH Research Daily"

    # Overview — only accept the signal-count callout (emoji="🌅") to avoid
    # accidentally grabbing the first headline's "Our Insights" callout when the
    # overview block is omitted by newer daily_writer versions.
    overview_match = re.search(
        r'<callout[^>]*emoji="🌅"[^>]*>(.*?)</callout>', xml_text, re.DOTALL
    )
    overview = (
        _strip_tags(overview_match.group(1)).replace("\n", " ")
        if overview_match
        else ""
    )
    overview = re.sub(r"\s+", " ", overview)
    # Strip the leading "本日信号概览：" prefix if present (redundant with card framing)
    overview = re.sub(r"^本日信号概览[:：]\s*", "", overview)

    # TL;DR — three formats observed across iterations:
    #   v3 (5-18+):       <h2>TL;DR</h2><ul><li>item</li>...</ul>
    #   v2 (5-15):        <h2>今日 TL;DR</h2><ul><li>item</li>...</ul>
    #   v1 (5-13/5-14):   <h2>今日 TL;DR</h2><p>intro：item；item；item。</p>
    # Match "(今日 )?TL;DR" with optional "今日 " prefix to cover all three.
    ul_match = re.search(
        r"<h2>(?:今日 )?TL;DR</h2>\s*<ul>(.*?)</ul>", xml_text, re.DOTALL
    )
    if ul_match:
        items = re.findall(r"<li>(.*?)</li>", ul_match.group(1), re.DOTALL)
        tldr_intro = ""
        tldr_bullets = [_strip_tags(it) for it in items if _strip_tags(it)]
        tldr_bullets_md = [_xml_to_feishu_md(it) for it in items if _strip_tags(it)]
    else:
        p_match = re.search(
            r"<h2>(?:今日 )?TL;DR</h2>\s*<p>(.*?)</p>", xml_text, re.DOTALL
        )
        tldr = _strip_tags(p_match.group(1)) if p_match else ""
        tldr_intro, tldr_bullets = _tldr_to_bullets(tldr)
        # v1 paragraph form has no per-bullet XML; markdown == plain for fallback
        tldr_bullets_md = list(tldr_bullets)

    return {
        "title": title,
        "overview": overview,
        "tldr_intro": tldr_intro,
        "tldr_bullets": tldr_bullets,
        "tldr_bullets_md": tldr_bullets_md,
    }


# ---------- Card payload ----------

def build_card(content: dict, digest_url: str | None = None) -> dict:
    """Build a Feishu interactive card payload (msg_type=interactive).

    Layout (concise):
        Header (blue, title)
        Overview line (signals/papers count)
        ──
        TL;DR header
        Intro line + bullet list of items
        Button: 查看完整日报 (if digest_url provided)
        Footer note
    """
    elements: list[dict] = []

    # Only include overview row when daily_writer actually emitted the 🌅 callout.
    if content.get("overview"):
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**本日概览** · {content['overview']}",
                },
            }
        )
        elements.append({"tag": "hr"})

    # TL;DR section — 5.22 design A: group by track + bold orgs/numbers + ⭐ headline
    tldr_lines = ["**🎯 今日 TL;DR**"]
    if content["tldr_intro"]:
        tldr_lines.append("")
        tldr_lines.append(content["tldr_intro"] + "：")
    # Prefer the markdown-rendered bullets (preserves <b> as **xxx**); fall back to plain.
    bullets_md = content.get("tldr_bullets_md") or content.get("tldr_bullets") or []
    # 5-29 fix: anchor.placeholder URLs in TL;DR ↗ links are unresolved placeholders
    # (the wiki doc has them resolved to real anchors, but .md keeps placeholders).
    # Replace with digest_url so ↗ at least jumps to the wiki doc top.
    if digest_url:
        bullets_md = [
            re.sub(r"https?://anchor\.placeholder/[^)\s]+", digest_url, b)
            for b in bullets_md
        ]
    if bullets_md:
        grouped = _render_grouped_tldr(bullets_md)
        if grouped:
            tldr_lines.append("")
            tldr_lines.append(grouped)

    elements.append(
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": "\n".join(tldr_lines)},
        }
    )

    # Detailed digest link button
    if digest_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📖 查看完整日报"},
                        "url": digest_url,
                        "type": "primary",
                    }
                ],
            }
        )

    # Footer note
    elements.append(
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": "由 HH Research AI Pipeline 自动生成 · 每日早间推送",
                }
            ],
        }
    )

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": content["title"]},
                "template": "blue",
            },
            "elements": elements,
        },
    }


# ---------- Signing & send ----------

def gen_sign(timestamp: int, secret: str) -> str:
    """Feishu webhook signature: HMAC-SHA256, key = '<ts>\\n<secret>', body = ''."""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


def send(webhook_url: str, secret: str, card_payload: dict) -> dict:
    ts = int(time.time())
    body = {
        "timestamp": str(ts),
        "sign": gen_sign(ts, secret),
        **card_payload,
    }
    r = httpx.post(
        webhook_url,
        json=body,
        timeout=30,
        # Avoid local proxy interception
        trust_env=False,
    )
    try:
        return r.json()
    except Exception:
        return {"status_code": r.status_code, "text": r.text}


# ---------- CLI ----------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "date",
        nargs="?",
        default=None,
        help="Digest date (YYYY-MM-DD); resolves to data/digests/digest_<date>.xml",
    )
    p.add_argument("--xml", help="Explicit path to digest XML (overrides date)")
    p.add_argument(
        "--digest-url",
        default=None,
        help="Optional URL to append as '查看完整日报' button (skip if no enterprise wiki yet)",
    )
    p.add_argument(
        "--title",
        default=None,
        help="Optional card title override; useful when local digest file date differs from publish date",
    )
    p.add_argument(
        "--send",
        action="store_true",
        help="Actually post to webhook (otherwise: preview JSON only)",
    )
    args = p.parse_args()

    # Resolve XML path
    if args.xml:
        xml_path = Path(args.xml)
    elif args.date:
        xml_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "digests"
            / f"digest_{args.date}.xml"
        )
    else:
        print("Error: provide a date (e.g. 2026-05-13) or --xml <path>", file=sys.stderr)
        return 2

    if not xml_path.exists():
        print(f"Error: digest file not found: {xml_path}", file=sys.stderr)
        return 2

    xml_text = xml_path.read_text(encoding="utf-8")
    content = extract(xml_text)
    if args.title:
        content["title"] = args.title

    print("=" * 60, file=sys.stderr)
    print(f"Extracted from: {xml_path.name}", file=sys.stderr)
    print(f"  Title:    {content['title']}", file=sys.stderr)
    print(f"  Overview: {content['overview'][:80]}", file=sys.stderr)
    print(f"  TL;DR intro: {content['tldr_intro']}", file=sys.stderr)
    print(f"  TL;DR bullets ({len(content['tldr_bullets'])}):", file=sys.stderr)
    for i, b in enumerate(content["tldr_bullets"], 1):
        print(f"    {i}. {b[:80]}", file=sys.stderr)
    print(f"  Digest URL: {args.digest_url or '(none)'}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    card = build_card(content, digest_url=args.digest_url)

    if not args.send:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        print(
            "\n[preview] No network call made. Re-run with --send to post.",
            file=sys.stderr,
        )
        return 0

    # Send mode
    url = os.environ.get("HH_LARK_ENTERPRISE_WEBHOOK_URL")
    secret = os.environ.get("HH_LARK_ENTERPRISE_WEBHOOK_SECRET")
    if not url or not secret:
        print(
            "Error: HH_LARK_ENTERPRISE_WEBHOOK_URL and "
            "HH_LARK_ENTERPRISE_WEBHOOK_SECRET must be set for --send",
            file=sys.stderr,
        )
        return 2

    resp = send(url, secret, card)
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return 0 if resp.get("code") == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
