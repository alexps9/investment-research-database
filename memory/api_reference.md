# API Reference

Base URL: `${KB_API_BASE_URL}` (default `http://localhost:8000`). All endpoints
are under the `/api` prefix. Interactive docs at `/docs`.

> Hosted backend: `https://Alexps9yyy-hh-research-api.hf.space`

## Health
- `GET /health` → `{"status":"ok"}` (no `/api` prefix)

## Auth (JWT bearer login)
- `POST /api/auth/login` `{username, password}` → `{access_token, token_type, user}`
  (401 on bad credentials). Token is an HS256 JWT signed with `JWT_SECRET`.
- `GET /api/auth/me` (Bearer token) → current `{id, username, display_name, is_admin}`
- The **frontend gates the whole app** on login; the API itself does not yet
  require the bearer on data endpoints (so MCP/agents keep working unchanged).
  Initial accounts are seeded on startup from `SEED_USERS` (see deployment).
- Concurrency note: writes run under **REPEATABLE READ**; a serialization
  failure (40001) / deadlock (40P01) is returned as **409** — clients should retry.

## Dashboard
- `GET /api/dashboard/stats` → totals (sources/signals/entities/relations)
- `GET /api/dashboard/latest-signals?limit=`
- `GET /api/dashboard/latest-runs?limit=`

## Sources  (full CRUD)
- `GET /api/sources?skip=&limit=`
- `GET /api/sources/{id}`
- `POST /api/sources`
- `PATCH /api/sources/{id}`
- `DELETE /api/sources/{id}`
- `POST /api/sources/{id}/accounts` · `POST /api/sources/{id}/tags`

## Signals  (full CRUD)
- `GET /api/signals?signal_type=&source_id=&organization_id=&status=&q=&published_from=&published_to=&skip=&limit=`
- `GET /api/signals/{id}` · `GET /api/signals/{id}/related`
- `POST /api/signals` · `PATCH /api/signals/{id}` · `DELETE /api/signals/{id}`
- `POST /api/signals/{id}/analysis` · `POST /api/signals/{id}/entities`

## Entities & graph
- `GET /api/entities?entity_type=&q=&skip=&limit=`
- `GET /api/entities/{id}` · `PATCH /api/entities/{id}` · `POST /api/entities`
- `POST /api/entities/{id}/aliases`
- `GET /api/entities/{id}/signals` · `GET /api/entities/{id}/relations`
- `POST /api/entities/{id}/relations`  (relation_type ∈ VALID_RELATION_TYPES)
- `GET /api/graph/relations?limit=`
- `POST /api/graph/sync` — derive **explicit** edges from structured data
  (person→WORKS_AT/PRE_WORKED_AT org, person/org→FOCUSES_ON topic, org→SUBSIDIARY_OF parent).
  Idempotent; entities matched by name *or* canonical_name. Returns `{created, skipped}`.
- `POST /api/graph/infer` — derive **implicit** edges: `CO_WORK` between people who
  share an org (current or via experiences) and `CO_AUTHOR` between people on the same
  signal. Symmetric (one canonical min/max edge per pair), idempotent, pairs capped at
  25 members/group. Returns `{created, skipped}`. Manual trigger via the graph page
  buttons; scheduled via `deploy/graph_refresh.sh` (cron).
- `GET /api/wiki/entities/{id}`  (full profile)

## Search
- `GET /api/search?q=`  (keyword search across entities/signals/sources)

## AI — semantic search & RAG
- `GET /api/ai/status` → `{embeddings_enabled, chat_enabled, embedding_model, llm_model}`
- `GET /api/ai/search?q=&types=entity,source,signal&limit=`  (vector search). `types`
  defaults to all, but the **frontend passes `types=entity`** — source rows duplicate
  entities, so search surfaces entities only (shown under the "信源 / Source" label).
- `POST /api/ai/ask` `{question, top_k, object_types?}` → `{answer, sources}` (RAG).
  Retrieval defaults to **`object_types=["entity"]`**. The system prompt is tuned to
  never mention "context"/retrieval internals and to keep "no relevant info" replies
  to one short sentence. Chat runs through the LiteLLM gateway (Bedrock Claude →
  DeepSeek-V4 fallback); upstream errors surface as **502**.
- `POST /api/ai/reindex` `{object_types?}`  (rebuild vector index; indexes all types)

## Deep Research  (async, proxied to the agent service on :9000)
- `POST /api/research/start` `{question, max_subtopics?=4 (1–6), searches_per_topic?=2 (1–4)}`
  → `{job_id, status:"running"}`. Kicks off an open_deep_research-style run (brief →
  plan → parallel web research → compress → report). Takes ~2–4 min.
- `GET /api/research/status/{job_id}` → `{status:"running"|"done"|"failed", phase, pct,
  message, result?, error?}`. On `done`, `result = {question, brief, subtopics[],
  report (Markdown), sources[{title,url}]}`. The frontend `/research` page polls this.
- Backend just proxies to the agent (`agent_base_url` → `http://agent:9000`); jobs are
  in-memory on the agent (lost on restart). Agent unreachable → **502**.

## Daily Boost
- `GET /api/daily?limit=` · `GET /api/daily/latest` · `GET /api/daily/{date}`
- `POST /api/daily/generate?digest_date=&window_days=&limit=`

## Funding  (full CRUD + trends)
- `GET /api/funding?sector=&round=&q=&limit=&offset=`
- `GET /api/funding/{id}` · `POST /api/funding` · `PATCH /api/funding/{id}` · `DELETE /api/funding/{id}`
- `GET /api/funding/trends` → totals + by_month / by_round / by_sector

## Export
- `GET /api/export/sources.csv`
- `GET /api/export/signals.csv?signal_type=&status=`

## Pipeline
- `GET /api/runs?limit=` · `POST /api/runs/mock`

> The Python wrappers for all of these live in [`tools/`](../tools) (one package per domain).
