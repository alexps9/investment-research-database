"""add research_sessions table for Research Studio

Revision ID: 0010_research_sessions
Revises: 0009_relation_dedup
Create Date: 2026-06-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0010_research_sessions"
down_revision: Union[str, None] = "0009_relation_dedup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_sessions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("agent_job_id", sa.Text(), nullable=True),
        sa.Column("brief", sa.Text(), nullable=True),
        sa.Column("subtopics", JSONB(), nullable=False, server_default="[]"),
        sa.Column("report", sa.Text(), nullable=True),
        sa.Column("sources", JSONB(), nullable=False, server_default="[]"),
        sa.Column("kb_sources", JSONB(), nullable=False, server_default="[]"),
        sa.Column("scope", JSONB(), nullable=True),
        sa.Column("industry", JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_research_sessions_created_at", "research_sessions", ["created_at"])
    op.create_index("ix_research_sessions_status", "research_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_research_sessions_status", table_name="research_sessions")
    op.drop_index("ix_research_sessions_created_at", table_name="research_sessions")
    op.drop_table("research_sessions")
