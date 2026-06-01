# AI Intelligence Knowledge Base

> Signal collection and knowledge management system for AI researchers.

**Knowledge chain:** Source → Signal → Entity → Relation → Wiki / Search

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│              Next.js 14  (localhost:3000)                   │
│   /dashboard  /sources  /signals  /entities  /wiki  /graph  │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP  /api/*  (rewrite proxy)
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                          │
│                   (localhost:8000)                          │
│                                                             │
│  Routers → Repositories → SQLAlchemy 2.x (async)           │
│                                                             │
│  /sources   /signals   /entities   /search                  │
│  /wiki      /graph     /dashboard  /runs                    │
└────────────────────────┬────────────────────────────────────┘
                         │  asyncpg
┌────────────────────────▼────────────────────────────────────┐
│                   PostgreSQL 16                             │
│                                                             │
│  organizations   sources   source_accounts   tags           │
│  signals   signal_analysis   signal_entities                │
│  entities   entity_aliases   entity_relations               │
│  embeddings (pgvector-ready)   pipeline_runs                │
└─────────────────────────────────────────────────────────────┘

  Other agents (Claude / Cursor / custom) ──MCP──► mcp_server
  (stdio or streamable-http)                          │ HTTP /api/*
                                                      ▼
                                              FastAPI backend
```

```
Data flow
─────────
External sources ──► Signal (evidence) ──► Entity (knowledge node)
                                                  │
                                           EntityRelation
                                                  │
                                           Wiki / Graph
```

---

## Quick Start

### Docker Compose (recommended)

```bash
cp .env.example backend/.env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

On first run, the backend automatically runs migrations, loads seed data, then starts the server.

---

### Local Development

**Prerequisites:** Python 3.12+, Node.js 20+, PostgreSQL 16

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env        # edit DB connection as needed
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry, CORS, router registration
│   │   ├── database.py        # Engine & session
│   │   ├── models/            # SQLAlchemy ORM (13 tables)
│   │   ├── schemas/           # Pydantic v2 request/response
│   │   ├── repositories/      # Data access layer
│   │   ├── routers/           # Route handlers
│   │   └── core/config.py     # Settings from env vars
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest suite
│   ├── seed.py                # Seed script
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/               # Next.js App Router pages
│       ├── components/        # Sidebar + UI components
│       └── lib/               # API client & TypeScript types
├── mcp_server/                # MCP server exposing the KB to other agents
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Resource | Endpoints |
|----------|-----------|
| Sources | `GET/POST /api/sources` · `PATCH/DELETE /api/sources/{id}` · `POST .../accounts` · `POST .../tags` |
| Signals | `GET/POST /api/signals` · `PATCH /api/signals/{id}` · `POST .../analysis` · `GET .../related` |
| Entities | `GET/POST /api/entities` · `PATCH /api/entities/{id}` · `POST .../aliases` · `GET/POST .../relations` |
| Search | `GET /api/search?q=` |
| Wiki | `GET /api/wiki/entities/{id}` |
| Graph | `GET /api/graph/relations` |
| Dashboard | `GET /api/dashboard/stats` · `GET .../latest-signals` · `GET .../latest-runs` |
| Runs | `GET /api/runs` · `POST /api/runs/mock` |

Full interactive docs: http://localhost:8000/docs

---

## Frontend Pages

| Path | Description |
|------|-------------|
| `/dashboard` | Stats + latest signals + pipeline runs |
| `/sources` | Source management table |
| `/signals` | Signal card list |
| `/entities` | Entity table with wiki links |
| `/wiki` | Global search (grouped by entity / signal / source) |
| `/wiki/entities/[id]` | Entity wiki detail (relations, signals, aliases) |
| `/graph-lite` | Relation graph (nodes + edges table) |

---

## Tests

```bash
cd backend

# Unit tests — no DB required
pytest tests/test_models.py -v

# API smoke tests — requires running backend
pytest tests/test_api.py -v
```

---

## MCP Server (for other agents)

The knowledge base is also exposed over the **Model Context Protocol**, so other
agents (Claude Desktop, Cursor, custom agents) can search, read Wiki profiles,
and contribute signals/entities. It wraps the same FastAPI backend over HTTP.

```bash
cd mcp_server
pip install -r requirements.txt

# stdio (local clients)
python server.py

# streamable-http (remote / multi-agent) → http://localhost:8765/mcp
MCP_TRANSPORT=streamable-http python server.py
```

Tools include `search_knowledge`, `get_entity_wiki`, `list_signals`,
`create_signal`, `add_entity_relation`, etc. Full tool list and client config:
see [mcp_server/README.md](./mcp_server/README.md).

---

## Database Schema (13 tables)

```
organizations ──< sources ──< source_accounts
                    │
                    └──< source_tags >── tags

signals ──< signal_analysis
   │
   └──< signal_entities >── entities ──< entity_aliases
                                │
                         entity_relations (subject → type → object)

embeddings   pipeline_runs
```

---


中文文档：[README.zh.md](./README.zh.md)
