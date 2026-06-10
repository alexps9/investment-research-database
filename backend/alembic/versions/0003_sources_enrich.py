"""enrich sources table with pipeline signal-source fields

Revision ID: 0003_sources_enrich
Revises: 0002_pgvector
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_sources_enrich"
down_revision: Union[str, None] = "0002_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_COLS = [
    ("tier",               sa.String(10)),
    ("sector",             sa.String(50)),
    ("research_focus",     sa.Text()),
    ("tier_reason",        sa.Text()),
    ("notes",              sa.Text()),
    ("source_authority",   sa.String(50)),
    ("last_tweet_at",      sa.DateTime(timezone=True)),
    ("avg_interval_days",  sa.Float()),
    ("arxiv_author_query", sa.Text()),
    ("affiliation_regex",  sa.Text()),
    ("orcid",              sa.Text()),
    ("twitter_url",        sa.Text()),
    ("openalex_url",       sa.Text()),
    ("scholar_url",        sa.Text()),
    ("github_url",         sa.Text()),
    ("personal_url",       sa.Text()),
    ("arxiv_homepage_url", sa.Text()),
]


def upgrade() -> None:
    for col_name, col_type in NEW_COLS:
        op.add_column("sources", sa.Column(col_name, col_type, nullable=True))
    op.create_index("ix_sources_tier", "sources", ["tier"])


def downgrade() -> None:
    op.drop_index("ix_sources_tier", table_name="sources")
    for col_name, _ in reversed(NEW_COLS):
        op.drop_column("sources", col_name)
