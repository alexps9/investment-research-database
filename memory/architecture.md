# Architecture

```
┌──────────────┐      HTTPS        ┌─────────────────────┐
│  Frontend    │  ───────────────► │   Backend (FastAPI) │
│  Next.js     │   /api/*          │   app/main.py       │
│  (Vercel)    │ ◄───────────────  │                     │
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

## Frontend structure (`frontend/src/`)

Next.js 14 app router. Pages are consolidated (do NOT recreate the old split pages):

- `app/dashboard` — stats + recent activity.
- `app/data` — **Data Hub**: tabbed Sources / Signals / Entities (merged). Reads
  `?tab=`. Per-row checkboxes + client-side CSV export (`lib/csv.ts`).
- `app/explore` — **Explore**: one page with three modes — AI Q&A (`/ai/ask`),
  semantic search (`/ai/search`), keyword search (`/search`). Results deep-link to
  the entity Wiki.
- `app/graph` — knowledge graph; search box does semantic (`/ai/search`) locate
  with substring fallback; side panel links to Wiki.
- `app/daily`, `app/funding` — Daily Boost & funding tracker.
- `app/wiki/entities/[id]` — entity Wiki detail (the only dynamic route).
- Legacy routes `app/{sources,signals,entities,wiki,ask}` are thin **client
  redirects** to the merged pages.
- Shared: `lib/api.ts` (fetch client), `lib/i18n.tsx` (zh/en), `lib/types.ts`,
  `lib/csv.ts`, `components/ui/*` (Card, Badge, Modal, PageHeader).

## Agent / tools / skills layout

- `tools/` — one **package per functional domain** (`sources`, `signals`,
  `entities`, `search`, `funding`, `daily`, `dashboard`) over a shared
  `tools/_client.py`. `tools/__init__.py` exposes `READONLY_TOOLS`, `WRITE_TOOLS`,
  `ALL_TOOLS`.
- `skills/` — one **directory per skill**, named by function; `skills/__init__.py`
  exposes `SKILLS`.
- `agent/` — one **directory per agent** (e.g. `agent/data_agent/`), each exposing
  a `build_<agent>()` factory; `agent/team.py` assembles the team.

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
