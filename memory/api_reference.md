# API Reference

Base URL: `${KB_API_BASE_URL}` (default `http://localhost:8000`). All endpoints
are under the `/api` prefix. Interactive docs at `/docs`.

> Hosted backend: `https://Alexps9yyy-hh-research-api.hf.space`

## Health
- `GET /health` → `{"status":"ok"}` (no `/api` prefix)

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
- `GET /api/wiki/entities/{id}`  (full profile)

## Search
- `GET /api/search?q=`  (keyword search across entities/signals/sources)

## AI — semantic search & RAG
- `GET /api/ai/status` → `{embeddings_enabled, chat_enabled, embedding_model, llm_model}`
- `GET /api/ai/search?q=&types=entity,source,signal&limit=`  (vector search)
- `POST /api/ai/ask` `{question, top_k}` → `{answer, sources}`  (RAG)
- `POST /api/ai/reindex` `{object_types?}`  (rebuild vector index)

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
