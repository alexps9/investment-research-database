# Architecture

```
┌──────────────┐      HTTPS        ┌─────────────────────┐
│  Frontend    │  ───────────────► │   Backend (FastAPI) │
│  Next.js     │   /api/*          │   app/main.py       │
│  (GH Pages)  │ ◄───────────────  │                     │
└──────────────┘                   │   routers/          │
                                   │   services/ (llm,   │
┌──────────────┐   MCP (http)      │     semantic, daily)│
│  MCP server  │ ──────────────►   │   repositories/     │
│ mcp_server/  │   /api/*          │   models/ (ORM)     │
└──────────────┘                   └─────────┬───────────┘
                                            │ asyncpg
┌──────────────┐   tools/ (http)            ▼
│ agent/       │ ──────────────►   ┌─────────────────────┐
│ (AutoGen)    │   /api/*          │ PostgreSQL+pgvector │
└──────────────┘                   │   (Supabase)        │
                                   └─────────────────────┘
              external LLM/embeddings: DeepSeek (chat) · SiliconFlow bge-m3 (embed)
```

## Key principle

**The FastAPI backend is the single source of truth and the only component that
touches PostgreSQL.** Everything else (frontend, MCP server, agents/tools) goes
through `/api/*`. This keeps validation, business logic and DB access in one
place and makes the other layers thin and replaceable.

## Backend layering (`backend/app/`)

- `main.py` — app + router registration + CORS.
- `routers/` — HTTP endpoints (thin; validate + delegate).
  `sources, signals, entities, search, wiki, runs, dashboard, graph, export,
  ai, daily, funding`.
- `schemas/` — Pydantic request/response models.
- `repositories/` — DB access objects (`SourceRepo`, `SignalRepo`, `EntityRepo`…).
- `services/` — cross-cutting logic: `llm.py` (chat + embeddings clients),
  `semantic.py` (indexing + vector search), `daily.py` (digest generation).
- `models/` — SQLAlchemy ORM (also defines `VALID_RELATION_TYPES`).
- `core/config.py` — pydantic-settings (env-driven).
- `alembic/` — migrations (offline SQL is applied manually in Supabase).

## Data flow examples

- **Semantic search**: query → `services/llm.embed_text` (SiliconFlow) → pgvector
  cosine search in `embeddings` → hits.
- **RAG ask**: question → semantic search for context → `services/llm.chat`
  (DeepSeek) → grounded answer + sources.
- **Daily Boost**: pick top signals in window → optional LLM summary → upsert
  `daily_digests`.

## External providers (env-configured)

- Embeddings: OpenAI-compatible; default **SiliconFlow `BAAI/bge-m3`, 1024 dims**.
  The `embeddings.vector` column dimension MUST match (`set_embedding_dim.sql`).
- Chat / RAG: **DeepSeek `deepseek-chat`** (OpenAI-compatible).
