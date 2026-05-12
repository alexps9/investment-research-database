"""
Pydantic models for the three-part insight reports.

Each technology path produces:
- TemporalReport: where is this tech in its lifecycle?
- TalentReport: who are the key people and institutions?
- BottleneckReport: what problems remain, what's next?
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Milestone(BaseModel):
    """A key event in a technology path's timeline."""

    year: int
    paper_title: str
    contribution: str


class TemporalReport(BaseModel):
    """时空定位: technology lifecycle positioning."""

    stage: str = Field(..., description="Lifecycle stage: 萌芽/成长/成熟/衰退")
    timeline_desc: str = Field(..., description="Narrative of the path's evolution")
    key_milestones: List[Milestone] = Field(default_factory=list)
    year_range: str = Field(..., description="e.g. 2023-2024")


class AuthorInfo(BaseModel):
    """An author with aggregated stats."""

    name: str
    paper_count: int
    total_citations: int


class InstitutionInfo(BaseModel):
    """An institution with paper count."""

    name: str
    paper_count: int
    category: str = Field(..., description="academic / industry")


class TalentReport(BaseModel):
    """人才图谱: key researchers and institutions."""

    top_authors: List[AuthorInfo] = Field(default_factory=list)
    institutions: List[InstitutionInfo] = Field(default_factory=list)
    summary: str = Field(..., description="One-paragraph talent summary")


class BottleneckReport(BaseModel):
    """瓶颈分析: current problems and future directions."""

    current_bottleneck: str = Field(..., description="Main unsolved problem")
    existing_solutions: List[str] = Field(default_factory=list)
    next_directions: List[str] = Field(default_factory=list)
    summary: str = Field(..., description="One-paragraph bottleneck summary")


class InsightReport(BaseModel):
    """Complete three-part report for a technology path."""

    path: str = Field(..., description="Path letter: A/B/C/D")
    path_name: str = Field(..., description="Human-readable path name")
    temporal: TemporalReport
    talent: TalentReport
    bottleneck: BottleneckReport
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    paper_count: int = Field(..., description="Number of papers in this path")
