#!/usr/bin/env python3
"""Subscribe listener — Feishu IM keyword → Bitable subscribers + bot reply.

Reads `im.message.receive_v1` events as NDJSON on stdin (one per line),
matches user-sent text against keyword patterns, and:
  1. Upserts the `subscribers` Bitable table (active / unsubscribed)
  2. Sends a confirmation IM reply via lark-cli

Designed to run as a long-running daemon under launchd, fed by:
    lark-cli event consume im.message.receive_v1 --as bot | python subscribe_listener.py

Only p2p (private) text messages are processed; group / non-text are ignored.

Schema notes (from `event schema im.message.receive_v1 --json`):
  - Fields are flat at root: .chat_type / .sender_id / .message_type / .content
  - .content is pre-rendered plain text for `text` messages (no fromjson needed)

Keywords (case-insensitive):
  - 订阅 / subscribe / 订阅日报      → status=active
  - 取消订阅 / 取消 / unsubscribe / 退订 → status=unsubscribed
  - 状态 / status / 我的订阅          → reply current status
  - 帮助 / help / ? / unknown        → reply help text
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------- Configuration ----------

SUBSCRIBERS_BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"  # HH Research Pipeline base
SUBSCRIBERS_TABLE_ID = "tbl4kcz0Gr5yIXpn"  # subscribers table

# Two profiles, different use cases:
#   - Bitable read/write needs USER identity (郭昊霖's personal profile has full
#     access to HH Research Pipeline base).
#   - IM reply needs the HRes' aha moment BOT identity (so replies come from the
#     same bot users search/subscribe; not from a random "郭昊霖 personal app").
LARK_CLI_PROFILE_BITABLE = "personal"  # Bitable ops, --as user
LARK_CLI_PROFILE_IM_BOT = "hres-bot"   # IM replies, --as bot (HRes' aha moment)

# Intent regex patterns (matched against stripped, lowercased text)
SUBSCRIBE_PATTERNS = [r"^订阅$", r"^subscribe$", r"^订阅日报$", r"^开启订阅$"]
UNSUBSCRIBE_PATTERNS = [r"^取消订阅$", r"^取消$", r"^unsubscribe$", r"^退订$", r"^关闭订阅$"]
STATUS_PATTERNS = [r"^状态$", r"^status$", r"^我的订阅$", r"^查询状态$"]
HELP_PATTERNS = [r"^帮助$", r"^help$", r"^\?$", r"^？$", r"^菜单$"]

HELP_TEXT = (
    "您好！欢迎使用 HH Research Daily 订阅助手 🤖\n\n"
    "📨 可用命令（直接输入即可）：\n"
    "  • 订阅 — 开启每日日报推送（BJT 12:00 主线）\n"
    "  • 取消订阅 — 关闭推送\n"
    "  • 状态 — 查看当前订阅状态\n"
    "  • 帮助 — 查看此说明\n\n"
    "由 HH Research 团队维护。建议关注本 bot 不要免打扰，以免错过日报。"
)


# ---------- Subprocess helpers (lark-cli wrappers) ----------


def _run_lark_cli(args: list[str], *, profile: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run lark-cli with the given profile. Returns (rc, stdout, stderr)."""
    env = {**os.environ, "LARK_CLI_NO_PROXY": "1"}
    proc = subprocess.run(
        ["lark-cli", "--profile", profile, *args],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ---------- Bitable: find / upsert subscriber ----------


def find_subscriber(open_id: str) -> dict | None:
    """Look up a row by open_id. Returns {record_id, status, ...} or None.

    Subscribers table is small (< 200 rows); we list all and match locally.
    """
    rc, stdout, stderr = _run_lark_cli([
        "base", "+record-list",
        "--as", "user",
        "--base-token", SUBSCRIBERS_BASE_TOKEN,
        "--table-id", SUBSCRIBERS_TABLE_ID,
        "--limit", "200",
        "--format", "json",
    ], profile=LARK_CLI_PROFILE_BITABLE)
    if rc != 0:
        log(f"find_subscriber: list rc={rc}, stderr={stderr[:200]}")
        return None
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        log(f"find_subscriber: JSON decode error: {e}; stdout head: {stdout[:200]}")
        return None
    rows = data.get("data", {}).get("data", [])
    record_ids = data.get("data", {}).get("record_id_list", [])
    fields = data.get("data", {}).get("fields", [])
    if len(rows) != len(record_ids):
        log(f"find_subscriber: rows/record_ids length mismatch: {len(rows)}/{len(record_ids)}")
        return None
    try:
        open_id_idx = fields.index("open_id")
        status_idx = fields.index("status")
    except ValueError:
        log(f"find_subscriber: missing required fields; got {fields}")
        return None
    for i, row in enumerate(rows):
        if row[open_id_idx] == open_id:
            raw_status = row[status_idx] if status_idx < len(row) else None
            status = _coerce_status(raw_status)
            return {"record_id": record_ids[i], "open_id": open_id, "status": status}
    return None


def _coerce_status(v) -> str | None:
    """Normalize select cell to plain string."""
    if v is None:
        return None
    if isinstance(v, list):
        if not v:
            return None
        first = v[0]
        if isinstance(first, dict):
            return first.get("name")
        return str(first)
    if isinstance(v, dict):
        return v.get("name")
    return str(v)


def upsert_subscriber(open_id: str, target_status: str, *, name: str | None = None) -> bool:
    """Upsert subscriber: update if exists (status only), else insert new row.

    target_status: 'active' or 'unsubscribed'.
    """
    existing = find_subscriber(open_id)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if existing and existing.get("record_id"):
        # Update: only flip status. subscribed_at stays; updated_at is auto.
        payload = {"status": target_status}
        rc, stdout, stderr = _run_lark_cli([
            "base", "+record-upsert",
            "--as", "user",
            "--base-token", SUBSCRIBERS_BASE_TOKEN,
            "--table-id", SUBSCRIBERS_TABLE_ID,
            "--record-id", existing["record_id"],
            "--json", json.dumps(payload, ensure_ascii=False),
        ], profile=LARK_CLI_PROFILE_BITABLE)
        if rc != 0:
            log(f"upsert_subscriber update rc={rc}, stderr={stderr[:200]}")
        return rc == 0

    # Insert new
    payload = {
        "open_id": open_id,
        "status": target_status,
        "subscribed_at": now_str,
        "note": f"自助订阅 by listener ({now_str})",
    }
    if name:
        payload["name"] = name
    rc, stdout, stderr = _run_lark_cli([
        "base", "+record-upsert",
        "--as", "user",
        "--base-token", SUBSCRIBERS_BASE_TOKEN,
        "--table-id", SUBSCRIBERS_TABLE_ID,
        "--json", json.dumps(payload, ensure_ascii=False),
    ], profile=LARK_CLI_PROFILE_BITABLE)
    if rc != 0:
        log(f"upsert_subscriber insert rc={rc}, stderr={stderr[:200]}")
    return rc == 0


# ---------- IM reply ----------


def reply_to_user(open_id: str, text: str) -> bool:
    """Send a text IM to the user as the HRes' aha moment bot."""
    rc, stdout, stderr = _run_lark_cli([
        "im", "+messages-send",
        "--user-id", open_id,
        "--text", text,
    ], profile=LARK_CLI_PROFILE_IM_BOT, timeout=15)
    if rc != 0:
        log(f"reply_to_user rc={rc}, stderr={stderr[:200]}")
    return rc == 0


# ---------- Intent matching ----------


def match_intent(text: str) -> str:
    """Match user message to intent. Returns: subscribe / unsubscribe / status / help / unknown"""
    t = (text or "").strip()
    if not t:
        return "help"
    t_lower = t.lower()
    for pat in SUBSCRIBE_PATTERNS:
        if re.fullmatch(pat, t_lower, re.IGNORECASE):
            return "subscribe"
    for pat in UNSUBSCRIBE_PATTERNS:
        if re.fullmatch(pat, t_lower, re.IGNORECASE):
            return "unsubscribe"
    for pat in STATUS_PATTERNS:
        if re.fullmatch(pat, t_lower, re.IGNORECASE):
            return "status"
    for pat in HELP_PATTERNS:
        if re.fullmatch(pat, t_lower, re.IGNORECASE):
            return "help"
    return "unknown"


# ---------- Event handler ----------


def handle_event(event: dict) -> None:
    """Process one IM event."""
    # Filter: only p2p text messages
    chat_type = event.get("chat_type")
    msg_type = event.get("message_type")
    if chat_type != "p2p":
        return
    if msg_type != "text":
        # For non-text private messages, send help once
        sender = event.get("sender_id")
        if sender:
            log(f"non-text p2p msg from {sender} (type={msg_type}) — sending help")
            reply_to_user(sender, HELP_TEXT)
        return

    open_id = event.get("sender_id")
    text = event.get("content", "") or ""
    if not open_id:
        log("skip: no sender_id")
        return

    intent = match_intent(text)
    log(f"{open_id} → intent={intent} text={text[:60]!r}")

    if intent == "subscribe":
        ok = upsert_subscriber(open_id, "active")
        reply = (
            "✅ 已订阅 HH Research Daily 主线（每日 BJT 12:00 推送）\n"
            "发送 取消订阅 可退订。"
            if ok
            else "❌ 订阅失败，请稍后重试或联系管理员。"
        )
    elif intent == "unsubscribe":
        ok = upsert_subscriber(open_id, "unsubscribed")
        reply = (
            "✅ 已取消订阅。如需重新开启，发送 订阅 即可。"
            if ok
            else "❌ 取消订阅失败，请稍后重试。"
        )
    elif intent == "status":
        sub = find_subscriber(open_id)
        if sub is None:
            reply = "您尚未订阅。发送 订阅 开启每日日报推送。"
        else:
            cur = sub.get("status") or "(未知)"
            if cur == "active":
                reply = "✅ 您当前已订阅。每日 BJT 12:00 收到 HH Research Daily 主线。"
            elif cur == "unsubscribed":
                reply = "您当前已退订。发送 订阅 可重新开启。"
            else:
                reply = f"您当前状态：{cur}"
    elif intent == "help":
        reply = HELP_TEXT
    else:  # unknown
        reply = HELP_TEXT  # fall back to help so user always gets something

    reply_to_user(open_id, reply)


# ---------- Logging ----------


def log(msg: str) -> None:
    """Log to stderr with timestamp prefix."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [listener] {msg}", file=sys.stderr, flush=True)


# ---------- Main loop ----------


def main() -> int:
    log("subscribe_listener started, reading NDJSON from stdin")
    n_processed = 0
    n_errors = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as e:
            n_errors += 1
            log(f"JSON decode error: {e}; line: {line[:200]}")
            continue
        try:
            handle_event(event)
            n_processed += 1
        except Exception as e:  # noqa: BLE001
            n_errors += 1
            log(f"handler exception: {e}")
    log(f"stdin closed; processed={n_processed} errors={n_errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
