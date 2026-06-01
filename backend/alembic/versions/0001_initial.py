"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("aliases", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("org_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("website_url", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("tag_type", sa.String(50), nullable=False, server_default="topic"),
        sa.Column("parent_id", UUID(as_uuid=False), sa.ForeignKey("tags.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="person"),
        sa.Column("organization_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("affiliation_type", sa.String(50), nullable=True),
        sa.Column("role_title", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("activity_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("importance_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("reliability_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])

    op.create_table(
        "source_accounts",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=False), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("handle", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("external_id", sa.Text, nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_source_accounts_platform_url", "source_accounts", ["platform", "url"], unique=True)

    op.create_table(
        "source_tags",
        sa.Column("source_id", UUID(as_uuid=False), sa.ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=False), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("assigned_by", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "signals",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("source_id", UUID(as_uuid=False), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("canonical_url", sa.Text, nullable=True),
        sa.Column("signal_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("abstract", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("external_id", sa.Text, nullable=True),
        sa.Column("content_hash", sa.Text, nullable=True),
        sa.Column("title_hash", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="collected"),
        sa.Column("raw_metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signals_published_at", "signals", ["published_at"])
    op.create_index("ix_signals_signal_type", "signals", ["signal_type"])
    op.create_index("ix_signals_status", "signals", ["status"])

    op.create_table(
        "signal_analysis",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("signal_id", UUID(as_uuid=False), sa.ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("tldr", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("why_it_matters", sa.Text, nullable=True),
        sa.Column("technical_points", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("limitations", sa.Text, nullable=True),
        sa.Column("topic_tags", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("entities", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("importance_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("novelty_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("relevance_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("reading_priority", sa.String(50), nullable=True),
        sa.Column("model_name", sa.Text, nullable=True),
        sa.Column("prompt_version", sa.Text, nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
    )

    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("homepage_url", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_entities_canonical_name_type", "entities", ["canonical_name", "entity_type"], unique=True)
    op.create_index("ix_entities_entity_type", "entities", ["entity_type"])
    op.create_index("ix_entities_canonical_name", "entities", ["canonical_name"])

    op.create_table(
        "entity_aliases",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=False), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.Text, nullable=False, unique=True),
        sa.Column("alias_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "signal_entities",
        sa.Column("signal_id", UUID(as_uuid=False), sa.ForeignKey("signals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=False), sa.ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(50), primary_key=True),
        sa.Column("mention_text", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("extracted_by", sa.Text, nullable=True),
        sa.Column("model_name", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signal_entities_signal_id", "signal_entities", ["signal_id"])
    op.create_index("ix_signal_entities_entity_id", "signal_entities", ["entity_id"])

    op.create_table(
        "entity_relations",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_entity_id", UUID(as_uuid=False), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("object_entity_id", UUID(as_uuid=False), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_signal_id", UUID(as_uuid=False), sa.ForeignKey("signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("extracted_by", sa.Text, nullable=True),
        sa.Column("model_name", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_entity_relations_unique", "entity_relations",
                    ["subject_entity_id", "relation_type", "object_entity_id", "source_signal_id"], unique=True)
    op.create_index("ix_entity_relations_subject", "entity_relations", ["subject_entity_id"])
    op.create_index("ix_entity_relations_object", "entity_relations", ["object_entity_id"])

    op.create_table(
        "embeddings",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("object_type", sa.String(50), nullable=False),
        sa.Column("object_id", UUID(as_uuid=False), nullable=False),
        sa.Column("embedding_type", sa.String(50), nullable=False),
        sa.Column("model_name", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_embeddings_unique", "embeddings",
                    ["object_type", "object_id", "embedding_type", "model_name"], unique=True)

    op.create_table(
        "pipeline_runs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("run_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_table("pipeline_runs")
    op.drop_table("embeddings")
    op.drop_index("ix_entity_relations_object")
    op.drop_index("ix_entity_relations_subject")
    op.drop_index("ix_entity_relations_unique")
    op.drop_table("entity_relations")
    op.drop_index("ix_signal_entities_entity_id")
    op.drop_index("ix_signal_entities_signal_id")
    op.drop_table("signal_entities")
    op.drop_table("entity_aliases")
    op.drop_index("ix_entities_canonical_name")
    op.drop_index("ix_entities_entity_type")
    op.drop_index("ix_entities_canonical_name_type")
    op.drop_table("entities")
    op.drop_table("signal_analysis")
    op.drop_index("ix_signals_status")
    op.drop_index("ix_signals_signal_type")
    op.drop_index("ix_signals_published_at")
    op.drop_table("signals")
    op.drop_table("source_tags")
    op.drop_index("ix_source_accounts_platform_url")
    op.drop_table("source_accounts")
    op.drop_index("ix_sources_source_type")
    op.drop_table("sources")
    op.drop_table("tags")
    op.drop_table("organizations")
