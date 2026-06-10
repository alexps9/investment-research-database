-- ============================================================
-- Migration 0003: Add extended fields to sources table
-- Run this in Supabase SQL Editor if your DB already has
-- migrations 0001 and 0002 applied.
-- ============================================================

BEGIN;

ALTER TABLE sources ADD COLUMN IF NOT EXISTS tier               VARCHAR(10);
ALTER TABLE sources ADD COLUMN IF NOT EXISTS sector             VARCHAR(50);
ALTER TABLE sources ADD COLUMN IF NOT EXISTS research_focus     TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS tier_reason        TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS notes              TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS source_authority   VARCHAR(50);
ALTER TABLE sources ADD COLUMN IF NOT EXISTS last_tweet_at      TIMESTAMP WITH TIME ZONE;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS avg_interval_days  FLOAT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS arxiv_author_query TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS affiliation_regex  TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS orcid              TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS twitter_url        TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS openalex_url       TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS scholar_url        TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS github_url         TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS personal_url       TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS arxiv_homepage_url TEXT;

CREATE INDEX IF NOT EXISTS ix_sources_tier ON sources (tier);

-- Update alembic version tracking
UPDATE alembic_version
SET version_num = '0003_sources_enrich'
WHERE version_num = '0002_pgvector';

COMMIT;
