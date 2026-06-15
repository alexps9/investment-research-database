# AGENTS.md

Agent-friendly context for the **HH-Research** repo. Read this first, then the
docs in [`memory/`](memory/README.md). Keep answers grounded in this file and the
actual code — do not invent endpoints, columns or env vars.

## TL;DR

HH-Research is an **AI research-intelligence knowledge base**: it tracks signal
sources, ingests signals (papers/tweets/releases/news), builds a knowledge graph
of entities & relations, and adds semantic search, RAG Q&A, a daily digest, and a
funding tracker. A FastAPI backend over PostgreSQL (Supabase + pgvector) is the
single source of truth; a Next.js frontend, an MCP server, and an AutoGen
multi-agent system all talk to it over `/api/*`.

## Repo layout

```
backend/      FastAPI app — the ONLY component that touches the database
frontend/     Next.js 14 static site
mcp_server/   MCP (Model Context Protocol) wrapper over the backend REST API
agent/        AutoGen 0.7 multi-agent system (data_agent first)
tools/        Atomic KB tools (1 async fn per backend endpoint)
skills/       Composed workflows built on tools/
memory/       Project docs (overview / architecture / data model / api / deploy)
*.sql         Supabase manual migrations
```

## Golden rules

1. **Backend owns the database.** Never add direct DB access in frontend, MCP,
   tools, skills, or agents — call `/api/*`. New persistence logic goes in
   `backend/app/{models,schemas,repositories,routers}`.
2. **Layering in the backend**: router (thin) → repository/service → model.
   Put DB queries in `repositories/`, cross-cutting logic in `services/`.
3. **Keep the layers in sync**: an ORM change usually needs a Pydantic schema
   change (`backend/app/schemas`), a frontend type (`frontend/src/lib/types.ts`),
   and a migration. Update [`memory/data_model.md`](memory/data_model.md) too.
4. **Migrations are manual on Supabase.** Add an Alembic revision under
   `backend/alembic/versions/` AND a runnable `migration_*.sql` for the SQL editor.
5. **Tools vs skills**: a *tool* is atomic (1 endpoint); a *skill* composes tools
   into a workflow returning human-readable output. Register new tools in
   `tools/__init__.py` and new skills in `skills/__init__.py`.
6. **Don't commit secrets.** Use env vars / `.env` (gitignored). Examples live in
   `*.env.example`. Never hardcode API keys or tokens.

## How to build & run

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload                # http://localhost:8000  (/docs, /health)

# Frontend
cd frontend && npm install && npm run dev     # http://localhost:3000

# MCP server (needs backend running)
cd mcp_server && pip install -r requirements.txt
MCP_TRANSPORT=streamable-http python server.py

# Multi-agent (from repo root)
pip install -r agent/requirements.txt
python -m agent.main "Audit source data quality"
```

## Conventions

- **Python**: 3.12, type hints + docstrings on public functions, `async` for IO.
  4-space indent. Tools/skills return JSON-serialisable values and never raise on
  HTTP errors — they return `{"error": ...}`.
- **TypeScript/Next.js**: function components, Tailwind, types in
  `frontend/src/lib/types.ts`, API calls via `frontend/src/lib/api.ts`.
  i18n strings go in `frontend/src/lib/i18n.tsx` (both `zh` and `en`).
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
  Only commit when asked; never force-push shared branches without confirmation.
- **Relation types** are an allowlist — see `VALID_RELATION_TYPES` in
  `backend/app/models/__init__.py`; the backend rejects others with 422.

## Key facts an agent needs

- API base: `${KB_API_BASE_URL}` + `/api` (default `http://localhost:8000`).
  Hosted backend: `https://Alexps9yyy-hh-research-api.hf.space`.
- Embeddings: OpenAI-compatible, default **SiliconFlow `BAAI/bge-m3` (1024 dims)**;
  the `embeddings.vector` column dim must match (`set_embedding_dim.sql`).
- Chat/RAG: **DeepSeek `deepseek-chat`**.
- Semantic search / RAG / funding / daily features require their env keys and the
  `migration_0004.sql` tables; otherwise those endpoints return errors while the
  rest of the API keeps working.

## Where to look

- Endpoints & params → [`memory/api_reference.md`](memory/api_reference.md)
- Tables & enums → [`memory/data_model.md`](memory/data_model.md)
- How it's deployed → [`memory/deployment.md`](memory/deployment.md)
- Tool/skill catalog → [`tools/`](tools), [`skills/README.md`](skills/README.md)
