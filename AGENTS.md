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
webapp/       Research Studio — standalone Next.js deep-research UI (4 pages, :8081 CN mirror)
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

# Research Studio (standalone webapp)
cd webapp && npm install && npm run dev       # http://localhost:3001

# MCP server (needs backend running)
cd mcp_server && pip install -r requirements.txt
MCP_TRANSPORT=streamable-http python server.py

# Multi-agent (from repo root)
pip install -r agent/requirements.txt
python -m agent.run pipeline              # full LangGraph pipeline
python -m agent.service                   # HTTP Q&A + deep research on :9000
curl -X POST http://localhost:9000/qa -H 'Content-Type: application/json' -d '{"question":"..."}'
# Deep research (async): start → poll
curl -X POST http://localhost:9000/research/start -H 'Content-Type: application/json' -d '{"question":"..."}'
curl http://localhost:9000/research/status/<job_id>
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
- **Deep Research agent** (`agent/deep_research_agent/`): an open_deep_research-style
  pipeline — **brief → plan (sub-topics) → per-topic research → final report**. It is
  **database-first**: each sub-topic is first grounded in the project's own KB via
  `deep_research_agent/kb.py` (`GET /api/ai/search`, `KB_API_BASE_URL`); the open web
  only **supplements** when KB coverage is thin (`KB_MIN_HITS`/`KB_SUFFICIENT_CHARS`),
  else a single web round adds recency. The **final report has exactly four top-level
  sections** — `## 1. 执行摘要`, `## 2. 技术路线`, `## 3. 核心人物`, `## 4. 产业追踪` — written
  by four concurrent writers (`_write_exec_summary` / `_write_route_section` /
  `_write_people_section` / `_write_industry_section` in `researcher.py`). All scattered
  sub-topic findings are **folded into these four**, with finer points as numbered
  sub-headings (`### 2.1`, `### 2.2`, `### 3.1`, …). Each writer has its own `max_tokens`
  budget so no single cap drops a whole "big point". **References are appended in code**: KB hits first (entities link
  to their `/wiki/entities/{id}` page) above external web links; the result dict carries
  both `sources` (web) and `kb_sources` (`{object_type,object_id,name,wiki_url,…}`). The
  `/research` page renders the Markdown report and offers **PDF export via browser print**
  (`window.print()` + a print stylesheet scoped to `#research-report` — native CJK, real
  links). All LLM calls go through the LiteLLM gateway (`llm.py`, roles map to optional
  `*_MODEL` env overrides); web search uses the free DuckDuckGo `tools/websearch` + an
  HTML→text page fetcher (`search.py`). Bounded by design (≤6 sub-topics, ≤4 searches/topic,
  concurrency 3) so a run is ~2–4 min.
  Exposed as **async jobs**: agent `POST /research/start` + `GET /research/status/{id}`
  (in-memory job dict with `phase`/`pct`/`message` progress), proxied by the backend.
  **Concurrency model** (research is I/O-bound, so one async worker carries many runs;
  the shared LiteLLM gateway + single proxy node are the real ceiling): the precise
  gates are two *global* semaphores — `LLM_MAX_CONCURRENCY` (default 8) caps in-flight
  LLM calls across all runs (`deep_research_agent/llm.py:ainvoke`), and
  `SEARCH_MAX_CONCURRENCY` (default 6) caps concurrent search+fetch bundles
  (`deep_research_agent/search.py:search_and_read`). Run admission is generous:
  `RESEARCH_MAX_CONCURRENT` (default 6) caps runs executing at once and queues the rest
  (job stays `running`/phase `queued`); `RESEARCH_MAX_PENDING` (default 30) bounds
  running+queued (else 429); finished jobs are pruned after `RESEARCH_JOB_TTL` (1h).
  HTML→text parsing runs via `asyncio.to_thread` so it doesn't stall the event loop.
  LiteLLM stays at **1 worker** (`LITELLM_NUM_WORKERS`) — each worker costs ~1GB and a
  2nd OOMs the 3.4GB host; it's async so one worker pipelines the throttled load fine.
  Burst 429/5xx from Bedrock retry (`num_retries: 2`) then fall back to DeepSeek-V4.
  Proxied by the backend at `/api/research/*` (`backend/app/routers/research.py`, `agent_base_url` →
  `http://agent:9000`). The frontend `/research` page polls status and renders the
  Markdown report (react-markdown + `@tailwindcss/typography`). **The agent container
  egresses search/fetch through the overseas proxy** (`HTTP(S)_PROXY=proxy:8118`,
  internal services in `NO_PROXY`) because DuckDuckGo is blocked from CN — without it
  `sources` come back empty and the report is LLM-only.

## Research Studio (`webapp/`)

A **separate** Next.js app (does not touch `frontend/`). To stay safe under
`output: 'export'` (dynamic `/s/[id]` routes break on hard-load/client-nav because
their RSC payloads aren't prerendered), **all views live on the index route `/`
driven by query params**. nginx falls back to `/index.html`, so deep links and
sidebar history work on both hard load and client navigation.

| Route (query param) | Purpose |
|-------|---------|
| `/` | Google-style search + ChatGPT-like session sidebar (`SearchHome`) |
| `/?id=<uuid>` | `SessionWorkspace`: live progress (`ResearchProgress`) → markdown report (4 fixed H2 sections: 执行摘要/技术路线/核心人物/产业追踪) + PDF export + sub-view links |
| `/?id=<uuid>&view=trajectory` | Paper timeline by `metadata.year`/`lane`, edges `BUILT_ON`/`RELATED_TO`/`COMPETES_WITH`; scope papers highlighted |
| `/?id=<uuid>&view=people` | `react-force-graph-2d` subgraph; scope entity IDs highlighted, rest dimmed |
| `/?id=<uuid>&view=industry` | Renders `session.industry` + live `/api/funding` + `/api/signals` |

`app/page.tsx` reads `useSearchParams()` (inside a `<Suspense>` boundary required
by static export) and renders `SearchHome` when no `id`, else `SessionWorkspace`.
Submitting a question `router.push('/?id=<uuid>')` → progress renders in place.

**Sessions API** (`backend/app/routers/research_sessions.py`):
- `POST /api/research/sessions` — create row, start agent job, return `{id,…}`
- `GET /api/research/sessions?limit=50` — sidebar history
- `GET /api/research/sessions/{id}` — full session; if `running`, polls agent and persists result
- `DELETE /api/research/sessions/{id}`

**Agent output extensions** (in addition to `report`/`kb_sources`/`sources`):
- `scope`: `{topic_ids, lane_ids, paper_ids, person_ids, org_ids, core_people,
  route_categories, paper_categories}` — LLM maps question to existing `entity_type=topic`
  lanes/rows; entity IDs from KB hits + graph expansion. `core_people=[{id,name,org,wiki_url}]`
  covers **all** queried person entities (each is a core person; names resolved via fetch).
  Authors are captured from **every** retrieved/expanded paper (`AUTHORED` expansion runs
  unconditionally — NOT gated on topic classification — so thin/empty topic hits still yield
  comprehensive core people). People cited as **`(source)`** (the `sources` signal-registry,
  e.g. Fei-Fei Li / Pieter Abbeel) carry a *source* id, not an entity id, so `_build_scope`
  resolves each to its person **entity** by name (`search_entities`) and folds it into
  `core_people` (gaining a `/wiki/entities/{id}` link + graph node). Source people + direct KB
  hits are ordered **first**, so they are the ones `_track_people_events` web-searches.
  `route_categories=[{key,label}]` + `paper_categories={paper_id:key}` are **dynamically
  generated** by `_classify_routes` (count is data-driven, NOT hard-coded). The Trajectory
  chart uses these as its lanes (so they match report §2 sub-headings); People graph
  highlights only **person** nodes (others dimmed).
- `industry`: derived **after** the report — `{core_people, tech_signals, impact_md,
  person_signals, capital, funding, sources}`. `tech_signals`+`impact_md` come from ONE LLM
  interpretation of the generated report (`_interpret_report_signals`); `person_signals`/
  `capital`/`funding` come from a per-core-person web search (`_track_people_events`, two
  query angles/person), each item carrying `person_id`+`wiki_url`. It prefers recent events
  but **widens the window** (months → 1–2 years) and aims for **≥3 capital/funding events**
  so the page is rarely empty; lists are date-sorted desc. Persisted in the
  `research_sessions.industry` JSON (the DB) and rendered on the Industry page.

Report §4 产业追踪 is composed deterministically from `industry` (`_compose_industry_section`)
so the report and the Industry page stay consistent.

> **JSON parsing (do not regress):** every structured LLM step (topic classification,
> `_classify_routes`, `_interpret_report_signals`, `_track_people_events`) relies on
> `_extract_json`, which must select whichever of `{`/`[` appears **first** and scan for the
> balanced close (honouring strings). Preferring `[` blindly truncates an object that merely
> *contains* an array (e.g. `{"categories":[…],"assignments":{}}`) to its inner array, which
> callers reject via `isinstance(parsed, dict)` — silently emptying route categories, tech
> signals, industry impact and per-person capital/funding.

**Frontend pages**: Trajectory chart supports drag-to-pan + spacing zoom (declutter dense
years). Industry page links core people to their wiki via `NEXT_PUBLIC_WIKI_BASE_URL`
(main frontend origin, e.g. `http://110.40.131.38:8080`; relative fallback when unset).

Deploy: CN static mirror on **:8081** (`deploy/webapp.nginx.conf`); optional second Vercel
project (Root Directory `webapp`). See [`memory/deployment.md`](memory/deployment.md).

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
  (`useRowSelection`, `Checkbox`, `ExportBar`, `bulkDelete`). All four checkbox
  lists — person Sources, **Organizations**, Signals, Entities (topic) — wire
  `onExportSelected/onExportAll` + `onDeleteSelected` into `ExportBar` for **bulk
  export (CSV) + bulk delete**; `bulkDelete()` deletes sequentially (REPEATABLE
  READ ⇒ avoid concurrent-write 409s) and reports per-id success/failure.
- **AI search & Q&A return entities only** (`/ai/search?types=entity`, `/ai/ask`
  defaults `object_types=["entity"]`) — source rows duplicate entities. The Explore
  UI shows these hits under the "信源 / Source" label. The Q&A system prompt forbids
  exposing retrieval jargon ("context") and keeps "no info" replies to one sentence.
- **Dashboard / graph labels**: the 4th stat card is **Knowledge Graph** (relations
  count → `/graph`), not "组织". Entity types render via `entityTypeLabel()` in
  `lib/entityColors.ts`. The graph **hides the `model` entity type**
  (`HIDDEN_ENTITY_TYPES` in `app/graph/page.tsx`). Graph entity/relation filters are
  **multi-select (combinable)**: clicking toggles each type into a focus set
  (`focusTypes`/`focusRelTypes`), and the union subgraph re-clusters (filterKey
  remount); "全部" resets.
- **Static-export gotcha**: with `output: 'export'`, a dynamic route's
  `generateStaticParams()` must return a non-empty array (see `wiki/entities/[id]`).
- **Papers entity type**: the knowledge graph includes `paper` entities (amber, label
  "论文" via `entityColors.ts`). The world-model paper dataset
  (`backend/data/world_model_export.json`, 186 papers) is imported by the idempotent
  `backend/scripts/import_world_model_papers.py` (run inside the backend container):
  it creates `paper` entities (name/arXiv url/metadata, **no PDF**), lane/row `topic`
  entities, and relations `AUTHORED` (paper→person, authors matched to existing people
  by name, optionally via `--vector-match`), `FOCUSES_ON` (paper→topic), `SUBTOPIC_OF`,
  and paper↔paper `BUILT_ON`/`RELATED_TO`/`COMPETES_WITH` (from dataset connections).
  `/graph/relations` is fetched with `limit=5000` to fit the larger graph.
- **Wiki = entity-centric, auto-maintained**: `GET /api/wiki/entities/{id}` aggregates
  entity + infobox metadata + relations (grouped by type) + signals + linked source.
  Creating/updating a **person/organization Source** auto-creates/refreshes its mirror
  entity (and thus its wiki) via `backend/app/services/wiki_sync.py`
  (`sync_source_to_entity`, called best-effort from the sources router; links by a stable
  `source_id` in entity metadata so renames are handled). `WikiEntityClient.tsx` renders a
  Wikipedia-style layout (lead + infobox sidebar + categorised relations + references +
  "see also" + categories).

## Where to look

- Endpoints & params → [`memory/api_reference.md`](memory/api_reference.md)
- Tables & enums → [`memory/data_model.md`](memory/data_model.md)
- How it's deployed → [`memory/deployment.md`](memory/deployment.md)
- Tool/skill catalog → [`tools/`](tools), [`skills/README.md`](skills/README.md)
