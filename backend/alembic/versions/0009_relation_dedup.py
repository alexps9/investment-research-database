"""dedupe manual entity relations and enforce uniqueness

The base UNIQUE(subject, relation_type, object, source_signal_id) does not
prevent duplicate *manual* relations because PostgreSQL treats NULL
source_signal_id values as distinct. This adds a partial unique index covering
manual relations (source_signal_id IS NULL) after removing existing dupes, so
repeated "add relation" clicks can no longer create phantom duplicate edges.

Revision ID: 0009_relation_dedup
Revises: 0008_users
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0009_relation_dedup"
down_revision: Union[str, None] = "0008_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove duplicate manual relations, keeping one physical row per key.
    op.execute(
        """
        DELETE FROM entity_relations a
        USING entity_relations b
        WHERE a.source_signal_id IS NULL
          AND b.source_signal_id IS NULL
          AND a.subject_entity_id = b.subject_entity_id
          AND a.relation_type     = b.relation_type
          AND a.object_entity_id  = b.object_entity_id
          AND a.ctid > b.ctid
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_entity_relations_manual_unique
        ON entity_relations (subject_entity_id, relation_type, object_entity_id)
        WHERE source_signal_id IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_entity_relations_manual_unique")
