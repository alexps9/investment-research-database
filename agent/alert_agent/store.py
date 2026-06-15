"""SQLite store for deduplication and audit trail."""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

from skills.signal_triage import tokens as _tokens, same_event as _same_event, TIER_RANK as _TIER_RANK

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert.db")


class Store:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_alerts (
                id INTEGER PRIMARY KEY,
                tweet_id TEXT UNIQUE,
                username TEXT,
                event_type TEXT,
                priority TEXT,
                message TEXT,
                summary TEXT,
                sent_at TIMESTAMP
            )
        """)
        # Add tier column if missing (existing DBs won't have it)
        try:
            self.conn.execute("ALTER TABLE sent_alerts ADD COLUMN tier TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def is_sent(self, tweet_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sent_alerts WHERE tweet_id = ?", (tweet_id,)
        ).fetchone()
        return row is not None

    def find_duplicate_event(self, summary: str, hours: int = 12) -> dict | None:
        """Find a previously pushed event that matches this summary.

        Returns {"summary": str, "username": str, "tier": str} of the prior push,
        or None if no duplicate found.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        # 只和「真正送达过用户」的记录比对去重：message 非空 = 已推送 / 进 pending 待审。
        # 被 skip / 被判重的记录 message 为空，是「幽灵记录」——若把它们也当判重基准，
        # 会出现：某事件第一次就被误判重(从没发出) → 后续每条同事件都和这条幽灵互毙 →
        # 事件永远发不出去（2026-06-12 贝索斯 Prometheus 漏报即此 bug）。
        rows = self.conn.execute(
            "SELECT summary, username, event_type, tier FROM sent_alerts "
            "WHERE sent_at > ? AND summary IS NOT NULL AND summary != '' "
            "AND message IS NOT NULL AND message != ''",
            (cutoff,)
        ).fetchall()
        new_toks = _tokens(summary)
        if not new_toks:
            return None
        best = None
        best_rank = -1
        for prev_summary, prev_user, prev_etype, prev_tier in rows:
            prev_toks = _tokens(prev_summary)
            if not prev_toks:
                continue
            # Deterministic event-match (the optional LLM escalation that the
            # original alert pipeline used now lives in the alert_agent layer).
            if _same_event(new_toks, prev_toks, 0.20):
                rank = _TIER_RANK.get(prev_tier or "", 0)
                if rank > best_rank:
                    best_rank = rank
                    best = {"summary": prev_summary, "username": prev_user,
                            "event_type": prev_etype, "tier": prev_tier or ""}
        return best

    def is_duplicate_event(self, summary: str, hours: int = 12) -> bool:
        """Check if a similar event was already pushed recently."""
        return self.find_duplicate_event(summary, hours) is not None

    def mark_sent(self, tweet_id: str, username: str, event_type: str, priority: str, message: str, summary: str = "", tier: str = ""):
        self.conn.execute(
            "INSERT OR IGNORE INTO sent_alerts (tweet_id, username, event_type, priority, message, summary, tier, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tweet_id, username, event_type, priority, message, summary, tier, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
