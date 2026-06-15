"""Time utilities — always use Asia/Shanghai as default local timezone."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def local_tz() -> ZoneInfo:
    return ZoneInfo(os.getenv("HH_TIMEZONE", "Asia/Shanghai"))


def now_local() -> datetime:
    return datetime.now(local_tz())


def today_local_start() -> datetime:
    """Midnight today in local timezone, tz-aware."""
    now = now_local()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def day_window(offset_days: int = 0) -> tuple[datetime, datetime]:
    """Return (start, end) datetimes for a local-day window. offset_days=0 = today, -1 = yesterday."""
    start = today_local_start() + timedelta(days=offset_days)
    end = start + timedelta(days=1)
    return start, end


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz())
    return dt.astimezone(timezone.utc)


def parse_arxiv_iso(s: str) -> datetime:
    """Parse arXiv's ISO timestamp to tz-aware datetime in UTC."""
    # arXiv returns e.g. '2026-04-24T08:00:00Z'
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
