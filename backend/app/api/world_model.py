"""
World Model CRUD API routes.

Provides endpoints for managing lanes, rows, papers, and connections
backed by a SQLite database.
"""

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.db import get_connection
from app.models.evolution import (
    ConnectionCreate,
    EvolutionPaper,
    LaneDef,
    PaperCreate,
    PaperUpdate,
    RowDef,
    WorldModelResponse,
)

router = APIRouter(prefix="/api/world-model", tags=["World Model"])
logger = logging.getLogger(__name__)


def _row_to_paper_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a sqlite3.Row from the papers table to a dictionary."""
    d = dict(row)
    # Parse authors from JSON string
    if d.get("authors"):
        try:
            d["authors"] = json.loads(d["authors"])
        except (json.JSONDecodeError, TypeError):
            d["authors"] = []
    else:
        d["authors"] = []
    return d


def _get_connections_for_paper(conn: sqlite3.Connection, paper_id: str) -> List[Dict[str, str]]:
    """Fetch connections where paper is the source."""
    cursor = conn.execute(
        "SELECT target_id, type FROM connections WHERE source_id = ?",
        (paper_id,),
    )
    return [{"target": row["target_id"], "type": row["type"]} for row in cursor.fetchall()]


def _build_paper_response(conn: sqlite3.Connection, row: sqlite3.Row) -> Dict[str, Any]:
    """Build a full paper response dict with connections."""
    paper_dict = _row_to_paper_dict(row)
    paper_dict["connections"] = _get_connections_for_paper(conn, paper_dict["id"])
    # Add default fields expected by the model
    paper_dict.setdefault("builds_on", [])
    paper_dict.setdefault("size", "md")
    paper_dict.setdefault("is_rising", False)
    paper_dict.setdefault("is_weak_signal", False)
    return paper_dict


# ─── GET /api/world-model ─────────────────────────────────────────


@router.get(
    "",
    response_model=WorldModelResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full world model data",
    description="Returns all lanes, rows, and papers with connections. "
    "Designed to be a drop-in replacement for the static JSON import.",
)
async def get_world_model() -> WorldModelResponse:
    """
    Retrieve the complete world model data structure.

    Returns:
        WorldModelResponse with lanes, rows, and papers (including connections)

    Raises:
        HTTPException 500: Database read error
    """
    conn = get_connection()
    try:
        # Fetch lanes
        lanes_cursor = conn.execute("SELECT id, title, subtitle, color FROM lanes")
        lanes = [dict(row) for row in lanes_cursor.fetchall()]

        # Fetch rows
        rows_cursor = conn.execute("SELECT id, lane, title, subtitle FROM rows")
        rows = [dict(row) for row in rows_cursor.fetchall()]

        # Fetch papers with connections
        papers_cursor = conn.execute("SELECT * FROM papers")
        papers = []
        for row in papers_cursor.fetchall():
            papers.append(_build_paper_response(conn, row))

        return WorldModelResponse(lanes=lanes, rows=rows, papers=papers)

    except sqlite3.Error as e:
        logger.error(f"Database error in get_world_model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── GET /api/world-model/papers ──────────────────────────────────


@router.get(
    "/papers",
    status_code=status.HTTP_200_OK,
    summary="List papers with optional filters",
)
async def list_papers(
    lane: Optional[str] = Query(None, description="Filter by lane ID"),
    row: Optional[str] = Query(None, description="Filter by row ID"),
) -> List[Dict[str, Any]]:
    """
    List all papers, optionally filtered by lane and/or row.

    Args:
        lane: Filter papers belonging to this lane
        row: Filter papers belonging to this row

    Returns:
        List of paper dicts with connections

    Raises:
        HTTPException 500: Database read error
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM papers WHERE 1=1"
        params: List[str] = []

        if lane:
            query += " AND lane = ?"
            params.append(lane)
        if row:
            query += " AND row = ?"
            params.append(row)

        cursor = conn.execute(query, params)
        papers = []
        for paper_row in cursor.fetchall():
            papers.append(_build_paper_response(conn, paper_row))

        return papers

    except sqlite3.Error as e:
        logger.error(f"Database error in list_papers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── GET /api/world-model/papers/{id} ─────────────────────────────


@router.get(
    "/papers/{paper_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single paper by ID",
)
async def get_paper(paper_id: str) -> Dict[str, Any]:
    """
    Retrieve a single paper with its connections.

    Args:
        paper_id: The paper's unique identifier

    Returns:
        Paper dict with connections

    Raises:
        HTTPException 404: Paper not found
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper '{paper_id}' not found.",
            )

        return _build_paper_response(conn, row)

    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in get_paper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── POST /api/world-model/papers ─────────────────────────────────


@router.post(
    "/papers",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new paper",
)
async def create_paper(paper: PaperCreate) -> Dict[str, Any]:
    """
    Create a new paper in the database.

    Args:
        paper: Paper data (id must be unique)

    Returns:
        The created paper dict

    Raises:
        HTTPException 409: Paper with this ID already exists
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        # Check if paper already exists
        existing = conn.execute("SELECT id FROM papers WHERE id = ?", (paper.id,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Paper '{paper.id}' already exists.",
            )

        # Serialize authors to JSON
        authors_json = json.dumps(paper.authors) if paper.authors else None

        conn.execute(
            """INSERT INTO papers (id, title, full_title, year, quarter, lane, row, path,
               paradigm, layer, shape, org, authors, arxiv_id, doi,
               cited_by_count, venue_tier, institution_tier, impact_score, impact_override)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                paper.id,
                paper.title,
                paper.full_title,
                paper.year,
                paper.quarter,
                paper.lane,
                paper.row,
                paper.path,
                paper.paradigm,
                paper.layer,
                paper.shape,
                paper.org,
                authors_json,
                paper.arxiv_id,
                paper.doi,
                paper.cited_by_count,
                paper.venue_tier,
                paper.institution_tier,
                paper.impact_score,
                paper.impact_override,
            ),
        )
        conn.commit()

        # Fetch and return the created paper
        cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (paper.id,))
        row = cursor.fetchone()
        return _build_paper_response(conn, row)

    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Integrity error: {e}",
        )
    except sqlite3.Error as e:
        logger.error(f"Database error in create_paper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── PUT /api/world-model/papers/{id} ─────────────────────────────


@router.put(
    "/papers/{paper_id}",
    status_code=status.HTTP_200_OK,
    summary="Update an existing paper",
)
async def update_paper(paper_id: str, updates: PaperUpdate) -> Dict[str, Any]:
    """
    Update fields of an existing paper. Only provided fields are updated.

    Args:
        paper_id: The paper's unique identifier
        updates: Fields to update (only non-None fields are applied)

    Returns:
        The updated paper dict

    Raises:
        HTTPException 404: Paper not found
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        # Check paper exists
        existing = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper '{paper_id}' not found.",
            )

        # Build SET clause from non-None fields
        update_data = updates.model_dump(exclude_none=True)
        if not update_data:
            # Nothing to update, just return current state
            cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            return _build_paper_response(conn, cursor.fetchone())

        # Serialize authors if present
        if "authors" in update_data:
            update_data["authors"] = json.dumps(update_data["authors"])

        set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values()) + [paper_id]

        conn.execute(f"UPDATE papers SET {set_clause} WHERE id = ?", values)
        conn.commit()

        # Fetch and return the updated paper
        cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
        return _build_paper_response(conn, cursor.fetchone())

    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in update_paper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── DELETE /api/world-model/papers/{id} ───────────────────────────


@router.delete(
    "/papers/{paper_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a paper",
)
async def delete_paper(paper_id: str) -> Dict[str, str]:
    """
    Delete a paper and all its associated connections.

    Args:
        paper_id: The paper's unique identifier

    Returns:
        Confirmation message

    Raises:
        HTTPException 404: Paper not found
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        # Check paper exists
        existing = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper '{paper_id}' not found.",
            )

        # Delete connections where this paper is source or target
        conn.execute(
            "DELETE FROM connections WHERE source_id = ? OR target_id = ?", (paper_id, paper_id)
        )
        # Delete the paper
        conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        conn.commit()

        return {"message": f"Paper '{paper_id}' deleted."}

    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_paper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── POST /api/world-model/connections ─────────────────────────────


@router.post(
    "/connections",
    status_code=status.HTTP_201_CREATED,
    summary="Add a connection between papers",
)
async def create_connection(connection: ConnectionCreate) -> Dict[str, str]:
    """
    Create a new connection between two papers.

    Args:
        connection: Connection data (source_id, target_id, type)

    Returns:
        The created connection data

    Raises:
        HTTPException 404: Source or target paper not found
        HTTPException 409: Connection already exists
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        # Verify both papers exist
        source = conn.execute(
            "SELECT id FROM papers WHERE id = ?", (connection.source_id,)
        ).fetchone()
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source paper '{connection.source_id}' not found.",
            )

        target = conn.execute(
            "SELECT id FROM papers WHERE id = ?", (connection.target_id,)
        ).fetchone()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target paper '{connection.target_id}' not found.",
            )

        # Check for duplicate
        existing = conn.execute(
            "SELECT 1 FROM connections WHERE source_id = ? AND target_id = ? AND type = ?",
            (connection.source_id, connection.target_id, connection.type),
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Connection ({connection.source_id} -> {connection.target_id}, type={connection.type}) already exists.",
            )

        conn.execute(
            "INSERT INTO connections (source_id, target_id, type) VALUES (?, ?, ?)",
            (connection.source_id, connection.target_id, connection.type),
        )
        conn.commit()

        return {
            "source_id": connection.source_id,
            "target_id": connection.target_id,
            "type": connection.type,
        }

    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Connection already exists: {e}",
        )
    except sqlite3.Error as e:
        logger.error(f"Database error in create_connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()


# ─── DELETE /api/world-model/connections ───────────────────────────


@router.delete(
    "/connections",
    status_code=status.HTTP_200_OK,
    summary="Remove a connection between papers",
)
async def delete_connection(connection: ConnectionCreate) -> Dict[str, str]:
    """
    Remove an existing connection between two papers.

    Args:
        connection: Connection to remove (source_id, target_id, type)

    Returns:
        Confirmation message

    Raises:
        HTTPException 404: Connection not found
        HTTPException 500: Database error
    """
    conn = get_connection()
    try:
        # Check connection exists
        existing = conn.execute(
            "SELECT 1 FROM connections WHERE source_id = ? AND target_id = ? AND type = ?",
            (connection.source_id, connection.target_id, connection.type),
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection ({connection.source_id} -> {connection.target_id}, type={connection.type}) not found.",
            )

        conn.execute(
            "DELETE FROM connections WHERE source_id = ? AND target_id = ? AND type = ?",
            (connection.source_id, connection.target_id, connection.type),
        )
        conn.commit()

        return {"message": "Connection deleted."}

    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    finally:
        conn.close()
