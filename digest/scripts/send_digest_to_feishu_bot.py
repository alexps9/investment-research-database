"""Send daily digest as Feishu interactive card to team members via 1-on-1 bot.

Reads a generated digest XML from data/digests/digest_<date>.xml, reuses the
title + overview + TL;DR extraction AND the interactive-card build logic from
send_digest_to_enterprise.py (so 1-on-1 push is byte-identical to the group
broadcast card), and pushes to each recipient open_id via HRes' aha moment
app.

Recipient resolution (priority):
  1. CLI --recipients (highest)
  2. Bitable subscribers table (status=active) — subscription-based, queried at run time
  3. .env FEISHU_BOT_RECIPIENT_OPENIDS (fallback if Bitable unavailable)
Pass --no-bitable to skip step 2 (force .env fallback).

Env vars (required for --send, optional for dry-run preview):
    FEISHU_BOT_APP_ID
    FEISHU_BOT_APP_SECRET
    FEISHU_BOT_RECIPIENT_OPENIDS   (fallback recipients if Bitable empty/unreachable)

Bitable subscribers source (defaults to HH Research Pipeline base):
    base_token = UdwrbpCMoasCs3snCvbcKgbsnfc
    table_id   = tbl4kcz0Gr5yIXpn  (subscribers)
    Filter:    status field == 'active'

Usage:
    # Dry-run preview (no network call, shows card JSON + recipient count):
    python scripts/send_digest_to_feishu_bot.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ

    # Send to Bitable active subscribers (production default):
    python scripts/send_digest_to_feishu_bot.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ --send

    # Force .env fallback (skip Bitable):
    python scripts/send_digest_to_feishu_bot.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ --no-bitable --send

    # Override recipients on CLI:
    python scripts/send_digest_to_feishu_bot.py 2026-05-20 \
        --digest-url https://my.feishu.cn/wiki/XYZ \
        --recipients ou_alice,ou_bob --send
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hh_research.publish.feishu_bot_publisher import (  # noqa: E402
    VALID_RECEIVE_ID_TYPES,
    FeishuBotAPIError,
    FeishuBotPublisher,
)
from send_digest_to_enterprise import build_card, extract  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

# Bitable subscribers source — single source of truth for production push targets
SUBSCRIBERS_BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"  # HH Research Pipeline base
SUBSCRIBERS_TABLE_ID = "tbl4kcz0Gr5yIXpn"  # subscribers table (created 5.22)


def _resolve_digest_path(date: str | None, explicit: str | None) -> Path | None:
    """Resolve the digest file path, preferring .xml then .md.

    Resolution order:
      1. explicit --xml path (wins even if extension is .md)
      2. data/digests/digest_<date>.xml
      3. latest data/digests/digest_<date>*.xml
      4. data/digests/digest_<date>.md
      5. latest data/digests/digest_<date>*.md

    Returns the resolved Path, or None if nothing found.

    Note: daily.py currently emits .md whose content is XML-like; extract()
    parses both identically, so .md is a safe fallback (5-29 incident fix).
    """
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    if not date:
        return None

    digests = REPO_ROOT / "data" / "digests"
    # Exact .xml
    exact_xml = digests / f"digest_{date}.xml"
    if exact_xml.exists():
        return exact_xml
    # Latest digest_<date>*.xml
    xmls = sorted(digests.glob(f"digest_{date}*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    if xmls:
        return xmls[0]
    # Exact .md
    exact_md = digests / f"digest_{date}.md"
    if exact_md.exists():
        return exact_md
    # Latest digest_<date>*.md
    mds = sorted(digests.glob(f"digest_{date}*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if mds:
        return mds[0]
    return None


def _extract_email(raw) -> str | None:
    """Pull a plain email out of Bitable's email field value.

    Bitable email-typed cells render as either:
      - Plain string: "alice@x.com"
      - Markdown link: "[alice@x.com](mailto:alice@x.com)"
      - Array of segments: [{"text":"...", "link":"mailto:..."}]
    Return clean "alice@x.com" or None if no email found.
    """
    if raw is None:
        return None
    import re
    if isinstance(raw, list):
        for seg in raw:
            if isinstance(seg, dict):
                link = seg.get("link") or ""
                if link.startswith("mailto:"):
                    return link[len("mailto:"):].strip()
                text = seg.get("text") or ""
                if "@" in text:
                    return text.strip()
        return None
    if isinstance(raw, str):
        m = re.search(r"mailto:([^)\s]+)", raw)
        if m:
            return m.group(1).strip()
        if "@" in raw:
            # plain email or markdown like "[a@b.com](...)"; strip brackets
            cleaned = re.sub(r"[\[\]()]", "", raw).split("(")[0].strip()
            if "@" in cleaned:
                return cleaned
    return None


def _coerce_status(raw) -> str | None:
    """Normalize a select cell value to plain status string."""
    if raw is None:
        return None
    if isinstance(raw, list) and raw:
        first = raw[0]
        return first.get("name") if isinstance(first, dict) else str(first)
    if isinstance(raw, dict):
        return raw.get("name")
    return str(raw)


def load_active_subscribers_from_bitable(group: str | None = None) -> tuple[list[str], list[str]]:
    """Read subscribers Bitable, return (recipients, log_lines).

    Each recipient is either an open_id (preferred) or an email (fallback when
    open_id is empty in the row). Feishu API auto-infers receive_id_type:
      - "ou_xxx"        → open_id
      - "alice@x.com"   → email
    This dual-mode supports both:
      1. User-initiated subscription via bot ("订阅" → row written with open_id)
      2. Admin-managed roster (admin adds email only; auto-推送 by email)

    If `group` is given (e.g. "G0", "G1"), only rows with matching `group` cell
    are included. If None (default), all active rows are included.
    """
    import subprocess
    log: list[str] = []
    # Retry 2x to survive transient Bitable API timeouts (e.g. TLS handshake).
    last_err = None
    proc = None
    for attempt in range(2):
        try:
            proc = subprocess.run(
                ["lark-cli", "--profile", "personal", "base", "+record-list",
                 "--as", "user",
                 "--base-token", SUBSCRIBERS_BASE_TOKEN,
                 "--table-id", SUBSCRIBERS_TABLE_ID,
                 "--limit", "200",
                 "--format", "json"],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "LARK_CLI_NO_PROXY": "1"},
            )
            if proc.returncode == 0:
                break
            last_err = f"rc={proc.returncode}, stderr={proc.stderr[:200]}"
        except Exception as e:
            last_err = f"exception: {e}"
        if attempt == 0:
            log.append(f"Bitable subscribers query attempt 1 failed ({last_err}); retrying...")
    if proc is None or proc.returncode != 0:
        log.append(f"Bitable subscribers query failed after retries: {last_err}")
        return ([], log)
    try:
        data = json.loads(proc.stdout)
        rows = data.get("data", {}).get("data", [])
        fields = data.get("data", {}).get("fields", [])
        idx = {name: i for i, name in enumerate(fields)}
        if "status" not in idx:
            log.append(f"Bitable subscribers schema missing 'status' field; got: {fields}")
            return ([], log)
        has_open_id = "open_id" in idx
        has_email = "email" in idx
        has_group = "group" in idx
        if group and not has_group:
            log.append(f"Bitable subscribers schema missing 'group' field but --group={group} requested; got: {fields}")
            return ([], log)
        if not has_open_id and not has_email:
            log.append(f"Bitable schema needs open_id or email field; got: {fields}")
            return ([], log)

        recipients: list[str] = []
        used_open_id = 0
        used_email = 0
        skipped_unsub = 0
        skipped_no_id = 0
        skipped_group_mismatch = 0
        for row in rows:
            status_val = row[idx["status"]] if idx["status"] < len(row) else None
            status_name = _coerce_status(status_val)
            if status_name != "active":
                skipped_unsub += 1
                continue
            if group:
                group_val = row[idx["group"]] if idx["group"] < len(row) else None
                group_name = _coerce_status(group_val)  # same select-cell shape
                if group_name != group:
                    skipped_group_mismatch += 1
                    continue
            # prefer open_id; fallback to email
            picked = None
            if has_open_id:
                oid = row[idx["open_id"]] if idx["open_id"] < len(row) else None
                if isinstance(oid, str) and oid.strip():
                    picked = oid.strip()
                    used_open_id += 1
            if picked is None and has_email:
                email_raw = row[idx["email"]] if idx["email"] < len(row) else None
                email_clean = _extract_email(email_raw)
                if email_clean:
                    picked = email_clean
                    used_email += 1
            if picked:
                recipients.append(picked)
            else:
                skipped_no_id += 1
        log.append(
            f"Bitable subscribers: {len(recipients)} active"
            f"{f' group={group}' if group else ''} "
            f"(open_id={used_open_id}, email={used_email}, "
            f"unsubscribed={skipped_unsub}, group_mismatch={skipped_group_mismatch}, "
            f"no_id={skipped_no_id}, total_rows={len(rows)})"
        )
        return (recipients, log)
    except Exception as e:
        log.append(f"Bitable subscribers parse exception: {e}")
        return ([], log)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "date",
        nargs="?",
        default=None,
        help="Digest date YYYY-MM-DD (resolves to data/digests/digest_<date>.xml, .md fallback)",
    )
    p.add_argument("--xml", help="Explicit path to digest file (.xml or .md; overrides date)")
    p.add_argument(
        "--digest-url",
        default=None,
        help="Wiki URL for the '查看完整日报' button (required for --send)",
    )
    p.add_argument("--title", help="Title override")
    p.add_argument(
        "--recipients",
        default=None,
        help="Comma-separated receive_ids (overrides FEISHU_BOT_RECIPIENT_OPENIDS env)",
    )
    p.add_argument(
        "--receive-id-type",
        default=None,
        choices=sorted(VALID_RECEIVE_ID_TYPES),
        help="Force all recipients to this id type. Default: auto-infer per "
        "recipient (email / ou_xxx / on_xxx / oc_xxx / else user_id)",
    )
    p.add_argument(
        "--send",
        action="store_true",
        help="Actually call Feishu API (otherwise dry-run preview)",
    )
    p.add_argument(
        "--no-bitable",
        action="store_true",
        help="Skip Bitable subscribers query, force .env fallback only",
    )
    p.add_argument(
        "--group",
        default=None,
        choices=("G0", "G1"),
        help="Filter Bitable subscribers by group. Omit = all active subscribers (default).",
    )
    args = p.parse_args()

    # Resolve digest path (.xml preferred, .md fallback — daily.py now emits .md
    # whose content is XML-like and extract() parses it the same way).
    digest_path = _resolve_digest_path(args.date, args.xml)
    if digest_path is None:
        if args.xml:
            print(f"Error: digest file not found: {args.xml}", file=sys.stderr)
        elif args.date:
            print(
                f"Error: no digest found for {args.date} "
                f"(tried digest_{args.date}.xml/.md and digest_{args.date}*.xml/.md)",
                file=sys.stderr,
            )
        else:
            print("Error: provide a date (e.g. 2026-05-20) or --xml <path>", file=sys.stderr)
        return 2
    xml_path = digest_path  # keep downstream variable name (preview/log)

    xml_text = xml_path.read_text(encoding="utf-8")
    content = extract(xml_text)
    if args.title:
        content["title"] = args.title

    # Refuse to send if no TL;DR bullets (avoid pushing a blank card)
    if not content.get("tldr_bullets"):
        print(
            f"Error: no TL;DR bullets extracted from {xml_path.name}. "
            "Digest may use a legacy format; Feishu bot push refused to avoid "
            "sending a near-empty card.",
            file=sys.stderr,
        )
        if args.send:
            return 2

    # Build the interactive card (byte-identical to enterprise group broadcast)
    card = build_card(content, digest_url=args.digest_url)

    # Resolve recipients (priority: CLI > Bitable subscribers > .env fallback)
    recipients: list[str] = []
    recipients_source = "cli"
    bitable_log: list[str] = []
    if args.recipients:
        recipients = [s.strip() for s in args.recipients.split(",") if s.strip()]
        recipients_source = f"cli (--recipients), {len(recipients)} ids"
    elif not args.no_bitable:
        recipients, bitable_log = load_active_subscribers_from_bitable(group=args.group)
        if recipients:
            group_suffix = f", group={args.group}" if args.group else ""
            recipients_source = f"Bitable subscribers (status=active{group_suffix}), {len(recipients)} ids"
    if not recipients:
        recip_str = os.environ.get("FEISHU_BOT_RECIPIENT_OPENIDS", "")
        recipients = [s.strip() for s in recip_str.split(",") if s.strip()]
        if recipients:
            recipients_source = f".env FEISHU_BOT_RECIPIENT_OPENIDS fallback, {len(recipients)} ids"
    for line in bitable_log:
        print(f"  [Bitable] {line}", file=sys.stderr)

    # ---- Preview ----
    bar = "=" * 60
    print(bar, file=sys.stderr)
    print("Feishu bot 1-on-1 push preview", file=sys.stderr)
    print(f"  Source:        {xml_path.name}", file=sys.stderr)
    print(f"  Title:         {content['title']}", file=sys.stderr)
    print(f"  TL;DR bullets: {len(content.get('tldr_bullets') or [])}", file=sys.stderr)
    print(
        f"  receive_id_type: {args.receive_id_type or '(auto-infer per recipient)'}",
        file=sys.stderr,
    )
    print(
        f"  Recipients:    {len(recipients)} "
        f"{recipients[:3]}{'...' if len(recipients) > 3 else ''}",
        file=sys.stderr,
    )
    print(f"  Source:        {recipients_source}", file=sys.stderr)
    print(f"  Jump URL:      {args.digest_url or '(none)'}", file=sys.stderr)
    print(bar, file=sys.stderr)

    # ---- Dry-run ----
    if not args.send:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        print(
            "\n[dry-run] No network call made. Re-run with --send to push.",
            file=sys.stderr,
        )
        return 0

    # ---- Send ----
    if not args.digest_url:
        print("Error: --digest-url required for --send", file=sys.stderr)
        return 2
    if not recipients:
        print(
            "Error: no recipients (set FEISHU_BOT_RECIPIENT_OPENIDS env or "
            "pass --recipients)",
            file=sys.stderr,
        )
        return 2

    try:
        pub = FeishuBotPublisher()
    except FeishuBotAPIError as e:
        print(f"Error: Feishu bot credentials not configured: {e}", file=sys.stderr)
        return 2

    # build_card returns {msg_type:"interactive", card:{...}}; we just need the inner card
    card_inner = card.get("card", card)

    try:
        result = pub.send_card_to_recipients(
            receive_ids=recipients,
            card=card_inner,
            receive_id_type=args.receive_id_type,
        )
    except Exception as e:
        print(f"Error: Feishu bot push failed: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("failed"):
        # Some recipients failed but batch ran — exit 0 (broadcast script logs it)
        # Per-recipient failure is non-fatal (user may have blocked bot, etc.)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
