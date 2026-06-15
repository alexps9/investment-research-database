"""Send success notification via email (QQ + Gmail).

Triggered by:
    - broadcast_today.sh at 09:30 after successful enterprise group broadcast

Channels:
    - Email (SMTP) — uses SMTP env vars same as notify_failure.py

Env vars (required):
    SMTP_HOST       e.g. smtp.gmail.com
    SMTP_PORT       e.g. 587
    SMTP_USER       sender address (also used as login)
    SMTP_PASSWORD   App Password (NOT your real Gmail password)
    SMTP_FROM       optional display sender, defaults to SMTP_USER
    NOTIFY_EMAILS   comma-separated list of recipients (includes QQ + Gmail)

Usage:
    python scripts/notify_success.py <date> <digest_url>

Example:
    python scripts/notify_success.py 2026-05-19 https://my.feishu.cn/docx/xxx
"""

from __future__ import annotations

import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def now_beijing() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def notify_email(date: str, digest_url: str) -> tuple[bool, str]:
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
        f"✅ HH Research Daily {date} 已成功发送至企业群\n"
        f"=========================================\n\n"
        f"时间 (北京): {now_beijing()}\n"
        f"完整日报: {digest_url}\n\n"
        f"--\n"
        f"This is an automated confirmation from your HH Research pipeline.\n"
    )

    msg = MIMEMultipart()
    msg["From"] = sender_from
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = f"[HH Research] Daily {date} broadcast 成功"
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
    if len(sys.argv) < 2:
        print("Usage: notify_success.py <date> [<digest_url>]", file=sys.stderr)
        return 2
    date = sys.argv[1]
    digest_url = sys.argv[2] if len(sys.argv) > 2 else ""
    ok, info = notify_email(date, digest_url)
    print(f"[notify_success] email: ok={ok} info={info}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
