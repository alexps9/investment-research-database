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
  `entities`, `search`, `funding`, `daily`, `dashboard`, `notify`, `websearch`)
  over a shared `tools/_client.py`. `tools/__init__.py` exposes `READONLY_TOOLS`,
  `WRITE_TOOLS`, `ALL_TOOLS`. `notify` (Feishu push) and `websearch` (free DDG
  search + primary-source lookup) are dependency-light tools used by the alert
  agent.
- `skills/` — one **directory per skill**, named by function; `skills/__init__.py`
  exposes `SKILLS`. `signal_triage` is a deterministic skill (tier/engagement
  scoring, cross-language triangulation, cluster-dedup; jieba optional).
- `agent/` — one **directory per agent**, each exposing a `build_<agent>()`
  factory; `agent/team.py` assembles the chat team.
  - `agent/data_agent/` — KB read/write/analysis specialist (group-chat).
  - `agent/alert_agent/` — real-time AI-signal triage. Refactored from a former
    standalone `alert/` pipeline: deterministic fetch (`fetcher.py`) + triage
    (`skills.signal_triage`) + prefilter (`headline/`), then an AutoGen agent does
    judge → summary → cross-verify → push (`tools.notify`) → persist
    (`tools.signals.create_signal`). Driven per-signal by
    `agent/alert_agent/pipeline.py` (not a round-robin chat participant).
    - `agent/alert_agent/headline/` — **vendored** HH-Research v8.0
      `HeadlineClassifier` (the prefilter brain), extracted from
      jingruzhao103-bit/HH-Research `daily-digest/src/hh_research`
      (`headline_classifier.py` + `canonical_entity.py` + a zero-dependency
      `Signal` dataclass). Self-contained & offline — no external package on
      PYTHONPATH. It scores a signal on 5 dims and tests 8 strong constraints
      using the P0+/P0 names in `config/p0_whitelist.yml`.

### Lesson: refactoring a standalone pipeline into the agent system

When merging external pipeline code (the `add-alert-agent` branch), split it by
responsibility instead of copying wholesale:
- **side-effecting atoms** (push, web search, KB write) → `tools/` (async, never
  raise, return `{"ok"|"error": ...}`).
- **deterministic, tuned logic** (scoring, clustering, dedup) → `skills/` (keep it
  pure & cheap; make heavy deps like jieba optional with a fallback).
- **LLM reasoning** (judge/summarise/review prompts) → the agent's
  `system_message`, driven by the shared `agent/config.get_model_client()`
  (DeepSeek) — drop provider-specific calls (the old code used AWS Bedrock).
- **source-specific plumbing & config** (feed fetchers, sqlite dedup, whitelists)
  → stays inside the agent package as infrastructure.
- **upstream deps that were "optional/degrade gracefully"** (here the
  `HeadlineClassifier` prefilter) → **vendor** them in (e.g.
  `agent/alert_agent/headline/`) so the feature actually works out of the box;
  trim heavy deps (pydantic `Signal` → dataclass) and rewire relative imports.

### Lesson: Windows file encoding

This repo runs on Windows (cp936 default). **Always pass `encoding="utf-8"` to
`open()`** when reading files with Chinese content (YAML configs, whitelists,
prompts). Without it, `open()` uses the locale codec and raises
`UnicodeDecodeError`; if that's swallowed by a broad `except`, configs silently
load empty (the alert whitelist did exactly this → prefilter degraded to all
"borderline"). The alert `fetcher.py`/`prefilter.py` reads are now explicit UTF-8.

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
