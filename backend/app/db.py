"""
SQLite database module for world-model papers.

Provides connection management and schema initialization.
Database path configurable via WORLD_MODEL_DB_PATH env var.
"""

import os
import sqlite3
from pathlib import Path

# Default database path: backend/data/world_model.db
_DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "data" / "world_model.db")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS lanes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    color TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rows (
    id TEXT PRIMARY KEY,
    lane TEXT NOT NULL REFERENCES lanes(id),
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    full_title TEXT,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    lane TEXT NOT NULL REFERENCES lanes(id),
    row TEXT NOT NULL REFERENCES rows(id),
    path TEXT NOT NULL DEFAULT 'trunk',
    paradigm TEXT,
    layer TEXT DEFAULT 'arch',
    shape TEXT DEFAULT 'circle' CHECK (shape IN ('circle', 'square')),
    org TEXT,
    authors TEXT,
    arxiv_id TEXT,
    doi TEXT,
    cited_by_count INTEGER DEFAULT 0,
    venue_tier INTEGER,
    institution_tier INTEGER,
    impact_score REAL,
    impact_override REAL
);

CREATE TABLE IF NOT EXISTS connections (
    source_id TEXT NOT NULL REFERENCES papers(id),
    target_id TEXT NOT NULL REFERENCES papers(id),
    type TEXT NOT NULL CHECK (type IN ('inherits', 'competes', 'borrows')),
    PRIMARY KEY (source_id, target_id, type)
);
"""


def get_db_path() -> str:
    """Get database path from environment or use default."""
    return os.environ.get("WORLD_MODEL_DB_PATH", _DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    """
    Create and return a new SQLite connection.

    The connection has:
    - Row factory set to sqlite3.Row for dict-like access
    - Foreign keys enforcement enabled

    Returns:
        sqlite3.Connection configured for use

    Raises:
        sqlite3.OperationalError: If database file cannot be created/opened
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """
    Initialize the database schema.

    Creates the data directory if it doesn't exist, then creates all tables.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).

    Raises:
        sqlite3.OperationalError: If schema creation fails
        OSError: If data directory cannot be created
    """
    db_path = get_db_path()
    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
