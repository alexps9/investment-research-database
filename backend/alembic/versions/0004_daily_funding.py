"""add daily_digests and funding_events tables

Revision ID: 0004_daily_funding
Revises: 0003_sources_enrich
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004_daily_funding"
down_revision: Union[str, None] = "0003_sources_enrich"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_digests",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("digest_date", sa.String(10), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("highlights", JSONB, nullable=False, server_default="[]"),
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_daily_digests_date", "daily_digests", ["digest_date"])

    op.create_table(
        "funding_events",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("round", sa.String(50), nullable=True),
        sa.Column("amount_usd", sa.Float(), nullable=True),
        sa.Column("amount_raw", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("investors", JSONB, nullable=False, server_default="[]"),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("extracted_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_funding_announced_at", "funding_events", ["announced_at"])
    op.create_index("ix_funding_round", "funding_events", ["round"])
    op.create_index("ix_funding_sector", "funding_events", ["sector"])


def downgrade() -> None:
    op.drop_index("ix_funding_sector", table_name="funding_events")
    op.drop_index("ix_funding_round", table_name="funding_events")
    op.drop_index("ix_funding_announced_at", table_name="funding_events")
    op.drop_table("funding_events")
    op.drop_index("ix_daily_digests_date", table_name="daily_digests")
    op.drop_table("daily_digests")
