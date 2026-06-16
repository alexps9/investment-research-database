"""add source_experiences table

Revision ID: 0006_source_experiences
Revises: 0005_research_fields
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0006_source_experiences"
down_revision: Union[str, None] = "0005_research_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_experiences",
        sa.Column("id", UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", UUID(as_uuid=False),
                  sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=False),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("org_name_raw", sa.Text(), nullable=True),  # fallback if org not in DB
        sa.Column("role_title", sa.Text(), nullable=True),
        sa.Column("start_date", sa.String(7), nullable=True),  # YYYY-MM
        sa.Column("end_date", sa.String(7), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_source_experiences_source_id", "source_experiences", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_source_experiences_source_id", table_name="source_experiences")
    op.drop_table("source_experiences")
