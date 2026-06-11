-- ============================================================
-- build_entities.sql
-- 从 sources / organizations 表构建实体和关系图谱
-- 在 Supabase SQL Editor 中执行
-- 顺序：先跑 migration_0003_only.sql + import_sources.sql，再跑本文件
-- ============================================================

BEGIN;

-- ── 1. organizations → entities ───────────────────────────────────────────────
-- 每个组织创建一条 organization 类型实体（DISTINCT 保证无重复候选行）
INSERT INTO entities (id, name, canonical_name, entity_type, description, homepage_url, metadata)
SELECT DISTINCT ON (lower(trim(o.name)))
    gen_random_uuid(),
    o.name,
    lower(trim(o.name)),
    'organization',
    o.description,
    o.website_url,
    jsonb_build_object('org_type', o.org_type)
FROM organizations o
ORDER BY lower(trim(o.name))
ON CONFLICT (canonical_name, entity_type) DO UPDATE
    SET description  = COALESCE(EXCLUDED.description, entities.description),
        homepage_url = COALESCE(EXCLUDED.homepage_url, entities.homepage_url),
        metadata     = entities.metadata || EXCLUDED.metadata;


-- ── 2. sources → entities ─────────────────────────────────────────────────────
-- 先用 DISTINCT ON 去重（同名同类型取 tier 最高的那条），再 upsert
INSERT INTO entities (id, name, canonical_name, entity_type, description, homepage_url, metadata)
SELECT
    gen_random_uuid(),
    s.name,
    lower(trim(s.name)),
    s.etype,
    COALESCE(NULLIF(trim(s.description), ''), s.tier_reason),
    COALESCE(NULLIF(trim(s.personal_url), ''),
             NULLIF(trim(s.arxiv_homepage_url), ''),
             NULLIF(trim(s.twitter_url), '')),
    jsonb_strip_nulls(jsonb_build_object(
        'tier',             s.tier,
        'sector',           s.sector,
        'research_focus',   s.research_focus,
        'source_authority', s.source_authority,
        'twitter_url',      s.twitter_url,
        'github_url',       s.github_url,
        'scholar_url',      s.scholar_url,
        'orcid',            s.orcid,
        'activity_status',  s.activity_status,
        'avg_interval_days',s.avg_interval_days
    ))
FROM (
    -- deduplicate: per (canonical_name, entity_type), keep the row with the
    -- most informative tier (P0+ first, then P1, P2, P3, others)
    SELECT DISTINCT ON (lower(trim(name)), etype)
        name, description, tier_reason, personal_url, arxiv_homepage_url,
        twitter_url, tier, sector, research_focus, source_authority,
        github_url, scholar_url, orcid, activity_status, avg_interval_days,
        CASE WHEN source_type = 'person' THEN 'person' ELSE 'organization' END AS etype
    FROM sources
    ORDER BY
        lower(trim(name)),
        CASE WHEN source_type = 'person' THEN 'person' ELSE 'organization' END,
        CASE tier
            WHEN 'P0+' THEN 1 WHEN 'P1' THEN 2
            WHEN 'P2'  THEN 3 WHEN 'P3' THEN 4
            ELSE 5
        END
) s
ON CONFLICT (canonical_name, entity_type) DO UPDATE
    SET description  = COALESCE(EXCLUDED.description, entities.description),
        homepage_url = COALESCE(EXCLUDED.homepage_url, entities.homepage_url),
        metadata     = entities.metadata || EXCLUDED.metadata,
        updated_at   = now();


-- ── 3. WORKS_AT / AFFILIATED_WITH 关系 ───────────────────────────────────────
-- person source → organization entity  : WORKS_AT
-- org source    → organization entity  : AFFILIATED_WITH
INSERT INTO entity_relations
    (id, subject_entity_id, relation_type, object_entity_id, confidence, extracted_by)
SELECT DISTINCT ON (es.id, eo.id)
    gen_random_uuid(),
    es.id,
    CASE WHEN s.source_type = 'person' THEN 'WORKS_AT' ELSE 'AFFILIATED_WITH' END,
    eo.id,
    0.95,
    'csv_import'
FROM sources s
JOIN organizations org ON s.organization_id = org.id
JOIN entities es ON lower(trim(es.name)) = lower(trim(s.name))
    AND es.entity_type = CASE WHEN s.source_type = 'person' THEN 'person' ELSE 'organization' END
JOIN entities eo ON lower(trim(eo.name)) = lower(trim(org.name))
    AND eo.entity_type = 'organization'
WHERE s.organization_id IS NOT NULL
  AND es.id IS NOT NULL
  AND eo.id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM entity_relations r
      WHERE r.subject_entity_id = es.id
        AND r.relation_type = CASE WHEN s.source_type = 'person' THEN 'WORKS_AT' ELSE 'AFFILIATED_WITH' END
        AND r.object_entity_id = eo.id
        AND r.source_signal_id IS NULL
  );


-- ── 4. FOCUSES_ON 关系（研究方向 → topic 实体） ───────────────────────────────
-- 将 research_focus 拆成独立 topic 实体，建 FOCUSES_ON 关系
-- 先创建 topic 类型实体（用子查询先 DISTINCT 再 INSERT，避免重复候选行）
INSERT INTO entities (id, name, canonical_name, entity_type, description, metadata)
SELECT gen_random_uuid(), topic_name, lower(topic_name), 'topic', NULL, '{}'::jsonb
FROM (
    SELECT DISTINCT trim(topic) AS topic_name
    FROM sources s,
         unnest(string_to_array(s.research_focus, ',')) AS topic
    WHERE s.research_focus IS NOT NULL
      AND trim(topic) <> ''
) deduped
ON CONFLICT (canonical_name, entity_type) DO NOTHING;

-- 再建 FOCUSES_ON 关系（先 unnest 到子查询，外层再 JOIN entities）
INSERT INTO entity_relations
    (id, subject_entity_id, relation_type, object_entity_id, confidence, extracted_by)
SELECT DISTINCT ON (es.id, et.id)
    gen_random_uuid(),
    es.id,
    'FOCUSES_ON',
    et.id,
    0.9,
    'csv_import'
FROM (
    SELECT lower(trim(s.name)) AS src_name, trim(tp) AS topic_name
    FROM sources s
    CROSS JOIN unnest(string_to_array(s.research_focus, ',')) AS tp
    WHERE s.research_focus IS NOT NULL
      AND trim(tp) <> ''
) st
JOIN entities es ON lower(trim(es.name)) = st.src_name
    AND es.entity_type IN ('person', 'organization')
JOIN entities et ON lower(trim(et.name)) = lower(st.topic_name)
    AND et.entity_type = 'topic'
WHERE NOT EXISTS (
    SELECT 1 FROM entity_relations r
    WHERE r.subject_entity_id = es.id
      AND r.relation_type = 'FOCUSES_ON'
      AND r.object_entity_id = et.id
      AND r.source_signal_id IS NULL
);


-- ── 5. 统计输出 ────────────────────────────────────────────────────────────────
SELECT
    (SELECT count(*) FROM entities WHERE entity_type = 'person')       AS person_entities,
    (SELECT count(*) FROM entities WHERE entity_type = 'organization') AS org_entities,
    (SELECT count(*) FROM entities WHERE entity_type = 'topic')        AS topic_entities,
    (SELECT count(*) FROM entity_relations WHERE relation_type = 'WORKS_AT')        AS works_at_rels,
    (SELECT count(*) FROM entity_relations WHERE relation_type = 'AFFILIATED_WITH') AS affiliated_rels,
    (SELECT count(*) FROM entity_relations WHERE relation_type = 'FOCUSES_ON')      AS focuses_on_rels;

COMMIT;
