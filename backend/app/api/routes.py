"""
FastAPI routes
All endpoints must have comprehensive error handling
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    GraphMetadata,
    GraphResponse,
    HealthResponse,
)
from app.models.evolution import EvolutionMapResponse
from app.models.reports import InsightReport
from app.services.citation_network import CitationNetworkBuilder, GraphConstructionError
from app.services.openalex_client import OpenAlexAPIError, OpenAlexClient

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint",
    description="Returns service status and version. Used by frontend to verify backend connectivity.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint

    Returns:
        HealthResponse: Status and version information

    Example:
        GET /api/health
        Response: {"status": "ok", "version": "1.0.0"}
    """
    return HealthResponse(status="ok", version="1.0.0")


@router.get(
    "/search",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    tags=["API"],
    summary="Search papers and build citation network",
    description="""
    Search academic papers and construct citation network graph.

    **Process**:
    1. Fetch top N papers from OpenAlex API by query
    2. Fetch references for each paper (parallel)
    3. Build directed citation graph using NetworkX
    4. Detect communities using Louvain algorithm
    5. Return graph data (nodes, links, metadata)

    **Performance**: Typically 3-10 seconds for 50 papers

    **Rate Limiting**: OpenAlex polite pool (no strict limits, < 10 req/s recommended)

    **Error Handling**: All errors are transparent with actionable messages
    """,
    responses={
        200: {
            "description": "Citation network graph",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [
                            {
                                "id": "W2123456789",
                                "title": "Attention Is All You Need",
                                "cited_by_count": 15000,
                                "publication_year": 2017,
                                "community": 0,
                            }
                        ],
                        "links": [{"source": "W2123456789", "target": "W2887654321"}],
                        "metadata": {
                            "total_nodes": 50,
                            "total_links": 120,
                            "communities": 5,
                            "avg_clustering": 0.35,
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid query parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Query cannot be empty. Provide a search term (e.g., 'machine learning')."
                    }
                }
            },
        },
        503: {
            "description": "OpenAlex API error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "OpenAlexAPIError: Request timeout after 30s | Status: 0 | Suggestion: Try again later"
                    }
                }
            },
        },
        500: {
            "description": "Graph construction error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "GraphConstructionError: Failed to build citation network | Details: papers_count=50"
                    }
                }
            },
        },
    },
)
async def search_papers(
    query: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Search query for academic papers",
        examples=["machine learning"],
    ),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of papers to return", examples=[100]
    ),
) -> GraphResponse:
    """
    Search papers and build citation network

    Args:
        query: Search query string (1-200 characters)
        limit: Number of papers (1-100)

    Returns:
        GraphResponse with nodes, links, metadata

    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 503: OpenAlex API error
        HTTPException 500: Graph construction error

    Example:
        GET /api/search?query=neural%20networks&limit=20
    """
    logger.info(f"Search request: query='{query}', limit={limit}")

    try:
        # Step 1: Fetch papers from OpenAlex
        async with OpenAlexClient() as client:
            papers = await client.fetch_papers(query, limit=limit)

        logger.info(f"Fetched {len(papers)} papers from OpenAlex")

        # Handle empty results
        if not papers:
            logger.warning(f"No papers found for query: '{query}'")
            return GraphResponse(
                nodes=[],
                links=[],
                metadata=GraphMetadata(
                    total_nodes=0, total_links=0, communities=0, avg_clustering=0.0
                ),
            )

        # Step 2: Build citation network
        builder = CitationNetworkBuilder()
        graph_response = builder.build_network(papers)

        logger.info(
            f"Built graph: {graph_response.metadata.total_nodes} nodes, "
            f"{graph_response.metadata.total_links} links, "
            f"{graph_response.metadata.communities} communities"
        )

        return graph_response

    except ValueError as e:
        # Input validation errors (should be caught by Pydantic, but just in case)
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except OpenAlexAPIError as e:
        # Transparent API error
        logger.error(f"OpenAlex API error: {e.format_message()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.format_message()
        )

    except GraphConstructionError as e:
        # Transparent graph error
        logger.error(f"Graph construction error: {e.format_message()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.format_message()
        )

    except Exception as e:
        # Unexpected error (still transparent)
        logger.exception(f"Unexpected error in /search: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


# ── Seed paper endpoints ──────────────────────────────────────────


@router.get(
    "/seed-network",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    tags=["Seed"],
    summary="Get seed papers citation network",
)
async def get_seed_network():
    """
    Return the citation network for the 10 hand-picked seed papers.
    Communities are overridden with hand-labeled technology paths.
    """
    from app.services.seed_network_service import build_seed_network

    try:
        return await build_seed_network()
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex error in /seed-network: {e.format_message()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.format_message(),
        )
    except Exception as e:
        logger.exception(f"Error in /seed-network: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


@router.get(
    "/seed-papers",
    status_code=status.HTTP_200_OK,
    tags=["Seed"],
    summary="Get seed papers with path labels",
)
async def get_seed_papers(
    path: Optional[str] = Query(None, description="Filter by path: A/B/C/D"),
):
    """Return seed papers with full metadata and path labels."""
    from app.services.seed_network_service import get_seed_papers_detail

    if path and path not in ("A", "B", "C", "D"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path '{path}'. Must be A, B, C, or D.",
        )

    try:
        results = await get_seed_papers_detail(path)
        return {"papers": results, "count": len(results)}
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex error in /seed-papers: {e.format_message()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.format_message(),
        )
    except Exception as e:
        logger.exception(f"Error in /seed-papers: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


@router.get(
    "/seed-report/{path}",
    response_model=InsightReport,
    status_code=status.HTTP_200_OK,
    tags=["Seed"],
    summary="Get three-part insight report for a technology path",
)
async def get_seed_report(path: str):
    """
    Return the three-part insight report (temporal, talent, bottleneck)
    for a given technology path (A/B/C/D).
    """
    from app.services.insight_report_service import generate_report

    if path not in ("A", "B", "C", "D"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path '{path}'. Must be A, B, C, or D.",
        )

    try:
        return generate_report(path)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error in /seed-report/{path}: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


# ── Evolution Map endpoints ──────────────────────────────────────


@router.get(
    "/evolution-map",
    response_model=EvolutionMapResponse,
    status_code=status.HTTP_200_OK,
    tags=["Evolution"],
    summary="Get full evolution map data for frontend rendering",
)
async def get_evolution_map():
    """Return lanes, rows, papers, and iterations for the evolution map view."""
    from app.data.evolution_map_data import ITERATIONS, LANES, PAPERS, ROWS

    return EvolutionMapResponse(
        lanes=LANES,
        rows=ROWS,
        papers=PAPERS,
        iterations=ITERATIONS,
    )


@router.get(
    "/evolution-map/world-model",
    response_model=EvolutionMapResponse,
    status_code=status.HTTP_200_OK,
    tags=["Evolution"],
    summary="Get World Model evolution map data",
)
async def get_world_model_map():
    """Return lanes, rows, papers, and iterations for the World Model evolution map."""
    from app.data.world_model_data import ITERATIONS, LANES, PAPERS, ROWS

    return EvolutionMapResponse(
        lanes=LANES,
        rows=ROWS,
        papers=PAPERS,
        iterations=ITERATIONS,
    )
