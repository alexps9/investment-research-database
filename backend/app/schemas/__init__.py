from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ── Organization ────────────────────────────────────────────────────────────

class OrganizationBase(BaseModel):
    name: str
    aliases: list[str] = []
    org_type: str = "other"
    website_url: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    org_type: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None


class OrganizationOut(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# ── Source ───────────────────────────────────────────────────────────────────

class SourceAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    platform: str
    handle: Optional[str] = None
    url: str
    is_primary: bool
    is_active: bool


class SourceTagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tag_id: str
    confidence: float
    assigned_by: str
    tag: Optional["TagOut"] = None


class SourceBase(BaseModel):
    name: str
    source_type: str = "person"
    organization_id: Optional[str] = None
    affiliation_type: Optional[str] = None
    role_title: Optional[str] = None
    description: Optional[str] = None
    activity_status: str = "unknown"
    importance_score: float = 0.5
    reliability_score: float = 0.5
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    organization_id: Optional[str] = None
    affiliation_type: Optional[str] = None
    role_title: Optional[str] = None
    description: Optional[str] = None
    activity_status: Optional[str] = None
    importance_score: Optional[float] = None
    reliability_score: Optional[float] = None
    is_active: Optional[bool] = None


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization: Optional[OrganizationOut] = None
    accounts: list[SourceAccountOut] = []
    source_tags: list[SourceTagOut] = []
    created_at: datetime
    updated_at: datetime


class SourceAccountCreate(BaseModel):
    platform: str
    handle: Optional[str] = None
    url: str
    external_id: Optional[str] = None
    is_primary: bool = False


class SourceTagCreate(BaseModel):
    tag_id: str
    confidence: float = 1.0
    assigned_by: str = "manual"


# ── Tag ──────────────────────────────────────────────────────────────────────

class TagBase(BaseModel):
    name: str
    tag_type: str = "topic"
    parent_id: Optional[str] = None
    description: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


SourceTagOut.model_rebuild()


# ── Signal ───────────────────────────────────────────────────────────────────

class SignalAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tldr: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    technical_points: list[str] = []
    limitations: Optional[str] = None
    topic_tags: list[str] = []
    entities: list[str] = []
    importance_score: float
    novelty_score: float
    relevance_score: float
    confidence_score: float
    reading_priority: Optional[str] = None
    model_name: Optional[str] = None
    analyzed_at: datetime


class SignalBase(BaseModel):
    title: str
    url: str
    signal_type: str = "other"
    source_id: Optional[str] = None
    organization_id: Optional[str] = None
    abstract: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str = "en"
    status: str = "collected"
    raw_metadata: dict = {}


class SignalCreate(SignalBase):
    pass


class SignalUpdate(BaseModel):
    title: Optional[str] = None
    signal_type: Optional[str] = None
    source_id: Optional[str] = None
    organization_id: Optional[str] = None
    abstract: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    status: Optional[str] = None
    raw_metadata: Optional[dict] = None


class SignalOut(SignalBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    collected_at: datetime
    canonical_url: Optional[str] = None
    content_hash: Optional[str] = None
    title_hash: Optional[str] = None
    external_id: Optional[str] = None
    analysis: Optional[SignalAnalysisOut] = None
    created_at: datetime
    updated_at: datetime


class SignalAnalysisCreate(BaseModel):
    tldr: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    technical_points: list[str] = []
    limitations: Optional[str] = None
    topic_tags: list[str] = []
    entities: list[str] = []
    importance_score: float = 0.0
    novelty_score: float = 0.0
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    reading_priority: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    metadata: dict = {}


class SignalEntityCreate(BaseModel):
    entity_id: str
    role: str
    mention_text: Optional[str] = None
    confidence: float = 1.0
    extracted_by: Optional[str] = None


# ── Entity ───────────────────────────────────────────────────────────────────

class EntityAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    alias: str
    alias_type: str


class EntityBase(BaseModel):
    name: str
    canonical_name: str
    entity_type: str
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    metadata: dict = {}


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    canonical_name: Optional[str] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    metadata: Optional[dict] = None


class EntityOut(EntityBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    aliases: list[EntityAliasOut] = []
    created_at: datetime
    updated_at: datetime


class EntityAliasCreate(BaseModel):
    alias: str
    alias_type: str = "other"


class EntityRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    subject_entity_id: str
    relation_type: str
    object_entity_id: str
    source_signal_id: Optional[str] = None
    confidence: float
    extracted_by: Optional[str] = None
    created_at: datetime
    subject: Optional["EntityOut"] = None
    object_entity: Optional["EntityOut"] = None


EntityRelationOut.model_rebuild()


class EntityRelationCreate(BaseModel):
    subject_entity_id: str
    relation_type: str
    object_entity_id: str
    source_signal_id: Optional[str] = None
    confidence: float = 1.0
    extracted_by: Optional[str] = None


# ── Pipeline ─────────────────────────────────────────────────────────────────

class PipelineRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    run_type: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    total_items: int
    success_items: int
    failed_items: int
    error_message: Optional[str] = None


class PipelineRunCreate(BaseModel):
    run_type: str
    status: str = "success"
    total_items: int = 0
    success_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None
    metadata: dict = {}


# ── Search ───────────────────────────────────────────────────────────────────

class SearchResults(BaseModel):
    sources: list[SourceOut] = []
    signals: list[SignalOut] = []
    entities: list[EntityOut] = []


# ── Wiki ─────────────────────────────────────────────────────────────────────

class WikiEntityProfile(BaseModel):
    entity: EntityOut
    aliases: list[EntityAliasOut] = []
    related_signals: list[SignalOut] = []
    outgoing_relations: list[EntityRelationOut] = []
    incoming_relations: list[EntityRelationOut] = []
    related_entities: list[EntityOut] = []


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int
