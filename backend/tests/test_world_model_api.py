"""
Tests for World Model CRUD API endpoints.
TDD Red Phase — these tests define the contract for the SQLite-backed world model API.
"""

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client with a temporary database."""
    db_path = str(tmp_path / "test_world_model.db")
    monkeypatch.setenv("WORLD_MODEL_DB_PATH", db_path)

    # Force reimport to pick up new env var
    import importlib

    import app.db as db_module

    importlib.reload(db_module)
    db_module.init_db()

    from app.main import app

    return TestClient(app)


@pytest.fixture
def seeded_client(client):
    """Client with some seed data pre-inserted."""
    import app.db as db_module

    conn = db_module.get_connection()
    try:
        conn.execute(
            "INSERT INTO lanes (id, title, subtitle, color) VALUES (?, ?, ?, ?)",
            ("rl_based", "RL-Based", "在想象中训练", "#059669"),
        )
        conn.execute(
            "INSERT INTO lanes (id, title, subtitle, color) VALUES (?, ?, ?, ?)",
            ("video_gen", "Video-Generative", "从观看中学习", "#2563EB"),
        )
        conn.execute(
            "INSERT INTO rows (id, lane, title, subtitle) VALUES (?, ?, ?, ?)",
            ("rssm_based", "rl_based", "RSSM-based", "PlaNet / Dreamer V1-V3"),
        )
        conn.execute(
            "INSERT INTO rows (id, lane, title, subtitle) VALUES (?, ?, ?, ?)",
            ("diffusion_video", "video_gen", "Diffusion-based", "Sora / Cosmos"),
        )
        conn.execute(
            """INSERT INTO papers (id, title, year, quarter, lane, row, path, paradigm, layer, shape, org, cited_by_count, impact_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "planet",
                "PlaNet",
                2019,
                2,
                "rl_based",
                "rssm_based",
                "trunk",
                "rssm",
                "arch",
                "circle",
                "Google",
                1200,
                91.1,
            ),
        )
        conn.execute(
            """INSERT INTO papers (id, title, year, quarter, lane, row, path, paradigm, layer, shape, org, cited_by_count, impact_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "dreamer_v1",
                "Dreamer V1",
                2020,
                1,
                "rl_based",
                "rssm_based",
                "trunk",
                "imagination_rl",
                "arch",
                "circle",
                "Google/Danijar",
                900,
                89.4,
            ),
        )
        conn.execute(
            "INSERT INTO connections (source_id, target_id, type) VALUES (?, ?, ?)",
            ("dreamer_v1", "planet", "inherits"),
        )
        conn.commit()
    finally:
        conn.close()
    return client


# ─── GET /api/world-model ───────────────────────────────────────────


class TestGetWorldModel:
    """Tests for GET /api/world-model — full data retrieval."""

    def test_returns_200_with_empty_db(self, client):
        """Empty database returns valid structure with empty arrays."""
        response = client.get("/api/world-model")
        assert response.status_code == 200
        data = response.json()
        assert "lanes" in data
        assert "rows" in data
        assert "papers" in data
        assert data["lanes"] == []
        assert data["rows"] == []
        assert data["papers"] == []

    def test_returns_full_data_structure(self, seeded_client):
        """Returns lanes, rows, and papers with connections."""
        response = seeded_client.get("/api/world-model")
        assert response.status_code == 200
        data = response.json()

        assert len(data["lanes"]) == 2
        assert len(data["rows"]) == 2
        assert len(data["papers"]) == 2

        # Verify lane structure
        rl_lane = next(l for l in data["lanes"] if l["id"] == "rl_based")
        assert rl_lane["title"] == "RL-Based"
        assert rl_lane["color"] == "#059669"

        # Verify paper has connections embedded
        dreamer = next(p for p in data["papers"] if p["id"] == "dreamer_v1")
        assert dreamer["connections"] == [{"target": "planet", "type": "inherits"}]

        # Paper without connections has empty list
        planet = next(p for p in data["papers"] if p["id"] == "planet")
        assert planet["connections"] == []


# ─── GET /api/world-model/papers ───────────────────────────────────


class TestListPapers:
    """Tests for GET /api/world-model/papers — list with filters."""

    def test_list_all_papers(self, seeded_client):
        """List all papers without filters."""
        response = seeded_client.get("/api/world-model/papers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_by_lane(self, seeded_client):
        """Filter papers by lane."""
        response = seeded_client.get("/api/world-model/papers?lane=rl_based")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["lane"] == "rl_based" for p in data)

    def test_filter_by_row(self, seeded_client):
        """Filter papers by row."""
        response = seeded_client.get("/api/world-model/papers?row=rssm_based")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_by_nonexistent_lane_returns_empty(self, seeded_client):
        """Filtering by a lane with no papers returns empty list."""
        response = seeded_client.get("/api/world-model/papers?lane=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data == []


# ─── GET /api/world-model/papers/{id} ─────────────────────────────


class TestGetPaper:
    """Tests for GET /api/world-model/papers/{id} — single paper."""

    def test_get_existing_paper(self, seeded_client):
        """Get a paper by ID returns full data with connections."""
        response = seeded_client.get("/api/world-model/papers/dreamer_v1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dreamer_v1"
        assert data["title"] == "Dreamer V1"
        assert data["year"] == 2020
        assert data["connections"] == [{"target": "planet", "type": "inherits"}]

    def test_get_nonexistent_paper_returns_404(self, seeded_client):
        """Requesting a non-existent paper returns 404."""
        response = seeded_client.get("/api/world-model/papers/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ─── POST /api/world-model/papers ──────────────────────────────────


class TestCreatePaper:
    """Tests for POST /api/world-model/papers — create paper."""

    def test_create_paper_success(self, seeded_client):
        """Create a new paper with valid data."""
        payload = {
            "id": "dreamer_v2",
            "title": "Dreamer V2",
            "year": 2021,
            "quarter": 1,
            "lane": "rl_based",
            "row": "rssm_based",
            "path": "trunk",
            "paradigm": "imagination_rl",
            "layer": "arch",
            "shape": "circle",
            "org": "Google/Danijar",
            "cited_by_count": 700,
            "impact_score": 87.8,
        }
        response = seeded_client.post("/api/world-model/papers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "dreamer_v2"
        assert data["title"] == "Dreamer V2"

    def test_create_paper_duplicate_id_returns_409(self, seeded_client):
        """Creating a paper with existing ID returns conflict."""
        payload = {
            "id": "planet",
            "title": "PlaNet Duplicate",
            "year": 2019,
            "quarter": 2,
            "lane": "rl_based",
            "row": "rssm_based",
            "path": "trunk",
        }
        response = seeded_client.post("/api/world-model/papers", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_paper_missing_required_field_returns_422(self, seeded_client):
        """Missing required field returns validation error."""
        payload = {
            "id": "incomplete",
            "title": "Incomplete Paper",
            # Missing year, quarter, lane, row, path
        }
        response = seeded_client.post("/api/world-model/papers", json=payload)
        assert response.status_code == 422

    def test_create_paper_invalid_quarter_returns_422(self, seeded_client):
        """Quarter must be between 1 and 4."""
        payload = {
            "id": "bad_quarter",
            "title": "Bad Quarter",
            "year": 2021,
            "quarter": 5,
            "lane": "rl_based",
            "row": "rssm_based",
            "path": "trunk",
        }
        response = seeded_client.post("/api/world-model/papers", json=payload)
        assert response.status_code == 422


# ─── PUT /api/world-model/papers/{id} ─────────────────────────────


class TestUpdatePaper:
    """Tests for PUT /api/world-model/papers/{id} — update paper."""

    def test_update_paper_success(self, seeded_client):
        """Update an existing paper's fields."""
        payload = {
            "title": "PlaNet (updated)",
            "cited_by_count": 1500,
            "impact_score": 92.0,
        }
        response = seeded_client.put("/api/world-model/papers/planet", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "PlaNet (updated)"
        assert data["cited_by_count"] == 1500
        assert data["impact_score"] == 92.0
        # Unchanged fields remain
        assert data["year"] == 2019
        assert data["lane"] == "rl_based"

    def test_update_nonexistent_paper_returns_404(self, seeded_client):
        """Updating a non-existent paper returns 404."""
        payload = {"title": "Ghost Paper"}
        response = seeded_client.put("/api/world-model/papers/nonexistent", json=payload)
        assert response.status_code == 404


# ─── DELETE /api/world-model/papers/{id} ───────────────────────────


class TestDeletePaper:
    """Tests for DELETE /api/world-model/papers/{id} — delete paper."""

    def test_delete_paper_success(self, seeded_client):
        """Delete an existing paper."""
        response = seeded_client.delete("/api/world-model/papers/planet")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        response = seeded_client.get("/api/world-model/papers/planet")
        assert response.status_code == 404

    def test_delete_paper_removes_connections(self, seeded_client):
        """Deleting a paper also removes its connections."""
        seeded_client.delete("/api/world-model/papers/planet")

        # dreamer_v1 should no longer have connection to planet
        response = seeded_client.get("/api/world-model/papers/dreamer_v1")
        data = response.json()
        assert data["connections"] == []

    def test_delete_nonexistent_paper_returns_404(self, seeded_client):
        """Deleting a non-existent paper returns 404."""
        response = seeded_client.delete("/api/world-model/papers/nonexistent")
        assert response.status_code == 404


# ─── POST /api/world-model/connections ─────────────────────────────


class TestCreateConnection:
    """Tests for POST /api/world-model/connections — add connection."""

    def test_create_connection_success(self, seeded_client):
        """Add a new connection between papers."""
        payload = {
            "source_id": "planet",
            "target_id": "dreamer_v1",
            "type": "competes",
        }
        response = seeded_client.post("/api/world-model/connections", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == "planet"
        assert data["target_id"] == "dreamer_v1"
        assert data["type"] == "competes"

    def test_create_duplicate_connection_returns_409(self, seeded_client):
        """Creating a duplicate connection returns conflict."""
        payload = {
            "source_id": "dreamer_v1",
            "target_id": "planet",
            "type": "inherits",
        }
        response = seeded_client.post("/api/world-model/connections", json=payload)
        assert response.status_code == 409

    def test_create_connection_invalid_type_returns_422(self, seeded_client):
        """Connection type must be inherits/competes/borrows."""
        payload = {
            "source_id": "planet",
            "target_id": "dreamer_v1",
            "type": "invalid_type",
        }
        response = seeded_client.post("/api/world-model/connections", json=payload)
        assert response.status_code == 422

    def test_create_connection_nonexistent_paper_returns_404(self, seeded_client):
        """Connection referencing non-existent paper returns 404."""
        payload = {
            "source_id": "nonexistent",
            "target_id": "planet",
            "type": "inherits",
        }
        response = seeded_client.post("/api/world-model/connections", json=payload)
        assert response.status_code == 404


# ─── DELETE /api/world-model/connections ───────────────────────────


class TestDeleteConnection:
    """Tests for DELETE /api/world-model/connections — remove connection."""

    def test_delete_connection_success(self, seeded_client):
        """Remove an existing connection."""
        payload = {
            "source_id": "dreamer_v1",
            "target_id": "planet",
            "type": "inherits",
        }
        response = seeded_client.request("DELETE", "/api/world-model/connections", json=payload)
        assert response.status_code == 200

        # Verify connection is gone
        response = seeded_client.get("/api/world-model/papers/dreamer_v1")
        data = response.json()
        assert data["connections"] == []

    def test_delete_nonexistent_connection_returns_404(self, seeded_client):
        """Deleting a non-existent connection returns 404."""
        payload = {
            "source_id": "planet",
            "target_id": "dreamer_v1",
            "type": "borrows",
        }
        response = seeded_client.request("DELETE", "/api/world-model/connections", json=payload)
        assert response.status_code == 404
