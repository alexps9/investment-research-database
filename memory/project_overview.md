# Project Overview — HH-Research

HH-Research is an **AI research-intelligence knowledge base**. It tracks signal
sources (researchers, labs, companies, feeds), ingests signals (papers, tweets,
blogs, model/GitHub releases, news), extracts a knowledge graph of entities and
relations, and layers semantic search, RAG Q&A, a daily highlight digest, and an
investment/financing tracker on top.

## What it does

- **Sources**: curated people/orgs/feeds we monitor, with tier (P0+/P1/P2/P3),
  sector, activity status, importance & reliability scores.
- **Signals**: evidence items (unique by URL) with optional LLM analysis
  (tldr, importance score, reading priority, topic tags).
- **Entities & graph**: canonical entities (person/org/model/method/dataset/…)
  connected by typed relations (WORKS_AT, AUTHORED, USES, …).
- **Wiki**: per-entity profile aggregating aliases, relations and related signals.
- **Semantic search + RAG** (`/ai/*`): pgvector embeddings + DeepSeek chat.
- **Daily Boost** (`/daily/*`): auto-selects the day's top signals and writes a
  summary digest.
- **Funding** (`/funding/*`): investment/financing events + trend aggregation.

## Components

| Component | Path | Stack | Hosting |
|-----------|------|-------|---------|
| Backend API | `backend/` | FastAPI, SQLAlchemy async, Alembic | Hugging Face Space (Docker) |
| Frontend | `frontend/` | Next.js 14, React 18, Tailwind | Vercel |
| MCP server | `mcp_server/` | `mcp` SDK, streamable-http | Hugging Face Space (Docker) |
| Multi-agent | `agent/` | AutoGen 0.7 | run locally / any host |
| Database | (Supabase) | PostgreSQL 16 + pgvector | Supabase |

> Frontend is live at https://investment-research-database.vercel.app/ (Vercel
> auto-deploys on push to the `public` repo's `main`). GitHub Pages is **not** used.

## Repo map

```
backend/      FastAPI app (routers, models, schemas, repositories, services, alembic)
frontend/     Next.js app (app router, components, lib) — merged Data Hub + Explore
mcp_server/   MCP wrapper over the backend REST API
agent/        AutoGen multi-agent system; one dir per agent (data_agent/, alert_agent/)
tools/        Atomic KB tools; one package per domain (sources/signals/…/notify/websearch)
skills/       Composed workflows; one dir per skill (…/signal_triage), built on tools/
memory/       This documentation set (for humans + code agents)
migration_*.sql, set_embedding_dim.sql   Supabase manual DB migrations
```

See also: [architecture.md](architecture.md), [data_model.md](data_model.md),
[api_reference.md](api_reference.md), [deployment.md](deployment.md).
