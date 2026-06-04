You are helping me build an AI Intelligence Knowledge Base system.

The goal is NOT to generate daily reports yet. The goal of this milestone is to build the knowledge-base foundation for collecting, storing, analyzing, searching, and browsing AI-related signals.

The core product should support this knowledge chain:

Source → Signal → Entity → Relation → Wiki/Search

Context:
I currently maintain a Feishu/Airtable-like table of AI signal sources. Each source may be a person, organization, website, RSS feed, GitHub repo, arXiv category, newsletter, or social account. Existing fields include:
- name
- Twitter/X URL
- organization
- industry/academia/other
- research directions, such as MLSys, Reasoning, Multimodal, Efficient LLM, RL, Pretrain
- activity status

I want to turn this into a real knowledge-base system. For now, focus on the database, backend APIs, and basic frontend UI for knowledge management and Wiki-style retrieval.

Do not implement daily report generation in this milestone.

Use the following architecture:

Backend:
- FastAPI
- SQLAlchemy 2.x
- Alembic migrations
- PostgreSQL
- pgvector-ready embedding table, but the app should still run even if embedding generation is not configured
- Pydantic schemas
- Clean service/repository structure

Frontend:
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui if already available in the project; otherwise use simple clean components
- Build basic pages for sources, signals, entities, wiki search, and entity detail

Optional / future:
- Neo4j is a future derived graph layer. Do NOT make Neo4j required in this milestone.
- However, design the schema so that entities and relations can later be synced to Neo4j.

Main data model:

1. organizations
Fields:
- id UUID primary key
- name text unique
- aliases text[]
- org_type text: company, university, lab, media, community, nonprofit, other
- website_url text
- description text
- country text
- created_at
- updated_at

2. sources
Fields:
- id UUID primary key
- name text not null
- source_type text: person, organization, rss, website, github_repo, arxiv_category, newsletter, social_account
- organization_id nullable FK to organizations
- affiliation_type text: industry, academia, media, independent, other
- role_title text
- description text
- activity_status text: very_active, active, normal, inactive, unknown
- importance_score float default 0.5
- reliability_score float default 0.5
- is_active boolean default true
- created_at
- updated_at

3. source_accounts
Fields:
- id UUID primary key
- source_id FK to sources
- platform text: x, twitter, github, google_scholar, semantic_scholar, homepage, blog, rss, huggingface, other
- handle text nullable
- url text not null
- external_id text nullable
- is_primary boolean default false
- is_active boolean default true
- last_checked_at timestamp nullable
- created_at
Unique:
- platform + url

4. tags
Fields:
- id UUID primary key
- name text unique
- tag_type text: topic, method, domain, content_type, org_type
- parent_id nullable FK to tags
- description text
- created_at

5. source_tags
Fields:
- source_id FK to sources
- tag_id FK to tags
- confidence float default 1.0
- assigned_by text: manual, llm, rule
- created_at
Primary key:
- source_id + tag_id

6. signals
A signal is any external evidence item: paper, tweet, blog, news, tech report, GitHub release, model release, benchmark, dataset.
Fields:
- id UUID primary key
- source_id nullable FK to sources
- organization_id nullable FK to organizations
- title text not null
- url text not null unique
- canonical_url text nullable
- signal_type text: paper, tweet, blog, news, tech_report, github_release, model_release, benchmark, dataset, other
- abstract text nullable
- content text nullable
- published_at timestamp nullable
- collected_at timestamp default now
- language text default 'en'
- external_id text nullable
- content_hash text nullable
- title_hash text nullable
- status text: collected, processed, duplicated, ignored, archived
- raw_metadata JSONB default {}
- created_at
- updated_at

7. signal_analysis
LLM or manual analysis result for each signal.
Fields:
- id UUID primary key
- signal_id FK to signals
- tldr text
- summary text
- why_it_matters text
- technical_points text[]
- limitations text
- topic_tags text[]
- entities text[]
- importance_score float default 0
- novelty_score float default 0
- relevance_score float default 0
- confidence_score float default 0
- reading_priority text: must_read, recommended, optional, skip
- model_name text
- prompt_version text
- analyzed_at timestamp default now
- metadata JSONB default {}

8. entities
Canonical knowledge nodes.
Fields:
- id UUID primary key
- name text not null
- canonical_name text not null
- entity_type text: person, organization, paper, model, method, dataset, benchmark, topic, project, system, event
- description text
- homepage_url text nullable
- metadata JSONB default {}
- created_at
- updated_at
Unique:
- canonical_name + entity_type

9. entity_aliases
Fields:
- id UUID primary key
- entity_id FK to entities
- alias text not null
- alias_type text: abbreviation, full_name, old_name, translated_name, typo, handle, other
- created_at
Unique:
- alias

10. signal_entities
Evidence-level entity mentions.
Fields:
- signal_id FK to signals
- entity_id FK to entities
- mention_text text nullable
- role text: main_subject, mentioned, author, publisher, method, benchmark, dataset, topic, source
- confidence float default 1.0
- extracted_by text nullable
- model_name text nullable
- created_at
Primary key:
- signal_id + entity_id + role

11. entity_relations
Canonical relation graph stored in PostgreSQL first.
Fields:
- id UUID primary key
- subject_entity_id FK to entities
- relation_type text:
  WORKS_AT, AFFILIATED_WITH, PUBLISHED, AUTHORED, RELEASED, PROPOSES, USES, EVALUATES_ON, BUILT_ON, MENTIONS, ABOUT, FOCUSES_ON, RELATED_TO, COMPETES_WITH, IMPROVES, INTRODUCES
- object_entity_id FK to entities
- source_signal_id nullable FK to signals
- confidence float default 1.0
- extracted_by text nullable
- model_name text nullable
- created_at
Unique:
- subject_entity_id + relation_type + object_entity_id + source_signal_id

12. embeddings
Make this pgvector-ready.
Fields:
- id UUID primary key
- object_type text: signal, entity, source
- object_id UUID not null
- embedding_type text: title, abstract, content, summary, entity_description
- embedding vector(1536), nullable if pgvector is unavailable in local dev
- model_name text
- created_at
Unique:
- object_type + object_id + embedding_type + model_name

13. pipeline_runs
Fields:
- id UUID primary key
- run_type text: collect, analyze, extract_entities, extract_relations, embed, sync_graph
- status text: running, success, failed, partial_success
- started_at timestamp default now
- finished_at timestamp nullable
- total_items int default 0
- success_items int default 0
- failed_items int default 0
- error_message text nullable
- metadata JSONB default {}

Build the following backend APIs:

Sources:
- GET /api/sources
- POST /api/sources
- GET /api/sources/{id}
- PATCH /api/sources/{id}
- DELETE /api/sources/{id}
- POST /api/sources/{id}/accounts
- POST /api/sources/{id}/tags

Signals:
- GET /api/signals
  Support filters: signal_type, source_id, organization_id, status, tag, q, published_from, published_to
- POST /api/signals
- GET /api/signals/{id}
- PATCH /api/signals/{id}
- POST /api/signals/{id}/analysis
- POST /api/signals/{id}/entities
- GET /api/signals/{id}/related

Entities:
- GET /api/entities
  Support filters: entity_type, q
- POST /api/entities
- GET /api/entities/{id}
- PATCH /api/entities/{id}
- POST /api/entities/{id}/aliases
- GET /api/entities/{id}/signals
- GET /api/entities/{id}/relations
- POST /api/entities/{id}/relations

Search / Wiki:
- GET /api/search?q=...
  Return grouped results: sources, signals, entities
- GET /api/wiki/entities/{id}
  Return entity profile, aliases, related signals, outgoing relations, incoming relations, and related entities

Pipelines:
- GET /api/runs
- POST /api/runs/mock
  This can create a fake run log for testing

Seed data:
Create seed data that resembles my current Feishu table:
Organizations:
- xAI
- Meta
- OpenAI
- Google DeepMind
- NVIDIA

Tags:
- MLSys
- Reasoning
- Multimodal
- Efficient LLM
- Generative AI
- Theory
- RL
- Pretrain
- AI Agents
- AI Safety
- RAG

Sources:
- xAI as organization source
- Hieu Pham, organization xAI, industry, tag MLSys, account https://x.com/hyhieu226
- Liam Zheng, organization xAI, industry, tag MLSys, account https://x.com/lm_zheng
- Qian Huang, organization xAI, industry, tag Reasoning, account https://x.com/qhwang3
- Greg Yang, organization xAI, industry, tag Theory, account https://x.com/TheGregYang
- Meta as organization source
- Reality Labs at Meta, organization Meta, industry, tag Multimodal or 智能硬件
- Yi Wan, organization Meta, industry, tag RL
- Mike Lewis, organization Meta, industry, tag Pretrain

Example signals:
- one paper signal
- one blog signal
- one tweet signal
- one model_release signal

Example entities:
- xAI
- Meta
- Grok
- Llama
- KV Cache
- MLSys
- Reasoning

Example relations:
- Hieu Pham WORKS_AT xAI
- xAI RELEASED Grok
- KV Cache RELATED_TO MLSys
- Llama RELEASED_BY Meta if you prefer using RELEASED from Meta to Llama

Important design rules:
- PostgreSQL is the source of truth.
- Neo4j is not required yet.
- Do not build daily report generation.
- Do not build subscriber or publishing features.
- Do not hard-code Twitter as a direct source field; use source_accounts.
- Do not let arbitrary relation types appear in the database; use the relation_type enum or validation.
- Treat signals as evidence. Entity relations should optionally point back to a source_signal_id.
- Keep APIs simple and documented.
- Add reasonable indexes for search/filtering:
  - signals.published_at
  - signals.signal_type
  - signals.status
  - sources.source_type
  - entities.entity_type
  - entities.canonical_name
  - entity_relations.subject_entity_id
  - entity_relations.object_entity_id
  - signal_entities.signal_id
  - signal_entities.entity_id

Frontend pages:

1. /dashboard
Show:
- total sources
- total signals
- total entities
- total relations
- latest signals
- latest pipeline runs

2. /sources
Show table:
- name
- type
- organization
- accounts
- tags
- activity_status
- importance_score
- reliability_score
Actions:
- create source
- edit source
- open detail

3. /signals
Show table/card list:
- title
- type
- source
- published_at
- status
- TL;DR if available
- entities
- tags
Actions:
- create signal
- edit signal
- open detail

4. /entities
Show table:
- name
- type
- aliases
- signal count
- relation count
Actions:
- create entity
- open Wiki page

5. /wiki
Search page:
- global search input
- grouped results by entity, signal, source

6. /wiki/entities/[id]
Entity Wiki page:
- name
- type
- description
- aliases
- related signals
- outgoing relations
- incoming relations
- related entities

7. /graph-lite
A simple non-Neo4j relation viewer using PostgreSQL entity_relations.
It can be a table or simple node-edge list. Do not overbuild visualization.

Implementation requirements:
- Make the project runnable locally with Docker Compose if possible.
- Include .env.example.
- Include README.md with setup steps.
- Include Alembic migration.
- Include seed command.
- Include basic unit tests or API smoke tests.
- If the repository already has conventions, follow them.
- If AGENTS.md exists, obey it.
- If no AGENTS.md exists, create one with coding conventions and test commands.

Testing:
- Add or update tests for main APIs.
- Run lint/typecheck/test commands if available.
- If some tests cannot run due to missing environment, document exactly what was not run and why.

Deliverables:
1. Database models and migrations.
2. Seed data.
3. Backend CRUD APIs.
4. Search and Wiki APIs.
5. Basic frontend pages.
6. README setup instructions.
7. AGENTS.md if missing.
8. A concise final summary of changed files and how to run the app.

Please work incrementally:
- First inspect the repository structure.
- Then propose the implementation plan.
- Then implement the MVP.
- Prefer simple, maintainable code over over-engineering.