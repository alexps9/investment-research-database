"""SQLite store for deduplication and audit trail."""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

from score import _tokens, _same_event, _maybe_same_event, llm_same_event, _STRONG_ENTITIES

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert.db")


_TIER_RANK = {"tier_1a": 5, "tier_1b": 4, "tier_2": 3, "tier_3": 2}


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
            matched = False
            if _same_event(new_toks, prev_toks, 0.20):
                matched = True
            elif _maybe_same_event(new_toks, prev_toks):
                if llm_same_event(summary, prev_summary):
                    matched = True
            if matched:
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
