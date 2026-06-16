"""research fields: description→introduction, method→approach, entity delete cascade

Revision ID: 0005_research_fields
Revises: 0004_daily_funding
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_research_fields"
down_revision: Union[str, None] = "0004_daily_funding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename entities.description → entities.introduction
    op.alter_column("entities", "description", new_column_name="introduction")

    # 2. Rename method → approach in entity_type
    op.execute("UPDATE entities SET entity_type = 'approach' WHERE entity_type = 'method'")

    # 3. Rename method → approach in tag_type
    op.execute("UPDATE tags SET tag_type = 'approach' WHERE tag_type = 'method'")


def downgrade() -> None:
    op.execute("UPDATE tags SET tag_type = 'method' WHERE tag_type = 'approach'")
    op.execute("UPDATE entities SET entity_type = 'method' WHERE entity_type = 'approach'")
    op.alter_column("entities", "introduction", new_column_name="description")
