"""
Migration script: world-model-data.json -> SQLite database.

Reads the frontend JSON data file and populates the SQLite database.
Idempotent: uses INSERT OR REPLACE so it can be run multiple times safely.

Usage:
    cd backend
    python scripts/migrate_json_to_sqlite.py
"""

import json
import sqlite3
import sys
from pathlib import Path

# Add backend to path so we can import app modules
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.db import get_db_path, init_db

# Path to the source JSON
JSON_PATH = BACKEND_DIR.parent / "frontend" / "src" / "data" / "world-model-data.json"


def load_json() -> dict:
    """Load and parse the world-model-data.json file."""
    if not JSON_PATH.exists():
        print(f"ERROR: JSON file not found at {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(
        f"Loaded JSON: {len(data['lanes'])} lanes, {len(data['rows'])} rows, {len(data['papers'])} papers"
    )
    return data


def migrate_lanes(conn: sqlite3.Connection, lanes: list) -> None:
    """Insert lanes into the database."""
    for lane in lanes:
        conn.execute(
            "INSERT OR REPLACE INTO lanes (id, title, subtitle, color) VALUES (?, ?, ?, ?)",
            (lane["id"], lane["title"], lane["subtitle"], lane["color"]),
        )
    print(f"  Migrated {len(lanes)} lanes")


def migrate_rows(conn: sqlite3.Connection, rows: list) -> None:
    """Insert rows into the database."""
    for row in rows:
        conn.execute(
            "INSERT OR REPLACE INTO rows (id, lane, title, subtitle) VALUES (?, ?, ?, ?)",
            (row["id"], row["lane"], row["title"], row["subtitle"]),
        )
    print(f"  Migrated {len(rows)} rows")


def migrate_papers(conn: sqlite3.Connection, papers: list) -> int:
    """
    Insert papers into the database.

    Returns:
        Number of connections inserted
    """
    connection_count = 0

    for paper in papers:
        # Serialize authors if present
        authors = paper.get("authors")
        authors_json = json.dumps(authors) if authors else None

        conn.execute(
            """INSERT OR REPLACE INTO papers
            (id, title, full_title, year, quarter, lane, row, path,
             paradigm, layer, shape, org, authors, arxiv_id, doi,
             cited_by_count, venue_tier, institution_tier, impact_score, impact_override)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                paper["id"],
                paper["title"],
                paper.get("full_title"),
                paper["year"],
                paper["quarter"],
                paper["lane"],
                paper["row"],
                paper.get("path", "trunk"),
                paper.get("paradigm"),
                paper.get("layer", "arch"),
                paper.get("shape", "circle"),
                paper.get("org"),
                authors_json,
                paper.get("arxiv_id"),
                paper.get("doi"),
                paper.get("cited_by_count", 0),
                paper.get("venue_tier"),
                paper.get("institution_tier"),
                paper.get("impact_score"),
                paper.get("impact_override"),
            ),
        )

    print(f"  Migrated {len(papers)} papers")

    # Now handle connections
    # First: explicit connections array
    for paper in papers:
        for conn_data in paper.get("connections", []):
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO connections (source_id, target_id, type) VALUES (?, ?, ?)",
                    (paper["id"], conn_data["target"], conn_data["type"]),
                )
                connection_count += 1
            except sqlite3.IntegrityError:
                # Skip if target paper doesn't exist yet (foreign key)
                pass

    # Second: builds_on array -> connections with type='inherits'
    # Skip if already inserted from explicit connections
    for paper in papers:
        for target_id in paper.get("builds_on", []):
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO connections (source_id, target_id, type) VALUES (?, ?, ?)",
                    (paper["id"], target_id, "inherits"),
                )
                connection_count += 1
            except sqlite3.IntegrityError:
                pass

    print(f"  Migrated {connection_count} connections (from connections[] + builds_on[])")
    return connection_count


def main() -> None:
    """Run the migration."""
    print("=" * 60)
    print("World Model JSON -> SQLite Migration")
    print("=" * 60)

    # Initialize database schema
    print(f"\nDatabase path: {get_db_path()}")
    init_db()
    print("Schema initialized.")

    # Load JSON data
    print(f"\nReading: {JSON_PATH}")
    data = load_json()

    # Connect and migrate
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = OFF")  # Disable during bulk insert for speed
    try:
        print("\nMigrating...")
        migrate_lanes(conn, data["lanes"])
        migrate_rows(conn, data["rows"])
        migrate_papers(conn, data["papers"])
        conn.commit()
        print("\nMigration complete!")

        # Verify counts
        lane_count = conn.execute("SELECT COUNT(*) FROM lanes").fetchone()[0]
        row_count = conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0]
        paper_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        conn_count = conn.execute("SELECT COUNT(*) FROM connections").fetchone()[0]
        print(f"\nDatabase contents:")
        print(f"  lanes: {lane_count}")
        print(f"  rows: {row_count}")
        print(f"  papers: {paper_count}")
        print(f"  connections: {conn_count}")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: Migration failed: {e}")
        raise
    finally:
        conn.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
