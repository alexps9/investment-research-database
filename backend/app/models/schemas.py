"""
Pydantic models for request/response validation
Ensures type safety and automatic OpenAPI docs
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check response
    Matches frontend expectation in api-client.ts
    """

    status: str = Field(..., description="Service status", examples=["ok"])
    version: str = Field(
        ...,
        description="API version (semantic versioning)",
        pattern=r"^\d+\.\d+\.\d+$",
        examples=["1.0.0"],
    )

    model_config = {"json_schema_extra": {"examples": [{"status": "ok", "version": "1.0.0"}]}}


class Paper(BaseModel):
    """
    Paper data from OpenAlex API

    Represents a single academic work with citation metadata.
    Maps directly to OpenAlex /works endpoint response.
    """

    id: str = Field(
        ..., description="OpenAlex Work ID (format: W1234567890)", examples=["W2123456789"]
    )
    title: str = Field(
        ...,
        description="Paper title",
        min_length=1,
        max_length=500,
        examples=["Attention Is All You Need"],
    )
    cited_by_count: int = Field(
        default=0, description="Number of citations", ge=0, examples=[15000]
    )
    publication_year: int = Field(
        ..., description="Year of publication", ge=1900, le=2100, examples=[2017]
    )
    reference_ids: List[str] = Field(
        default_factory=list,
        description="OpenAlex IDs of cited papers",
        examples=[["W2887654321", "W2776543210"]],
    )
    doi: Optional[str] = Field(
        None, description="Digital Object Identifier", examples=["10.48550/arXiv.1706.03762"]
    )
    author_names: List[str] = Field(
        default_factory=list,
        description="Author names",
        examples=[["Ashish Vaswani", "Noam Shazeer"]],
    )
    abstract: Optional[str] = Field(
        None, description="Paper abstract text (reconstructed from inverted index)"
    )
    institutions: List[str] = Field(
        default_factory=list,
        description="Author institutions",
        examples=[["Google Brain", "Stanford University"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "W2123456789",
                    "title": "Attention Is All You Need",
                    "cited_by_count": 15000,
                    "publication_year": 2017,
                    "reference_ids": ["W2887654321"],
                    "doi": "10.48550/arXiv.1706.03762",
                    "author_names": ["Ashish Vaswani", "Noam Shazeer"],
                    "abstract": None,
                    "institutions": ["Google Brain"],
                }
            ]
        }
    }


class OpenAlexAPIError(Exception):
    """
    OpenAlex API communication error with transparent details

    Philosophy: NEVER hide API errors. Always include:
    - What failed (endpoint, query)
    - Why it failed (status code, response)
    - How to fix (actionable suggestion)
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        details: Optional[dict] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.suggestion = suggestion or "Check OpenAlex API status at https://docs.openalex.org/"
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error with full transparency"""
        parts = [f"OpenAlexAPIError: {self.message}"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")

        parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts)


class Node(BaseModel):
    """Graph node representing a paper"""

    id: str = Field(..., description="Paper ID")
    title: str = Field(..., description="Paper title")
    cited_by_count: int = Field(default=0, description="Citation count")
    publication_year: int = Field(..., description="Publication year")
    community: Optional[int] = Field(None, description="Community ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "W2123456789",
                    "title": "Attention Is All You Need",
                    "cited_by_count": 15000,
                    "publication_year": 2017,
                    "community": 0,
                }
            ]
        }
    }


class Link(BaseModel):
    """Graph edge representing a citation"""

    source: str = Field(..., description="Source paper ID (cites)")
    target: str = Field(..., description="Target paper ID (cited)")

    model_config = {
        "json_schema_extra": {"examples": [{"source": "W2123456789", "target": "W2887654321"}]}
    }


class GraphMetadata(BaseModel):
    """Graph metadata and statistics"""

    total_nodes: int = Field(..., description="Total number of papers")
    total_links: int = Field(..., description="Total number of citations")
    communities: int = Field(..., description="Number of communities detected")
    community_names: Dict[str, str] = Field(default_factory=dict, description="Community ID to name mapping")
    avg_clustering: Optional[float] = Field(None, description="Average clustering coefficient")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_nodes": 50,
                    "total_links": 120,
                    "communities": 5,
                    "avg_clustering": 0.35,
                }
            ]
        }
    }


class GraphResponse(BaseModel):
    """Citation network graph response"""

    nodes: List[Node] = Field(..., description="Graph nodes (papers)")
    links: List[Link] = Field(..., description="Graph edges (citations)")
    metadata: GraphMetadata = Field(..., description="Graph statistics")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
            ]
        }
    }


class GraphConstructionError(Exception):
    """Graph construction error with transparent details"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.format_message())

    def format_message(self) -> str:
        parts = [f"GraphConstructionError: {self.message}"]
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")
        return " | ".join(parts)
