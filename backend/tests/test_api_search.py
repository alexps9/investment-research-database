"""
/search Endpoint Tests - TDD Approach

Test Types:
- Unit tests (mocked dependencies)
- Integration tests (real OpenAlex API)
- E2E tests (full stack)

Coverage Target: >= 85%
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import GraphConstructionError, GraphResponse, OpenAlexAPIError, Paper

client = TestClient(app)


# ============================================================================
# Test 1: Search - Success (Mocked)
# ============================================================================


def test_search_returns_valid_graph():
    """
    RED: Write this test FIRST, see it FAIL
    GREEN: Implement /search endpoint to make it pass

    Input: Query "deep learning", limit 10
    Expected: 200 response with valid GraphResponse
    """
    # Mock papers
    mock_papers = [
        Paper(
            id=f"W{i}",
            title=f"Paper {i}",
            cited_by_count=100 * i,
            publication_year=2020,
            reference_ids=[f"W{j}" for j in range(max(0, i - 1), i)],
        )
        for i in range(10)
    ]

    with patch("app.api.routes.OpenAlexClient") as MockClient:
        # Mock fetch_papers
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.fetch_papers = AsyncMock(return_value=mock_papers)

        # Execute request
        response = client.get("/api/search?query=deep%20learning&limit=10")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "nodes" in data
        assert "links" in data
        assert "metadata" in data

        assert data["metadata"]["total_nodes"] == 10
        assert data["metadata"]["communities"] >= 1

        # Verify node structure
        node = data["nodes"][0]
        assert "id" in node
        assert "title" in node
        assert "cited_by_count" in node
        assert "community" in node


# ============================================================================
# Test 2: Search - Query Validation
# ============================================================================


def test_search_validates_query_required():
    """
    Test that query parameter is required

    Input: No query parameter
    Expected: 422 Unprocessable Entity
    """
    response = client.get("/api/search?limit=10")

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_search_validates_query_min_length():
    """
    Test query minimum length validation

    Input: Empty query ""
    Expected: 422 or 400
    """
    response = client.get("/api/search?query=&limit=10")

    # FastAPI Pydantic validation returns 422
    assert response.status_code in [400, 422]


# ============================================================================
# Test 3: Search - Limit Validation
# ============================================================================


def test_search_validates_limit_range():
    """
    Test limit parameter range validation

    Input: limit=150 (exceeds max 100)
    Expected: 422 Unprocessable Entity
    """
    response = client.get("/api/search?query=test&limit=150")

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_search_validates_limit_minimum():
    """
    Test limit minimum validation

    Input: limit=0
    Expected: 422
    """
    response = client.get("/api/search?query=test&limit=0")

    assert response.status_code == 422


# ============================================================================
# Test 4: Search - OpenAlex Error Handling
# ============================================================================


def test_search_handles_openalex_error():
    """
    Test transparent error handling for OpenAlex API failures

    Input: Mock OpenAlexAPIError
    Expected: 503 with transparent error message
    """
    with patch("app.api.routes.OpenAlexClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.fetch_papers = AsyncMock(
            side_effect=OpenAlexAPIError(
                message="Request timeout after 30s", status_code=0, suggestion="Try again later"
            )
        )

        response = client.get("/api/search?query=test&limit=10")

        assert response.status_code == 503

        data = response.json()
        assert "timeout" in data["detail"].lower()
        assert "try again later" in data["detail"].lower()


# ============================================================================
# Test 5: Search - Empty Results
# ============================================================================


def test_search_handles_empty_results():
    """
    Test handling of queries with no results

    Input: Query returns 0 papers
    Expected: 200 with empty graph
    """
    with patch("app.api.routes.OpenAlexClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.fetch_papers = AsyncMock(return_value=[])

        response = client.get("/api/search?query=nonexistentxyz123&limit=10")

        assert response.status_code == 200

        data = response.json()
        assert data["metadata"]["total_nodes"] == 0
        assert data["metadata"]["total_links"] == 0
        assert data["metadata"]["communities"] == 0


# ============================================================================
# Test 6: Search - Graph Construction Error
# ============================================================================


def test_search_handles_graph_construction_error():
    """
    Test error handling when graph construction fails

    Input: Mock GraphConstructionError
    Expected: 500 with transparent error message
    """
    mock_papers = [
        Paper(id="W1", title="Test", cited_by_count=0, publication_year=2020, reference_ids=[])
    ]

    with (
        patch("app.api.routes.OpenAlexClient") as MockClient,
        patch("app.api.routes.CitationNetworkBuilder") as MockBuilder,
    ):

        mock_client = MockClient.return_value.__aenter__.return_value
        mock_client.fetch_papers = AsyncMock(return_value=mock_papers)

        mock_builder_instance = MockBuilder.return_value
        mock_builder_instance.build_network.side_effect = GraphConstructionError(
            message="Failed to detect communities", details={"error": "Test error"}
        )

        response = client.get("/api/search?query=test&limit=10")

        assert response.status_code == 500

        data = response.json()
        assert "GraphConstructionError" in data["detail"]


# ============================================================================
# Test 7: Search - Integration Test (Real API)
# ============================================================================


@pytest.mark.integration
def test_search_integration_end_to_end():
    """
    Integration test with real OpenAlex API

    WARNING: Requires internet connection
    Run with: pytest -m integration

    Expected: Complete workflow works end-to-end
    """
    response = client.get("/api/search?query=machine%20learning&limit=20")

    # Should succeed
    assert response.status_code == 200

    data = response.json()

    # Verify structure
    assert "nodes" in data
    assert "links" in data
    assert "metadata" in data

    # Verify data
    assert len(data["nodes"]) <= 20
    assert data["metadata"]["total_nodes"] <= 20
    assert data["metadata"]["communities"] >= 1

    # Verify nodes have all required fields
    if data["nodes"]:
        node = data["nodes"][0]
        assert "id" in node
        assert "title" in node
        assert "cited_by_count" in node
        assert "publication_year" in node
        assert "community" in node
