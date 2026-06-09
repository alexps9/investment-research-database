"""add pgvector extension and vector column to embeddings

Revision ID: 0002_pgvector
Revises: 0001_initial
Create Date: 2026-06-09 00:00:00.000000

Prerequisites
-------------
- PostgreSQL 15+ (or RDS for PostgreSQL 15+) with pgvector extension available.
- On RDS, pgvector is pre-installed; just run this migration.
- On plain docker postgres:16-alpine, install the extension first:
    docker compose exec db sh -c "apk add --no-cache pgvector postgresql16-pgvector 2>/dev/null || true"
  Or simply use ankane/pgvector image instead of postgres:16-alpine.

Dimension
---------
The vector column is fixed at 1536 to match OpenAI text-embedding-3-small /
text-embedding-ada-002.  If you need a different dimension, edit this file
before running the migration, then update EMBEDDING_DIMENSIONS in .env.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import os

revision: str = "0002_pgvector"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Read dimension from env so it stays in sync with Settings.embedding_dimensions.
VECTOR_DIM = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "embeddings",
        sa.Column("vector", sa.Text, nullable=True),  # placeholder type
    )

    # Replace placeholder with real vector type now that the extension exists.
    op.execute(
        f"ALTER TABLE embeddings ALTER COLUMN vector TYPE vector({VECTOR_DIM}) "
        f"USING vector::vector({VECTOR_DIM})"
    )

    # IVFFlat index for approximate nearest-neighbour search.
    # lists=100 is a reasonable default for up to ~1M rows; tune as data grows.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat "
        "ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_ivfflat")
    op.drop_column("embeddings", "vector")
    # Do NOT drop the extension — other tables may depend on it.
