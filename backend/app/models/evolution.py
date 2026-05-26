"""
Pydantic models for Evolution Map (PRD v2 four-layer ontology).

Era -> Bottleneck/Lane -> Row/Paradigm -> Paper
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Layer = Literal["arch", "sys", "infer", "train", "memory"]

Size = Literal["sm", "md", "lg"]

Shape = Literal["circle", "square"]

ConnectionType = Literal["inherits", "competes", "borrows"]


class Connection(BaseModel):
    target: str
    type: ConnectionType


class EvolutionPaper(BaseModel):
    id: str
    title: str
    full_title: Optional[str] = None
    year: int
    quarter: Literal[1, 2, 3, 4]
    paradigm: Optional[str] = None
    layer: Optional[Layer] = "arch"
    lane: str = Field(..., description="Top-level bottleneck lane ID")
    row: str = Field(..., description="Sub-row within lane")
    path: str = Field(default="trunk", description="Track within row (trunk or named fork)")
    size: Size = Field(default="md", description="Legacy sm/md/lg (fallback if no impact_score)")
    shape: Shape = Field(default="circle", description="Node shape encoding")
    builds_on: List[str] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)
    org: Optional[str] = None
    authors: Optional[List[str]] = Field(default_factory=list)
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    cited_by_count: int = 0
    venue_tier: Optional[int] = Field(default=None, description="1-5, T1=top oral, T5=tech report")
    institution_tier: Optional[int] = Field(default=None, description="1-4, T1=top AI lab")
    impact_score: Optional[float] = Field(default=None, description="0-100 continuous, computed")
    impact_override: Optional[float] = Field(
        default=None, description="Manual override for impact_score"
    )
    is_rising: bool = False
    is_weak_signal: bool = False


class LaneDef(BaseModel):
    id: str
    title: str
    subtitle: str
    color: str


class RowDef(BaseModel):
    id: str
    lane: str
    title: str
    subtitle: str


class IterationMutation(BaseModel):
    summary: str
    detail: str
    bottleneck: Optional[str] = None
    result: Optional[str] = None


class IterationDef(BaseModel):
    id: str
    title: str
    subtitle: str
    path: str
    row: str
    papers: List[str]
    mutations: Dict[str, IterationMutation]


class EvolutionMapResponse(BaseModel):
    lanes: List[LaneDef]
    rows: List[RowDef]
    papers: List[EvolutionPaper]
    iterations: List[IterationDef] = Field(default_factory=list)


# ─── World Model API-specific models ──────────────────────────────


class PaperCreate(BaseModel):
    """Request body for creating a paper."""

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    full_title: Optional[str] = None
    year: int = Field(..., ge=1900, le=2100)
    quarter: Literal[1, 2, 3, 4]
    lane: str = Field(..., min_length=1)
    row: str = Field(..., min_length=1)
    path: str = Field(default="trunk")
    paradigm: Optional[str] = None
    layer: Optional[Layer] = "arch"
    shape: Shape = "circle"
    org: Optional[str] = None
    authors: Optional[List[str]] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    cited_by_count: int = 0
    venue_tier: Optional[int] = None
    institution_tier: Optional[int] = None
    impact_score: Optional[float] = None
    impact_override: Optional[float] = None


class PaperUpdate(BaseModel):
    """Request body for updating a paper. All fields optional."""

    title: Optional[str] = None
    full_title: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    quarter: Optional[Literal[1, 2, 3, 4]] = None
    lane: Optional[str] = None
    row: Optional[str] = None
    path: Optional[str] = None
    paradigm: Optional[str] = None
    layer: Optional[Layer] = None
    shape: Optional[Shape] = None
    org: Optional[str] = None
    authors: Optional[List[str]] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    cited_by_count: Optional[int] = None
    venue_tier: Optional[int] = None
    institution_tier: Optional[int] = None
    impact_score: Optional[float] = None
    impact_override: Optional[float] = None


class ConnectionCreate(BaseModel):
    """Request body for creating a connection."""

    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    type: ConnectionType


class WorldModelResponse(BaseModel):
    """Full world model data for frontend."""

    lanes: List[LaneDef]
    rows: List[RowDef]
    papers: List[EvolutionPaper]
