"""Send failure notification via Feishu IM + email.

Triggered by:
    - health_check.sh at 00:30 if daily pipeline didn't start
    - run_daily_pipeline.sh if pipeline exits non-zero

Channels:
    1. Feishu IM (primary) — uses lark-cli `personal` profile, always works if logged in
    2. Email (secondary) — uses SMTP via env vars; silently skipped if not configured

Env vars for email (optional):
    SMTP_HOST       e.g. smtp.gmail.com
    SMTP_PORT       e.g. 587
    SMTP_USER       sender address (also used as login)
    SMTP_PASSWORD   App Password (NOT your real Gmail password)
    SMTP_FROM       optional display sender, defaults to SMTP_USER
    NOTIFY_EMAILS   comma-separated list of recipients

Env var for Feishu IM:
    NOTIFY_USER_OPEN_ID   defaults to ou_69c034f8f67053dca0cfaf9c6e9f3262

Usage:
    python scripts/notify_failure.py <reason_code> <human_message>

Example:
    python scripts/notify_failure.py pipeline_not_started \\
        "Pipeline 在 2026-05-14 00:00 没有启动，可能笔记本休眠 / launchd 没触发。"
"""

from __future__ import annotations

import os
import smtplib
import subprocess
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

# Load .env if available
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


DEFAULT_OPEN_ID = "ou_69c034f8f67053dca0cfaf9c6e9f3262"


def now_beijing() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def notify_feishu_im(reason: str, message: str) -> tuple[bool, str]:
    """Send IM to user via lark-cli personal profile."""
    open_id = os.environ.get("NOTIFY_USER_OPEN_ID", DEFAULT_OPEN_ID)
    text = (
        f"⚠️ HH Research Pipeline 异常\n\n"
        f"原因: {reason}\n"
        f"时间: {now_beijing()} (北京)\n\n"
        f"{message}"
    )
    env = {**os.environ, "LARK_CLI_NO_PROXY": "1"}
    try:
        r = subprocess.run(
            [
                "lark-cli",
                "--profile",
                "personal",
                "im",
                "+messages-send",
                "--user-id",
                open_id,
                "--text",
                text,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False,
        )
        if r.returncode == 0:
            return True, "ok"
        return False, f"rc={r.returncode} stderr={r.stderr[:200]}"
    except Exception as e:
        return False, f"exception: {e}"


def notify_email(reason: str, message: str) -> tuple[bool, str]:
    """Send email via SMTP. Returns (ok, info)."""
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT", "587")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    recipients = os.environ.get("NOTIFY_EMAILS", "")
    if not all([host, user, password, recipients]):
        return False, "SMTP env vars not fully configured (skipping email)"

    sender_from = os.environ.get("SMTP_FROM", user)
    to_list = [a.strip() for a in recipients.split(",") if a.strip()]

    body = (
        f"HH Research Pipeline 异常通知\n"
        f"=================================\n\n"
        f"原因 (reason_code): {reason}\n"
        f"时间 (北京): {now_beijing()}\n\n"
        f"详情:\n{message}\n\n"
        f"--\n"
        f"This is an automated alert from your laptop's HH Research pipeline.\n"
        f"If you didn't expect this, the daily pipeline may not have run.\n"
    )

    msg = MIMEMultipart()
    msg["From"] = sender_from
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = f"[HH Research] Pipeline alert: {reason}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, int(port), timeout=30) as s:
            s.starttls()
            s.login(user, password)
            s.sendmail(sender_from, to_list, msg.as_string())
        return True, f"sent to {len(to_list)} addrs"
    except Exception as e:
        return False, f"smtp error: {e}"


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: notify_failure.py <reason_code> <message>", file=sys.stderr
        )
        return 2
    reason = sys.argv[1]
    message = sys.argv[2]

    print(f"[notify] reason={reason}", file=sys.stderr)

    im_ok, im_info = notify_feishu_im(reason, message)
    print(f"[notify] feishu_im: {'OK' if im_ok else 'FAIL'} ({im_info})", file=sys.stderr)

    email_ok, email_info = notify_email(reason, message)
    print(
        f"[notify] email:     {'OK' if email_ok else 'SKIP/FAIL'} ({email_info})",
        file=sys.stderr,
    )

    # Exit 0 if at least one channel succeeded
    return 0 if (im_ok or email_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
