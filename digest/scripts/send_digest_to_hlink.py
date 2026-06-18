"""Send daily digest summary to HH Research team via H Link (HCMLink) 1-on-1 push.

Reads a generated digest XML from data/digests/digest_<date>.xml, reuses the
title + overview + TL;DR extraction from send_digest_to_enterprise.py, formats
them as plain-text H Link textcard `content` (<=1000 chars), and posts to one
or more H Link open_ids via /cgi/message/send.

Env vars (required for --send, optional for dry-run preview):
    H_LINK_APP_ID
    H_LINK_APP_KEY
    H_LINK_APP_SECRET
    H_LINK_PORTAL                 (optional)
    H_LINK_RECIPIENT_OPENIDS      (comma-separated default recipients)

Usage:
    # Dry-run preview (no network, shows payload + char-count stats):
    python scripts/send_digest_to_hlink.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ

    # Actually send:
    python scripts/send_digest_to_hlink.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ --send

    # Send to specific recipients (overrides H_LINK_RECIPIENT_OPENIDS):
    python scripts/send_digest_to_hlink.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ \
        --recipients oid_alice,oid_bob --send

    # Explicit XML path (e.g. for backfill or test fixtures):
    python scripts/send_digest_to_hlink.py --xml data/digests/digest_2026-05-20.xml \
        --digest-url https://my.feishu.cn/wiki/XYZ
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
# Ensure src/ is on sys.path so we can import hh_research.* when invoked as a script
sys.path.insert(0, str(REPO_ROOT / "src"))
# Sibling scripts/ for extract() reuse
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hh_research.publish.hlink_publisher import (  # noqa: E402
    SAFE_CONTENT_LIMIT,
    TEXTCARD_CONTENT_LIMIT,
    HLinkAPIError,
    HLinkPublisher,
)
from send_digest_to_enterprise import extract  # noqa: E402

load_dotenv(REPO_ROOT / ".env")


# ---------- Content composition ----------

SEPARATOR = "─" * 29  # visual divider line in textcard

# Strip Feishu-wiki anchor placeholders like (↗) / （↗） — H Link has no
# per-bullet jump; the whole card jumps to a single URL, so anchor markers
# are noise in H Link textcards.
_ANCHOR_PLACEHOLDER = re.compile(r"[（(]\s*↗\s*[)）]")


def _clean_bullet(s: str) -> str:
    s = _ANCHOR_PLACEHOLDER.sub("", s)
    return re.sub(r"\s+", " ", s).strip().rstrip("。").rstrip("；")


def build_summary_lines(content: dict) -> list[str]:
    """Convert extracted digest dict into H Link textcard plain-text lines.

    Target layout (≤1000 chars total after join with '\\n'):

        本日概览: <overview>
        ─────────────────────────────
        今日 TL;DR

        1. 【track】<bullet 1>
        2. 【track】<bullet 2>
        ...

        查看完整日报 →
    """
    lines: list[str] = []

    overview = (content.get("overview") or "").strip()
    if overview:
        lines.append(f"本日概览: {overview}")
        lines.append(SEPARATOR)

    lines.append("今日 TL;DR")
    lines.append("")

    intro = (content.get("tldr_intro") or "").strip()
    if intro:
        lines.append(intro + "：")

    for i, b in enumerate(content.get("tldr_bullets") or [], 1):
        lines.append(f"{i}. {_clean_bullet(b)}")

    lines.append("")
    lines.append("查看完整日报 →")
    return lines


def fit_to_limit(lines: list[str], limit: int = SAFE_CONTENT_LIMIT) -> list[str]:
    """Drop the lowest-priority TL;DR bullets first if total content exceeds limit.

    Priority order (kept first): overview, separator, TL;DR heading, intro,
    bullets 1..N, footer. We pop from the tail of bullets (after the "今日 TL;DR"
    block, before the footer) until it fits.
    """
    joined = "\n".join(lines)
    if len(joined) <= limit:
        return lines

    # Find indices of bullets (lines starting with "N. ")
    bullet_indices = [i for i, ln in enumerate(lines) if ln and ln[:1].isdigit() and ". " in ln[:4]]

    while len(joined) > limit and bullet_indices:
        drop = bullet_indices.pop()  # drop last bullet
        lines.pop(drop)
        joined = "\n".join(lines)

    # If still over limit (overview alone too long), the publisher.truncate_content
    # will hard-cut with "..." at the very end.
    return lines


# ---------- CLI ----------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "date",
        nargs="?",
        default=None,
        help="Digest date YYYY-MM-DD (resolves to data/digests/digest_<date>.xml)",
    )
    p.add_argument("--xml", help="Explicit path to digest XML (overrides date)")
    p.add_argument(
        "--digest-url",
        default=None,
        help="Wiki URL to jump to when user taps the textcard (required for --send)",
    )
    p.add_argument(
        "--title",
        default=None,
        help="Title override (otherwise uses <title> from digest XML)",
    )
    p.add_argument(
        "--recipients",
        default=None,
        help="Comma-separated open_ids (overrides env / --group)",
    )
    p.add_argument(
        "--group",
        default=None,
        choices=("G0", "G1"),
        help="Pick recipients from env H_LINK_RECIPIENT_OPENIDS_<group> (G0 or G1). "
             "Omit = use H_LINK_RECIPIENT_OPENIDS (all).",
    )
    p.add_argument(
        "--send",
        action="store_true",
        help="Actually call H Link API (otherwise dry-run preview)",
    )
    args = p.parse_args()

    # Resolve XML path
    if args.xml:
        xml_path = Path(args.xml)
    elif args.date:
        xml_path = REPO_ROOT / "data" / "digests" / f"digest_{args.date}.xml"
    else:
        print("Error: provide a date (e.g. 2026-05-20) or --xml <path>", file=sys.stderr)
        return 2
    if not xml_path.exists():
        print(f"Error: digest XML not found: {xml_path}", file=sys.stderr)
        return 2

    xml_text = xml_path.read_text(encoding="utf-8")
    content = extract(xml_text)
    if args.title:
        content["title"] = args.title

    # Safety: refuse to send if no TL;DR bullets were extracted (intro alone
    # is not enough — it's just a header phrase). Legacy digest formats with
    # <p><b>track</b>...</p> narrative TL;DR fall through here. For --send
    # this exits 2; broadcast_today.sh treats it as non-blocking WARN.
    if not content.get("tldr_bullets"):
        print(
            f"Error: no TL;DR bullets extracted from {xml_path.name}. "
            "Digest likely uses a legacy <p>-narrative format; H Link push "
            "refused to avoid sending a near-empty card.",
            file=sys.stderr,
        )
        if args.send:
            return 2

    summary_lines = build_summary_lines(content)
    summary_lines = fit_to_limit(summary_lines)
    content_str = "\n".join(summary_lines)
    char_count = len(content_str)

    # Resolve recipients (priority: --recipients > --group-specific env > generic env)
    if args.recipients:
        recip_str = args.recipients
        recipients_source = "cli --recipients"
    elif args.group:
        env_key = f"H_LINK_RECIPIENT_OPENIDS_{args.group}"
        recip_str = os.environ.get(env_key, "")
        recipients_source = f"env {env_key}"
        if not recip_str:
            print(f"Warning: --group {args.group} but {env_key} is empty", file=sys.stderr)
    else:
        recip_str = os.environ.get("H_LINK_RECIPIENT_OPENIDS", "")
        recipients_source = "env H_LINK_RECIPIENT_OPENIDS (all)"
    recipients = [s.strip() for s in recip_str.split(",") if s.strip()]
    print(f"  recipients source: {recipients_source}", file=sys.stderr)

    # ---- Preview ----
    bar = "=" * 60
    print(bar, file=sys.stderr)
    print(f"H Link textcard preview", file=sys.stderr)
    print(f"  Source:        {xml_path.name}", file=sys.stderr)
    print(f"  Title:         {content['title']}", file=sys.stderr)
    print(f"  Overview:      {(content.get('overview') or '')[:80]}", file=sys.stderr)
    print(f"  TL;DR bullets: {len(content.get('tldr_bullets') or [])}", file=sys.stderr)
    print(
        f"  Recipients:    {len(recipients)} "
        f"{recipients[:3]}{'...' if len(recipients) > 3 else ''}",
        file=sys.stderr,
    )
    print(
        f"  Content chars: {char_count} / {TEXTCARD_CONTENT_LIMIT} "
        f"(buffer {TEXTCARD_CONTENT_LIMIT - char_count})",
        file=sys.stderr,
    )
    print(f"  Jump URL:      {args.digest_url or '(none)'}", file=sys.stderr)
    print(bar, file=sys.stderr)
    print("--- textcard.content (literal) ---", file=sys.stderr)
    print(content_str, file=sys.stderr)
    print("--- end ---", file=sys.stderr)

    if char_count > TEXTCARD_CONTENT_LIMIT:
        print(
            "WARN: content exceeds 1000 chars even after fit_to_limit; "
            "publisher will hard-truncate with '...'",
            file=sys.stderr,
        )

    # ---- Dry-run ----
    if not args.send:
        pub = HLinkPublisher(
            app_id=os.environ.get("H_LINK_APP_ID") or "<H_LINK_APP_ID>",
            app_key=os.environ.get("H_LINK_APP_KEY") or "<H_LINK_APP_KEY>",
            app_secret=os.environ.get("H_LINK_APP_SECRET") or "<H_LINK_APP_SECRET>",
            portal=os.environ.get("H_LINK_PORTAL"),
        )
        payload = pub.build_textcard_payload(
            open_ids=recipients or ["<oid_placeholder>"],
            title=content["title"],
            content=content_str,
            url=args.digest_url or "<digest_url_placeholder>",
        )
        # Redact secrets even in dry-run (we never put secret in payload, but in case)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(
            "\n[dry-run] No network call made. Re-run with --send to post.",
            file=sys.stderr,
        )
        return 0

    # ---- Send ----
    if not args.digest_url:
        print("Error: --digest-url required for --send", file=sys.stderr)
        return 2
    if not recipients:
        print(
            "Error: no recipients (set H_LINK_RECIPIENT_OPENIDS env or pass --recipients)",
            file=sys.stderr,
        )
        return 2

    try:
        pub = HLinkPublisher()
    except HLinkAPIError as e:
        print(f"Error: H Link credentials not configured: {e}", file=sys.stderr)
        return 2

    try:
        resp = pub.send_textcard(
            open_ids=recipients,
            title=content["title"],
            summary_lines=summary_lines,
            url=args.digest_url,
        )
    except Exception as e:
        print(f"Error: H Link push failed: {e}", file=sys.stderr)
        return 1

    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
