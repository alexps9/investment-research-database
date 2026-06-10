"""add pgvector extension and vector column to embeddings

Revision ID: 0002_pgvector
Revises: 0001_initial
Create Date: 2026-06-09 00:00:00.000000

Behaviour
---------
This migration is *tolerant*: it only adds the pgvector extension, the
``embeddings.vector`` column and its index when the ``vector`` extension is
actually available on the server.

- Supabase / Amazon RDS / the ``pgvector/pgvector`` docker image: the
  extension is available, so the column + IVFFlat index are created.
- Offline SQL generation (``alembic upgrade head --sql``): always emits
  the pgvector DDL (Supabase always has the extension).
- A plain local PostgreSQL install without pgvector: the migration logs a
  notice and skips the vector parts, so ``alembic upgrade head`` still
  succeeds and the app boots.

Dimension
---------
Controlled by the EMBEDDING_DIMENSIONS env var (default 1536, matching
OpenAI text-embedding-3-small / ada-002).
"""

from typing import Sequence, Union
from alembic import op
from alembic import context as alembic_context
import sqlalchemy as sa
import os

revision: str = "0002_pgvector"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))


def _pgvector_available(bind) -> bool:
    row = bind.execute(
        sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
    ).first()
    return row is not None


def upgrade() -> None:
    # In offline (--sql) mode there is no real DB connection; always emit the
    # pgvector DDL because Supabase and RDS both ship with the extension.
    if alembic_context.is_offline_mode():
        pgvector_ok = True
    else:
        bind = op.get_bind()
        pgvector_ok = _pgvector_available(bind)

    if not pgvector_ok:
        print(
            "[0002_pgvector] 'vector' extension is not available on this server — "
            "skipping vector column/index. Install pgvector (or use RDS / the "
            "pgvector docker image) and re-run this migration to enable vector search."
        )
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "embeddings",
        sa.Column("vector", sa.Text, nullable=True),  # placeholder type
    )
    op.execute(
        f"ALTER TABLE embeddings ALTER COLUMN vector TYPE vector({VECTOR_DIM}) "
        f"USING vector::vector({VECTOR_DIM})"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat "
        "ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_ivfflat")
    has_col = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'embeddings' AND column_name = 'vector'"
        )
    ).first()
    if has_col:
        op.drop_column("embeddings", "vector")
    # Do NOT drop the extension — other objects may depend on it.
