import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Float, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    org_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="other"
    )  # company, university, lab, media, community, nonprofit, other
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list["Source"]] = relationship("Source", back_populates="organization")
    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="organization")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="person"
    )  # person, organization, rss, website, github_repo, arxiv_category, newsletter, social_account
    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    affiliation_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # industry, academia, media, independent, other
    role_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="unknown"
    )  # very_active, active, normal, inactive, unknown
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.5")
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.5")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization | None"] = relationship("Organization", back_populates="sources")
    accounts: Mapped[list["SourceAccount"]] = relationship("SourceAccount", back_populates="source", cascade="all, delete-orphan")
    source_tags: Mapped[list["SourceTag"]] = relationship("SourceTag", back_populates="source", cascade="all, delete-orphan")
    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="source")

    __table_args__ = (
        Index("ix_sources_source_type", "source_type"),
    )


class SourceAccount(Base):
    __tablename__ = "source_accounts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # x, twitter, github, google_scholar, semantic_scholar, homepage, blog, rss, huggingface, other
    handle: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["Source"] = relationship("Source", back_populates="accounts")

    __table_args__ = (
        Index("ix_source_accounts_platform_url", "platform", "url", unique=True),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    tag_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="topic"
    )  # topic, method, domain, content_type, org_type
    parent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tags.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parent: Mapped["Tag | None"] = relationship("Tag", remote_side="Tag.id")
    source_tags: Mapped[list["SourceTag"]] = relationship("SourceTag", back_populates="tag", cascade="all, delete-orphan")


class SourceTag(Base):
    __tablename__ = "source_tags"

    source_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    assigned_by: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="manual"
    )  # manual, llm, rule
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["Source"] = relationship("Source", back_populates="source_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="source_tags")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    signal_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="other"
    )  # paper, tweet, blog, news, tech_report, github_release, model_release, benchmark, dataset, other
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    title_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="collected"
    )  # collected, processed, duplicated, ignored, archived
    raw_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped["Source | None"] = relationship("Source", back_populates="signals")
    organization: Mapped["Organization | None"] = relationship("Organization", back_populates="signals")
    analysis: Mapped["SignalAnalysis | None"] = relationship("SignalAnalysis", back_populates="signal", uselist=False, cascade="all, delete-orphan")
    signal_entities: Mapped[list["SignalEntity"]] = relationship("SignalEntity", back_populates="signal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_signals_published_at", "published_at"),
        Index("ix_signals_signal_type", "signal_type"),
        Index("ix_signals_status", "status"),
    )


class SignalAnalysis(Base):
    __tablename__ = "signal_analysis"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    signal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    tldr: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_points: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    entities: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    reading_priority: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # must_read, recommended, optional, skip
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")

    signal: Mapped["Signal"] = relationship("Signal", back_populates="analysis")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # person, organization, paper, model, method, dataset, benchmark, topic, project, system, event
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list["EntityAlias"]] = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    signal_entities: Mapped[list["SignalEntity"]] = relationship("SignalEntity", back_populates="entity", cascade="all, delete-orphan")
    outgoing_relations: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation", foreign_keys="EntityRelation.subject_entity_id", back_populates="subject", cascade="all, delete-orphan"
    )
    incoming_relations: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation", foreign_keys="EntityRelation.object_entity_id", back_populates="object_entity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_entities_canonical_name_type", "canonical_name", "entity_type", unique=True),
        Index("ix_entities_entity_type", "entity_type"),
        Index("ix_entities_canonical_name", "canonical_name"),
    )


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    alias_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="other"
    )  # abbreviation, full_name, old_name, translated_name, typo, handle, other
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="aliases")


class SignalEntity(Base):
    __tablename__ = "signal_entities"

    signal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("signals.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )  # main_subject, mentioned, author, publisher, method, benchmark, dataset, topic, source
    mention_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    extracted_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signal: Mapped["Signal"] = relationship("Signal", back_populates="signal_entities")
    entity: Mapped["Entity"] = relationship("Entity", back_populates="signal_entities")

    __table_args__ = (
        Index("ix_signal_entities_signal_id", "signal_id"),
        Index("ix_signal_entities_entity_id", "entity_id"),
    )


VALID_RELATION_TYPES = {
    "WORKS_AT", "AFFILIATED_WITH", "PUBLISHED", "AUTHORED", "RELEASED",
    "PROPOSES", "USES", "EVALUATES_ON", "BUILT_ON", "MENTIONS", "ABOUT",
    "FOCUSES_ON", "RELATED_TO", "COMPETES_WITH", "IMPROVES", "INTRODUCES",
}


class EntityRelation(Base):
    __tablename__ = "entity_relations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    subject_entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    object_entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    source_signal_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("signals.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    extracted_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subject: Mapped["Entity"] = relationship("Entity", foreign_keys=[subject_entity_id], back_populates="outgoing_relations")
    object_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[object_entity_id], back_populates="incoming_relations")
    source_signal: Mapped["Signal | None"] = relationship("Signal")

    __table_args__ = (
        Index(
            "ix_entity_relations_unique",
            "subject_entity_id", "relation_type", "object_entity_id", "source_signal_id",
            unique=True,
        ),
        Index("ix_entity_relations_subject", "subject_entity_id"),
        Index("ix_entity_relations_object", "object_entity_id"),
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)  # signal, entity, source
    object_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    embedding_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # title, abstract, content, summary, entity_description
    # vector column is added conditionally if pgvector is available
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_embeddings_unique",
            "object_type", "object_id", "embedding_type", "model_name",
            unique=True,
        ),
    )


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    run_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # collect, analyze, extract_entities, extract_relations, embed, sync_graph
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="running"
    )  # running, success, failed, partial_success
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    success_items: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
