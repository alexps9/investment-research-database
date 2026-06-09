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

    # --- pgvector -----------------------------------------------------------
    # Dimension must match the embedding model used by the pipeline.
    # 1536 = OpenAI text-embedding-3-small / ada-002
    # 3072 = OpenAI text-embedding-3-large
    embedding_dimensions: int = 1536

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
