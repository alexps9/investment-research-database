BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

CREATE TABLE organizations (
    id UUID NOT NULL, 
    name TEXT NOT NULL, 
    aliases TEXT[] DEFAULT '{}' NOT NULL, 
    org_type VARCHAR(50) DEFAULT 'other' NOT NULL, 
    website_url TEXT, 
    description TEXT, 
    country VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE tags (
    id UUID NOT NULL, 
    name TEXT NOT NULL, 
    tag_type VARCHAR(50) DEFAULT 'topic' NOT NULL, 
    parent_id UUID, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    UNIQUE (name), 
    FOREIGN KEY(parent_id) REFERENCES tags (id) ON DELETE SET NULL
);

CREATE TABLE sources (
    id UUID NOT NULL, 
    name TEXT NOT NULL, 
    source_type VARCHAR(50) DEFAULT 'person' NOT NULL, 
    organization_id UUID, 
    affiliation_type VARCHAR(50), 
    role_title TEXT, 
    description TEXT, 
    activity_status VARCHAR(50) DEFAULT 'unknown' NOT NULL, 
    importance_score FLOAT DEFAULT '0.5' NOT NULL, 
    reliability_score FLOAT DEFAULT '0.5' NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL
);

CREATE INDEX ix_sources_source_type ON sources (source_type);

CREATE TABLE source_accounts (
    id UUID NOT NULL, 
    source_id UUID NOT NULL, 
    platform VARCHAR(50) NOT NULL, 
    handle TEXT, 
    url TEXT NOT NULL, 
    external_id TEXT, 
    is_primary BOOLEAN DEFAULT 'false' NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    last_checked_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_source_accounts_platform_url ON source_accounts (platform, url);

CREATE TABLE source_tags (
    source_id UUID NOT NULL, 
    tag_id UUID NOT NULL, 
    confidence FLOAT DEFAULT '1.0' NOT NULL, 
    assigned_by VARCHAR(50) DEFAULT 'manual' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (source_id, tag_id), 
    FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE CASCADE, 
    FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

CREATE TABLE signals (
    id UUID NOT NULL, 
    source_id UUID, 
    organization_id UUID, 
    title TEXT NOT NULL, 
    url TEXT NOT NULL, 
    canonical_url TEXT, 
    signal_type VARCHAR(50) DEFAULT 'other' NOT NULL, 
    abstract TEXT, 
    content TEXT, 
    published_at TIMESTAMP WITH TIME ZONE, 
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    language VARCHAR(10) DEFAULT 'en' NOT NULL, 
    external_id TEXT, 
    content_hash TEXT, 
    title_hash TEXT, 
    status VARCHAR(50) DEFAULT 'collected' NOT NULL, 
    raw_metadata JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE SET NULL, 
    FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
    UNIQUE (url)
);

CREATE INDEX ix_signals_published_at ON signals (published_at);

CREATE INDEX ix_signals_signal_type ON signals (signal_type);

CREATE INDEX ix_signals_status ON signals (status);

CREATE TABLE signal_analysis (
    id UUID NOT NULL, 
    signal_id UUID NOT NULL, 
    tldr TEXT, 
    summary TEXT, 
    why_it_matters TEXT, 
    technical_points TEXT[] DEFAULT '{}' NOT NULL, 
    limitations TEXT, 
    topic_tags TEXT[] DEFAULT '{}' NOT NULL, 
    entities TEXT[] DEFAULT '{}' NOT NULL, 
    importance_score FLOAT DEFAULT '0' NOT NULL, 
    novelty_score FLOAT DEFAULT '0' NOT NULL, 
    relevance_score FLOAT DEFAULT '0' NOT NULL, 
    confidence_score FLOAT DEFAULT '0' NOT NULL, 
    reading_priority VARCHAR(50), 
    model_name TEXT, 
    prompt_version TEXT, 
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (signal_id), 
    FOREIGN KEY(signal_id) REFERENCES signals (id) ON DELETE CASCADE
);

CREATE TABLE entities (
    id UUID NOT NULL, 
    name TEXT NOT NULL, 
    canonical_name TEXT NOT NULL, 
    entity_type VARCHAR(50) NOT NULL, 
    description TEXT, 
    homepage_url TEXT, 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_entities_canonical_name_type ON entities (canonical_name, entity_type);

CREATE INDEX ix_entities_entity_type ON entities (entity_type);

CREATE INDEX ix_entities_canonical_name ON entities (canonical_name);

CREATE TABLE entity_aliases (
    id UUID NOT NULL, 
    entity_id UUID NOT NULL, 
    alias TEXT NOT NULL, 
    alias_type VARCHAR(50) DEFAULT 'other' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(entity_id) REFERENCES entities (id) ON DELETE CASCADE, 
    UNIQUE (alias)
);

CREATE TABLE signal_entities (
    signal_id UUID NOT NULL, 
    entity_id UUID NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    mention_text TEXT, 
    confidence FLOAT DEFAULT '1.0' NOT NULL, 
    extracted_by TEXT, 
    model_name TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (signal_id, entity_id, role), 
    FOREIGN KEY(signal_id) REFERENCES signals (id) ON DELETE CASCADE, 
    FOREIGN KEY(entity_id) REFERENCES entities (id) ON DELETE CASCADE
);

CREATE INDEX ix_signal_entities_signal_id ON signal_entities (signal_id);

CREATE INDEX ix_signal_entities_entity_id ON signal_entities (entity_id);

CREATE TABLE entity_relations (
    id UUID NOT NULL, 
    subject_entity_id UUID NOT NULL, 
    relation_type VARCHAR(50) NOT NULL, 
    object_entity_id UUID NOT NULL, 
    source_signal_id UUID, 
    confidence FLOAT DEFAULT '1.0' NOT NULL, 
    extracted_by TEXT, 
    model_name TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(subject_entity_id) REFERENCES entities (id) ON DELETE CASCADE, 
    FOREIGN KEY(object_entity_id) REFERENCES entities (id) ON DELETE CASCADE, 
    FOREIGN KEY(source_signal_id) REFERENCES signals (id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX ix_entity_relations_unique ON entity_relations (subject_entity_id, relation_type, object_entity_id, source_signal_id);

CREATE INDEX ix_entity_relations_subject ON entity_relations (subject_entity_id);

CREATE INDEX ix_entity_relations_object ON entity_relations (object_entity_id);

CREATE TABLE embeddings (
    id UUID NOT NULL, 
    object_type VARCHAR(50) NOT NULL, 
    object_id UUID NOT NULL, 
    embedding_type VARCHAR(50) NOT NULL, 
    model_name TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_embeddings_unique ON embeddings (object_type, object_id, embedding_type, model_name);

CREATE TABLE pipeline_runs (
    id UUID NOT NULL, 
    run_type VARCHAR(50) NOT NULL, 
    status VARCHAR(50) DEFAULT 'running' NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    finished_at TIMESTAMP WITH TIME ZONE, 
    total_items INTEGER DEFAULT '0' NOT NULL, 
    success_items INTEGER DEFAULT '0' NOT NULL, 
    failed_items INTEGER DEFAULT '0' NOT NULL, 
    error_message TEXT, 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    PRIMARY KEY (id)
);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial') RETURNING alembic_version.version_num;

-- Running upgrade 0001_initial -> 0002_pgvector

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE embeddings ADD COLUMN vector TEXT;

ALTER TABLE embeddings ALTER COLUMN vector TYPE vector(1536) USING vector::vector(1536);

CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

UPDATE alembic_version SET version_num='0002_pgvector' WHERE alembic_version.version_num = '0001_initial';

-- Running upgrade 0002_pgvector -> 0003_sources_enrich

ALTER TABLE sources ADD COLUMN tier VARCHAR(10);

ALTER TABLE sources ADD COLUMN sector VARCHAR(50);

ALTER TABLE sources ADD COLUMN research_focus TEXT;

ALTER TABLE sources ADD COLUMN tier_reason TEXT;

ALTER TABLE sources ADD COLUMN notes TEXT;

ALTER TABLE sources ADD COLUMN source_authority VARCHAR(50);

ALTER TABLE sources ADD COLUMN last_tweet_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE sources ADD COLUMN avg_interval_days FLOAT;

ALTER TABLE sources ADD COLUMN arxiv_author_query TEXT;

ALTER TABLE sources ADD COLUMN affiliation_regex TEXT;

ALTER TABLE sources ADD COLUMN orcid TEXT;

ALTER TABLE sources ADD COLUMN twitter_url TEXT;

ALTER TABLE sources ADD COLUMN openalex_url TEXT;

ALTER TABLE sources ADD COLUMN scholar_url TEXT;

ALTER TABLE sources ADD COLUMN github_url TEXT;

ALTER TABLE sources ADD COLUMN personal_url TEXT;

ALTER TABLE sources ADD COLUMN arxiv_homepage_url TEXT;

CREATE INDEX ix_sources_tier ON sources (tier);

UPDATE alembic_version SET version_num='0003_sources_enrich' WHERE alembic_version.version_num = '0002_pgvector';

COMMIT;

