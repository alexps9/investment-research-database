# Data Model

PostgreSQL 16 + pgvector. IDs are UUID strings. Timestamps are timezone-aware.
Defined in `backend/app/models/__init__.py`.

> Isolation: the API engine runs at **REPEATABLE READ** (snapshot isolation).
> Write conflicts → 40001/40P01 → 409 (retryable). Get-or-create is race-safe.

## users  (login auth — migration 0008)
App login accounts. Passwords are pbkdf2_sha256 (never plaintext).
`id, username (unique), password_hash, display_name, is_active, is_admin, created_at, last_login_at`
- Seeded on startup from the `SEED_USERS` env (idempotent; existing rows untouched).

## organizations
Companies / universities / labs / media / communities.
`id, name (unique), aliases[], org_type, website_url, description, country, created_at, updated_at`
- `org_type`: company | university | lab | media | community | nonprofit | other

## sources
A person/org/feed/repo we monitor.
`id, name, source_type, organization_id→organizations, affiliation_type, role_title,
description, activity_status, importance_score, reliability_score, is_active`
plus enrichment: `tier, sector, research_focus, tier_reason, notes, source_authority,
last_tweet_at, avg_interval_days, arxiv_author_query, affiliation_regex, orcid,
twitter_url, openalex_url, scholar_url, github_url, personal_url, arxiv_homepage_url`
- `source_type`: person | organization | rss | website | github_repo | arxiv_category | newsletter | social_account
- `activity_status`: very_active | active | normal | inactive | unknown
- `tier`: P0+ | P1 | P2 | P3

## signals
Evidence items. `url` is unique.
`id, source_id→sources, organization_id→organizations, title, url, canonical_url,
signal_type, abstract, content, published_at, collected_at, language, status,
external_id, content_hash`
- `signal_type`: paper | tweet | blog | news | tech_report | github_release | model_release | benchmark | dataset | other
- `status`: collected | processed | duplicated | ignored | archived

## signal_analysis  (1:1 with signal)
`id, signal_id→signals (unique), tldr, summary, why_it_matters, technical_points[],
limitations, topic_tags[], entities[], importance_score, novelty_score,
relevance_score, confidence_score, reading_priority, model_name, prompt_version, metadata`
- `reading_priority`: must_read | recommended | optional | skip

## entities
Canonical knowledge-graph nodes.
`id, name, canonical_name, entity_type, description, homepage_url, metadata`
- unique on (`canonical_name`, `entity_type`)
- `entity_type`: person | organization | paper | model | method | dataset | benchmark | topic | project | system | event

## entity_aliases
`id, entity_id→entities, alias (unique), alias_type`

## signal_entities  (signal ↔ entity, with role)
PK = (`signal_id`, `entity_id`, `role`). `mention_text, confidence, extracted_by, model_name`
- `role`: main_subject | mentioned | author | publisher | method | benchmark | dataset | topic | source

## entity_relations  (knowledge graph edges)
`id, subject_entity_id→entities, relation_type, object_entity_id→entities,
source_signal_id→signals, confidence, extracted_by, model_name`
- `relation_type` ∈ VALID_RELATION_TYPES: WORKS_AT, AFFILIATED_WITH, PUBLISHED,
  AUTHORED, RELEASED, PROPOSES, USES, EVALUATES_ON, BUILT_ON, MENTIONS, ABOUT,
  FOCUSES_ON, RELATED_TO, COMPETES_WITH, IMPROVES, INTRODUCES
- unique on (subject, relation_type, object, source_signal)
- **manual edges** (`source_signal_id IS NULL`) also have a partial unique index
  `ix_entity_relations_manual_unique (subject, relation_type, object)` (migration
  0009) — NULLs are distinct in the base constraint, so this stops duplicate
  manual edges. `add_relation` is idempotent (returns the existing edge).

## embeddings  (pgvector)
`id, object_type, object_id, embedding_type, vector(EMBEDDING_DIMENSIONS), model_name`
- `object_type`: signal | entity | source
- unique on (object_type, object_id, embedding_type, model_name)
- dimension must equal the embedding model's output (default 1024 for bge-m3)

## daily_digests  (Daily Boost)
`id, digest_date (unique, YYYY-MM-DD), summary, highlights(jsonb), signal_count,
model_name, created_at, updated_at`

## funding_events
`id, company_name, organization_id→organizations, round, amount_usd ($M),
amount_raw, currency, investors(jsonb), sector, announced_at, source_url,
description, extracted_by, created_at, updated_at`

## pipeline_runs
Audit log of pipeline stages. `id, run_type, status, started_at, finished_at,
total_items, success_items, failed_items, error_message, metadata`

## Migrations
Alembic lives in `backend/alembic/`. Because the DB is hosted on Supabase, the
SQL is applied **manually** in the Supabase SQL editor:
- `migration_0004.sql` — creates `daily_digests` + `funding_events`.
- `set_embedding_dim.sql` — changes the `embeddings.vector` dimension when the
  embedding model changes (truncates existing vectors).
