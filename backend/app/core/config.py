from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge"
    app_name: str = "AI Intelligence Knowledge Base"
    debug: bool = False
    api_prefix: str = "/api"

    # --- PostgreSQL connection pool -----------------------------------------
    # Tune for RDS instance class; t4g.micro can handle pool_size=5 comfortably.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30   # seconds to wait for a connection from the pool
    db_pool_recycle: int = 1800  # recycle connections older than 30 min

    # SSL mode for asyncpg:
    #   "disable"     – local docker / plain TCP
    #   "require"     – RDS (TLS required, no cert verification)
    #   "verify-full" – RDS with downloaded RDS CA bundle
    db_ssl_mode: str = "disable"

    # --- Embeddings (OpenAI-compatible provider) ----------------------------
    # Default: SiliconFlow BAAI/bge-m3 (1024 dims, free quota, strong Chinese).
    # Works with any OpenAI-compatible /embeddings endpoint — just change the
    # three vars below. Leave the key empty to disable semantic features.
    #   OpenAI   : base=https://api.openai.com/v1   model=text-embedding-3-small  dim=1536
    #   SiliconFlow: base=https://api.siliconflow.cn/v1 model=BAAI/bge-m3         dim=1024
    #   Zhipu    : base=https://open.bigmodel.cn/api/paas/v4 model=embedding-3    dim=1024/2048
    # IMPORTANT: embedding_dimensions MUST match the model AND the pgvector
    # column type (run set_embedding_dim.sql in Supabase when you change it).
    embedding_api_key: str | None = None
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024

    # --- LLM chat (DeepSeek, OpenAI-compatible API) -------------------------
    # Used for RAG question answering and analysis. Leave key empty to disable.
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: int = 60

    # --- Auth (JWT bearer login) --------------------------------------------
    # JWT signing secret — MUST be overridden in production via env JWT_SECRET.
    jwt_secret: str = "hh-research-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    # Seed initial users on startup (idempotent). Format: "user:pass,user2:pass2".
    # Defaults mirror the project's bootstrap accounts; change passwords in prod.
    seed_users: str = (
        "alex:alex0409,qiutian:qiutian123,haolin:haolin123,"
        "angela:angela123,aseed:aseed123"
    )

    # --- Redis (local: docker compose; prod: Amazon ElastiCache) ------------
    redis_url: str = "redis://localhost:6379/0"

    # --- Object storage (local: MinIO; prod: Amazon S3) ---------------------
    # Leave s3_endpoint_url empty / None in production to target real AWS S3.
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_bucket: str = "hh-research"
    s3_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
