"""add org_tags table and organizations.parent_org_id

Revision ID: 0007_org_fields
Revises: 0006_source_experiences
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0007_org_fields"
down_revision: Union[str, None] = "0006_source_experiences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Parent organization (SUBSIDIARY_OF shortcut)
    op.add_column(
        "organizations",
        sa.Column(
            "parent_org_id",
            UUID(as_uuid=False),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Organization ↔ Topic tag links
    op.create_table(
        "org_tags",
        sa.Column("org_id", UUID(as_uuid=False),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=False),
                  sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("assigned_by", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_org_tags_org_id", "org_tags", ["org_id"])


def downgrade() -> None:
    op.drop_index("ix_org_tags_org_id", table_name="org_tags")
    op.drop_table("org_tags")
    op.drop_column("organizations", "parent_org_id")
