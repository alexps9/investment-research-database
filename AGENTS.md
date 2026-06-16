# AGENTS.md

Agent-friendly context for the **HH-Research** repo. Read this first, then the
docs in [`memory/`](memory/README.md). Keep answers grounded in this file and the
actual code — do not invent endpoints, columns or env vars.

## TL;DR

HH-Research is an **AI research-intelligence knowledge base**: it tracks signal
sources, ingests signals (papers/tweets/releases/news), builds a knowledge graph
of entities & relations, and adds semantic search, RAG Q&A, a daily digest, and a
funding tracker. A FastAPI backend over PostgreSQL (Supabase + pgvector) is the
single source of truth; a Next.js frontend, an MCP server, and a LangGraph
multi-agent system all talk to it over `/api/*`.

## Repo layout

```
backend/      FastAPI app — the ONLY component that touches the database
frontend/     Next.js 14 app (deployed on Vercel) — merged Data Hub + Explore pages
mcp_server/   MCP (Model Context Protocol) wrapper over the backend REST API
agent/        LangGraph multi-agent system — ingestion/analysis/entity/alert/digest/data
tools/        Atomic KB tools — one package per domain (sources/signals/…/notify/websearch)
skills/       Composed workflows — one dir per skill (…/signal_triage, headline_selection); skills/headline/ is a shared vendored support pkg
memory/       Project docs (overview / architecture / data model / api / deploy)
*.sql         Supabase manual migrations
```

Directory conventions (mirror each other): **tools** = one package per functional
domain; **skills** = one directory per skill (named by function); **agents** = one
directory per agent (named by agent), each exposing a `build_<name>()` factory.

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
5. **Tools vs skills**: a *tool* is atomic (1 endpoint), lives in its domain
   package (e.g. `tools/sources/`); a *skill* composes tools into a workflow
   returning human-readable output and lives in its own dir (e.g.
   `skills/daily_brief/`). Register new tools in `tools/__init__.py`
   (`READONLY_TOOLS`/`WRITE_TOOLS`) and new skills in `skills/__init__.py` (`SKILLS`).
   Add a new agent as `agent/<name>/` and wire it into `agent/graph.py`. Tools are
   async, must never raise (return `{"ok"|"error": ...}`), and side-effecting ones
   (e.g. `tools/notify`) go in `WRITE_TOOLS`. LangGraph pipeline:
   **Ingestion → Analysis → (Entity + Alert)**; **Digest** runs daily on analyzed
   signals; **Data Agent** is read-only Q&A via HTTP `/qa`. When integrating an
   external pipeline, split it: side-effecting atoms → `tools/`, deterministic tuned
   logic → `skills/`, LLM prompts → agent node modules, source-specific plumbing →
   the agent package. See `agent/ingestion_agent/`, `agent/analysis_agent/`,
   `agent/entity_agent/`, `agent/alert_agent/`, `agent/digest_agent/`,
   `agent/data_agent/` as the models.
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
python -m agent.run pipeline              # full LangGraph pipeline
python -m agent.service                   # HTTP Q&A on :9000
curl -X POST http://localhost:9000/qa -H 'Content-Type: application/json' -d '{"question":"..."}'
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
- **Auth**: JWT bearer login (`/api/auth/login`, `/api/auth/me`); pbkdf2 hashing
  + PyJWT in `backend/app/core/security.py`. The **frontend** requires login
  (`AuthProvider` + `AppGate` gate, token in `localStorage`, sent on every
  request by `frontend/src/lib/api.ts`). Data endpoints are **not** bearer-gated
  so MCP/agents keep working. Initial users are seeded idempotently on startup
  from the `SEED_USERS` env (`backend/app/core/seed.py`).
- **Concurrency / isolation**: the async engine runs at **REPEATABLE READ**
  (PostgreSQL snapshot isolation — no dirty/non-repeatable/phantom reads).
  Write/write conflicts surface as 40001/40P01 → mapped to a retryable **409**
  in `app.main`. Get-or-create paths (tags/entities) are race-safe (savepoint +
  IntegrityError recovery); manual entity relations have a partial unique index
  (`source_signal_id IS NULL`) and `add_relation` is idempotent — no dup edges.

## Key facts an agent needs

- API base: `${KB_API_BASE_URL}` + `/api` (default `http://localhost:8000`).
  Hosted backend: `https://Alexps9yyy-hh-research-api.hf.space`.
- Embeddings: OpenAI-compatible, default **SiliconFlow `BAAI/bge-m3` (1024 dims)**;
  the `embeddings.vector` column dim must match (`set_embedding_dim.sql`).
- Chat/RAG: an OpenAI-compatible **LiteLLM gateway** (`*_BASE_URL=http://litellm:4000/v1`,
  model `claude-sonnet-4-6`). Primary = **AWS Bedrock Claude** (egressed through an
  overseas SS proxy, since Anthropic geo-blocks CN IPs); **fallback = DeepSeek-V4**
  (`api.deepseek.com`, direct via `NO_PROXY`) so Q&A keeps working when the proxy /
  Bedrock is down. App code is provider-agnostic — it only ever sees the gateway.
- Semantic search / RAG / funding / daily features require their env keys and the
  `migration_0004.sql` tables; otherwise those endpoints return errors while the
  rest of the API keeps working.

## Deployment & frontend notes

- **Frontend deploys to Vercel** (live: https://investment-research-database.vercel.app/),
  not GitHub Pages. Deploy = `git push public database/v1.0:main --force`; Vercel
  auto-builds. A `deploy-pages.yml` workflow exists but is **not** the deploy path — ignore it.
- **Vercel → Tencent backend proxy**: `frontend/vercel.json` rewrites `/api/:path*`
  to the HTTP-only Tencent backend (`http://110.40.131.38:8000`), avoiding mixed-content.
  `next.config.js` only enables `rewrites()` in dev and only sets `trailingSlash`
  for GitHub-Pages builds (`NEXT_PUBLIC_BASE_PATH`), else the 308s break the proxy.
- Backend + MCP deploy to Hugging Face Spaces via `git subtree split` (see
  [`memory/deployment.md`](memory/deployment.md)).
- **Frontend pages are merged** — `/data` (Sources/Signals/Entities tabs, `?tab=`)
  and `/explore` (AI Q&A + semantic + keyword search). Old routes
  (`/sources /signals /entities /wiki /ask`) are client redirects; don't recreate
  them as full pages. Selective CSV export is client-side (`frontend/src/lib/csv.ts`).
- **Row selection + bulk actions** live in `components/data/selection.tsx`
  (`useRowSelection`, `Checkbox`, `ExportBar`, `bulkDelete`). The three checkbox
  lists (person Sources / Signals / Entities) wire `onDeleteSelected` into
  `ExportBar` for **bulk delete**; `bulkDelete()` deletes sequentially (REPEATABLE
  READ ⇒ avoid concurrent-write 409s) and reports per-id success/failure.
- **AI search & Q&A return entities only** (`/ai/search?types=entity`, `/ai/ask`
  defaults `object_types=["entity"]`) — source rows duplicate entities. The Explore
  UI shows these hits under the "信源 / Source" label. The Q&A system prompt forbids
  exposing retrieval jargon ("context") and keeps "no info" replies to one sentence.
- **Dashboard / graph labels**: the 4th stat card is **Knowledge Graph** (relations
  count → `/graph`), not "组织". Entity types render via `entityTypeLabel()` in
  `lib/entityColors.ts` (e.g. `model` → "AI 模型"). Graph type/relation filters are
  **solo-focus**: clicking one isolates+re-clusters its subgraph.
- **Static-export gotcha**: with `output: 'export'`, a dynamic route's
  `generateStaticParams()` must return a non-empty array (see `wiki/entities/[id]`).

## Where to look

- Endpoints & params → [`memory/api_reference.md`](memory/api_reference.md)
- Tables & enums → [`memory/data_model.md`](memory/data_model.md)
- How it's deployed → [`memory/deployment.md`](memory/deployment.md)
- Tool/skill catalog → [`tools/`](tools), [`skills/README.md`](skills/README.md)
