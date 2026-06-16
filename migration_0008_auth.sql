-- Migration 0008 + 0009: user login auth + entity-relation dedupe.
-- Safe to run in the Supabase SQL editor (idempotent). Alembic applies the
-- same changes automatically on the HF backend startup.

-- ── 0008: users table ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username      text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    display_name  text,
    is_active     boolean NOT NULL DEFAULT true,
    is_admin      boolean NOT NULL DEFAULT false,
    created_at    timestamptz DEFAULT now(),
    last_login_at timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
-- Initial accounts are seeded at backend startup (pbkdf2-hashed); see
-- backend/app/core/seed.py and the SEED_USERS env var.

-- ── 0009: dedupe manual entity relations + enforce uniqueness ─────────────────
DELETE FROM entity_relations a
USING entity_relations b
WHERE a.source_signal_id IS NULL
  AND b.source_signal_id IS NULL
  AND a.subject_entity_id = b.subject_entity_id
  AND a.relation_type     = b.relation_type
  AND a.object_entity_id  = b.object_entity_id
  AND a.ctid > b.ctid;

CREATE UNIQUE INDEX IF NOT EXISTS ix_entity_relations_manual_unique
ON entity_relations (subject_entity_id, relation_type, object_entity_id)
WHERE source_signal_id IS NULL;
