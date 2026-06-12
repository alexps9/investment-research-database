-- ============================================================
-- set_embedding_dim.sql
-- 切换 embedding 向量维度（在 Supabase SQL Editor 执行）
--
-- 当你更换 embedding 模型时运行本文件，使 pgvector 列维度与模型一致：
--   SiliconFlow BAAI/bge-m3        -> 1024  (默认)
--   OpenAI text-embedding-3-small  -> 1536
--   Zhipu  embedding-3             -> 1024 或 2048
--
-- 注意：改维度会清空已有向量（embeddings 表数据），改完后到前端
--       「智能问答」页点「重建索引」重新生成即可。
-- ============================================================

BEGIN;

-- 1. 清空旧向量（维度不同无法保留）
TRUNCATE TABLE embeddings;

-- 2. 删除依赖该列的向量索引
DROP INDEX IF EXISTS ix_embeddings_vector_ivfflat;

-- 3. 修改向量维度（★ 如换其他模型，把 1024 改成对应维度）
ALTER TABLE embeddings
    ALTER COLUMN vector TYPE vector(1024) USING NULL;

-- 4. 重建余弦相似度索引
CREATE INDEX IF NOT EXISTS ix_embeddings_vector_ivfflat
    ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

COMMIT;
