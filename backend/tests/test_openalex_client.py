"""
OpenAlex Client Tests - TDD Approach

Test Strategy:
- Unit tests with mocked HTTP responses
- Integration tests with real API (marked @pytest.mark.integration)
- Performance tests (marked @pytest.mark.slow)

Coverage Target: >= 85%
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.models.schemas import OpenAlexAPIError, Paper
from app.services.openalex_client import OpenAlexClient

# ============================================================================
# Test 1: Fetch Papers - Success Case
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_papers_returns_valid_papers():
    """
    RED: Write this test FIRST, see it FAIL
    GREEN: Implement fetch_papers() to make it pass
    REFACTOR: Optimize if needed

    Input: Query "machine learning", limit 10
    Expected: List of 10 Paper objects with valid data
    """
    # Arrange: Mock HTTP response
    mock_response_data = {
        "results": [
            {
                "id": "https://openalex.org/W2123456789",
                "title": "Machine Learning Basics",
                "cited_by_count": 100,
                "publication_year": 2020,
                "referenced_works": ["https://openalex.org/W9876543210"],
                "doi": "10.1234/ml.2020",
                "authorships": [
                    {"author": {"display_name": "John Doe"}},
                    {"author": {"display_name": "Jane Smith"}},
                ],
            },
            {
                "id": "https://openalex.org/W2123456790",
                "title": "Deep Learning",
                "cited_by_count": 500,
                "publication_year": 2021,
                "referenced_works": [],
                "doi": None,
                "authorships": [],
            },
        ]
    }

    # Mock httpx.AsyncClient.get
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        async with OpenAlexClient() as client:
            papers = await client.fetch_papers("machine learning", limit=2)

        # Assert
        assert len(papers) == 2
        assert isinstance(papers[0], Paper)

        # Verify first paper
        assert papers[0].id == "W2123456789"
        assert papers[0].title == "Machine Learning Basics"
        assert papers[0].cited_by_count == 100
        assert papers[0].publication_year == 2020
        assert len(papers[0].reference_ids) == 1
        assert papers[0].doi == "10.1234/ml.2020"
        assert "John Doe" in papers[0].author_names

        # Verify second paper
        assert papers[1].id == "W2123456790"
        assert papers[1].cited_by_count == 500
        assert len(papers[1].reference_ids) == 0
        assert papers[1].doi is None


# ============================================================================
# Test 2: Fetch Papers - Timeout Error
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_papers_handles_timeout():
    """
    Test transparent error handling for network timeout

    Input: Mock timeout exception
    Expected: OpenAlexAPIError with clear message and suggestion
    """
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        # Simulate timeout on all retry attempts
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        async with OpenAlexClient() as client:
            with pytest.raises(OpenAlexAPIError) as exc_info:
                await client.fetch_papers("test query", limit=10)

            error = exc_info.value
            # Verify transparent error message
            assert "Request timeout" in error.message
            assert error.status_code == 0
            assert "timeout" in error.details
            assert "Try again later" in error.suggestion


# ============================================================================
# Test 3: Fetch Papers - HTTP Error (503)
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_papers_handles_http_error():
    """
    Test transparent error handling for HTTP errors

    Input: Mock 503 Service Unavailable
    Expected: OpenAlexAPIError with status code and response details
    """
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service temporarily unavailable"

        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="503 Service Unavailable", request=MagicMock(), response=mock_response
        )

        async with OpenAlexClient() as client:
            with pytest.raises(OpenAlexAPIError) as exc_info:
                await client.fetch_papers("test", limit=10)

            error = exc_info.value
            assert error.status_code == 503
            assert "503" in error.message
            assert "Service temporarily unavailable" in error.details["response"]
            assert "503: Service unavailable" in error.suggestion


# ============================================================================
# Test 4: Fetch Papers - Rate Limiting (429) with Retry
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_papers_retries_on_rate_limit():
    """
    Test retry logic with exponential backoff for rate limiting

    Input: First 2 attempts return 429, 3rd attempt returns 200
    Expected: Successful response after retries
    """
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.text = "Too Many Requests"

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"results": []}
    mock_response_200.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        # First 2 calls raise 429, 3rd succeeds
        side_effects = [
            httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response_429),
            httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response_429),
            mock_response_200,
        ]
        mock_get.side_effect = side_effects

        async with OpenAlexClient(max_concurrent=1) as client:
            # Should succeed after retries
            papers = await client.fetch_papers("test", limit=10)
            assert papers == []

            # Verify 3 attempts were made
            assert mock_get.call_count == 3


# ============================================================================
# Test 5: Fetch References - Success
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_references_returns_valid_ids():
    """
    Test fetching references for a single paper

    Input: Valid work_id "W2123456789"
    Expected: List of reference Work IDs
    """
    mock_response_data = {
        "referenced_works": [
            "https://openalex.org/W111",
            "https://openalex.org/W222",
            "https://openalex.org/W333",
        ]
    }

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        async with OpenAlexClient() as client:
            refs = await client.fetch_references("W2123456789")

        assert len(refs) == 3
        assert "https://openalex.org/W111" in refs
        assert all(ref.startswith("https://openalex.org/W") for ref in refs)


# ============================================================================
# Test 6: Fetch Papers - Empty Query Validation
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_papers_validates_empty_query():
    """
    Test input validation for empty query

    Input: Empty string ""
    Expected: ValueError with clear message
    """
    async with OpenAlexClient() as client:
        with pytest.raises(ValueError) as exc_info:
            await client.fetch_papers("", limit=10)

        error_msg = str(exc_info.value)
        assert "Query cannot be empty" in error_msg
        assert "Provide a search term" in error_msg


# ============================================================================
# Test 7: Fetch All References - Parallel Success
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_all_references_parallel_success():
    """
    Test parallel fetching of references for multiple papers

    Input: 20 work IDs
    Expected: Dict with all 20 mappings, completes in < 5 seconds
    """
    work_ids = [f"W{i}" for i in range(100, 120)]  # 20 IDs

    async def mock_fetch_references(work_id: str):
        # Simulate API delay
        import asyncio

        await asyncio.sleep(0.1)
        return [f"{work_id}_ref1", f"{work_id}_ref2"]

    with patch.object(OpenAlexClient, "fetch_references", side_effect=mock_fetch_references):
        import time

        async with OpenAlexClient(max_concurrent=10) as client:
            start = time.time()
            refs_map = await client.fetch_all_references(work_ids)
            elapsed = time.time() - start

        # Verify results
        assert len(refs_map) == 20
        assert all(work_id in refs_map for work_id in work_ids)

        # Verify performance (parallel execution)
        # With max_concurrent=10, 20 requests should take ~0.2s (2 batches)
        # Add buffer for overhead
        assert elapsed < 5.0, f"Took {elapsed}s, expected < 5s"


# ============================================================================
# Test 8: Fetch All References - Partial Failure
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_all_references_handles_partial_failure():
    """
    Test transparent error reporting when some requests fail

    Input: 10 work IDs, 2 fail with API error
    Expected: OpenAlexAPIError listing all failures transparently
    """
    work_ids = [f"W{i}" for i in range(10)]

    async def mock_fetch_references(work_id: str):
        # Simulate failures for W5 and W7
        if work_id in ["W5", "W7"]:
            raise OpenAlexAPIError(message=f"Failed to fetch {work_id}", status_code=404)
        return [f"{work_id}_ref"]

    with patch.object(OpenAlexClient, "fetch_references", side_effect=mock_fetch_references):
        async with OpenAlexClient() as client:
            with pytest.raises(OpenAlexAPIError) as exc_info:
                await client.fetch_all_references(work_ids)

            error = exc_info.value
            # Verify transparent error reporting
            assert "Failed to fetch references for 2/10 papers" in error.message
            assert error.details["failed_count"] == 2
            assert error.details["success_count"] == 8
            assert len(error.details["errors"]) == 2
            # Verify specific failed IDs are listed
            failed_ids = [e["work_id"] for e in error.details["errors"]]
            assert "W5" in failed_ids
            assert "W7" in failed_ids


# ============================================================================
# Integration Tests (Real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_papers_integration_real_api():
    """
    Integration test with real OpenAlex API

    WARNING: Requires internet connection
    Run with: pytest -m integration
    """
    async with OpenAlexClient() as client:
        papers = await client.fetch_papers("neural networks", limit=5)

        # Verify real API response
        assert len(papers) <= 5
        assert all(isinstance(p, Paper) for p in papers)
        assert all(p.id.startswith("W") for p in papers)
        assert all(p.cited_by_count >= 0 for p in papers)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_references_integration_real_api():
    """
    Integration test for fetching references from real API

    Uses a known paper: "Attention Is All You Need" (W2963663549)
    """
    async with OpenAlexClient() as client:
        refs = await client.fetch_references("W2963663549")

        # Verify real references
        assert len(refs) > 0
        assert all(isinstance(ref, str) for ref in refs)


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.asyncio
async def test_fetch_papers_performance():
    """
    Performance test: Fetch 50 papers in < 5 seconds

    Run with: pytest -m slow
    """
    import time

    async with OpenAlexClient() as client:
        start = time.time()
        papers = await client.fetch_papers("computer science", limit=50)
        elapsed = time.time() - start

        assert len(papers) <= 50
        assert elapsed < 5.0, f"Took {elapsed}s, target < 5s"


@pytest.mark.slow
@pytest.mark.asyncio
async def test_fetch_all_references_performance():
    """
    Performance test: Fetch references for 50 papers in < 10 seconds

    Requires integration test setup
    """
    import time

    async with OpenAlexClient() as client:
        # First get 50 papers
        papers = await client.fetch_papers("machine learning", limit=50)
        work_ids = [p.id for p in papers[:50]]

        # Then fetch all references in parallel
        start = time.time()
        refs_map = await client.fetch_all_references(work_ids)
        elapsed = time.time() - start

        assert len(refs_map) > 0
        assert elapsed < 10.0, f"Took {elapsed}s, target < 10s"
