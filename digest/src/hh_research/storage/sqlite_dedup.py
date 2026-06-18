"""SQLite-backed dedup store for source_ids we've already seen.

Keeps the pipeline idempotent across daily reruns without round-tripping to Bitable.
Designed as an interface (DedupStore) so the backing store can be swapped to
Postgres when we move to the cloud.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable, Protocol


class DedupStore(Protocol):
    def seen(self, source_id: str) -> bool: ...
    def mark_seen(self, source_id: str, note: str | None = None) -> None: ...
    def mark_many(self, source_ids: Iterable[str]) -> None: ...
    def count(self) -> int: ...


class SQLiteDedupStore:
    """Local SQLite implementation of DedupStore."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            data_dir = Path(os.getenv("HH_DATA_DIR", "./data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "dedup.sqlite"
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen (
                source_id TEXT PRIMARY KEY,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                note TEXT
            )
            """
        )
        self._conn.commit()

    def seen(self, source_id: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM seen WHERE source_id = ? LIMIT 1", (source_id,))
        return cur.fetchone() is not None

    def mark_seen(self, source_id: str, note: str | None = None) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen(source_id, note) VALUES (?, ?)",
            (source_id, note),
        )
        self._conn.commit()

    def mark_many(self, source_ids: Iterable[str]) -> None:
        rows = [(sid, None) for sid in source_ids]
        if not rows:
            return
        self._conn.executemany(
            "INSERT OR IGNORE INTO seen(source_id, note) VALUES (?, ?)", rows
        )
        self._conn.commit()

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM seen")
        return int(cur.fetchone()[0])

    def filter_unseen(self, source_ids: Iterable[str]) -> list[str]:
        """Return those source_ids that are NOT yet in the seen set."""
        ids = list(source_ids)
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        cur = self._conn.execute(
            f"SELECT source_id FROM seen WHERE source_id IN ({placeholders})", ids
        )
        seen = {row[0] for row in cur.fetchall()}
        return [sid for sid in ids if sid not in seen]

    def close(self) -> None:
        self._conn.close()
