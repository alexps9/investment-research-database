-- Research Studio: persisted deep-research sessions (migration 0010)
CREATE TABLE IF NOT EXISTS research_sessions (
    id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    phase VARCHAR(50),
    pct INTEGER NOT NULL DEFAULT 0,
    agent_job_id TEXT,
    brief TEXT,
    subtopics JSONB NOT NULL DEFAULT '[]',
    report TEXT,
    sources JSONB NOT NULL DEFAULT '[]',
    kb_sources JSONB NOT NULL DEFAULT '[]',
    scope JSONB,
    industry JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_research_sessions_created_at ON research_sessions (created_at);
CREATE INDEX IF NOT EXISTS ix_research_sessions_status ON research_sessions (status);
