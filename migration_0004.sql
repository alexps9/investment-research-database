-- ============================================================
-- migration_0004.sql
-- Daily Boost + 投融资 两张新表（在 Supabase SQL Editor 执行）
-- 幂等：可重复运行
-- ============================================================

-- 1. 每日精选摘要
CREATE TABLE IF NOT EXISTS daily_digests (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_date   varchar(10) NOT NULL UNIQUE,
    summary       text,
    highlights    jsonb NOT NULL DEFAULT '[]',
    signal_count  integer NOT NULL DEFAULT 0,
    model_name    text,
    created_at    timestamptz DEFAULT now(),
    updated_at    timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_daily_digests_date ON daily_digests (digest_date);

-- 2. 投融资事件
CREATE TABLE IF NOT EXISTS funding_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    text NOT NULL,
    organization_id uuid REFERENCES organizations(id) ON DELETE SET NULL,
    round           varchar(50),
    amount_usd      double precision,
    amount_raw      text,
    currency        varchar(10),
    investors       jsonb NOT NULL DEFAULT '[]',
    sector          varchar(100),
    announced_at    timestamptz,
    source_url      text,
    description     text,
    extracted_by    text,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_funding_announced_at ON funding_events (announced_at);
CREATE INDEX IF NOT EXISTS ix_funding_round ON funding_events (round);
CREATE INDEX IF NOT EXISTS ix_funding_sector ON funding_events (sector);

-- 3. 记录迁移版本（Alembic）
UPDATE alembic_version SET version_num = '0004_daily_funding';
