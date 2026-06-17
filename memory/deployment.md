# Deployment

Three free-tier hosts + Supabase. Working branch: `database/v1.0`.

## Git remotes

| Remote | Target | Purpose |
|--------|--------|---------|
| `origin` | `github.com/jingruzhao103-bit/HH-Research` | source of truth (push `database/v1.0`) |
| `public` | `github.com/alexps9/investment-research-database` | frontend → **Vercel** (push to `main`) |
| `hf` | HF Space `Alexps9yyy/hh-research-api` | backend (subtree of `backend/`) |
| (mcp) | HF Space `Alexps9yyy/hh-research-mcp` | MCP server (subtree of `mcp_server/`) |

## Backend → Hugging Face Space (Docker)

```bash
git subtree split --prefix backend -b hf-deploy
git push hf hf-deploy:main --force
```
Set Space secrets: `DATABASE_URL` (Supabase session pooler), `DB_SSL_MODE=require`,
`EMBEDDING_API_KEY`, `DEEPSEEK_API_KEY` (optional), embedding overrides as needed.
For login auth set `JWT_SECRET` (long random) and optionally `SEED_USERS`
(`user:pass,...`, default seeds the bootstrap accounts on first start).
URL: `https://Alexps9yyy-hh-research-api.hf.space` (health at `/health`).

> Auth/schema note: migrations 0008 (`users`) + 0009 (relation dedupe) + 0010
> (`research_sessions`) are applied by `alembic upgrade head` (HF `start.sh`). The server
> alembic, so run `docker compose ... run --rm backend alembic upgrade head`
> once after pulling new migrations. Users are seeded on startup (idempotent),
> so deploying any one backend populates the shared Supabase DB.

## MCP server → Hugging Face Space (Docker)

```bash
git subtree split --prefix mcp_server -b mcp-deploy
git push <space-remote> mcp-deploy:main --force
```
Set Space variable: `KB_API_BASE_URL=https://Alexps9yyy-hh-research-api.hf.space`
(others default: `MCP_TRANSPORT=streamable-http`, `MCP_HOST=0.0.0.0`, `MCP_PORT=8765`).
Endpoint: `https://Alexps9yyy-hh-research-mcp.hf.space/mcp`.

> Note: the `mcp` SDK enables DNS-rebinding protection when bound to `0.0.0.0`,
> which 421s behind a proxy. We pass `TransportSecuritySettings(enable_dns_rebinding_protection=False)`.

## Frontend → domestic mirror (CN users) + Vercel (overseas)

**Why**: `*.vercel.app` is GFW-throttled in mainland China — from a CN client the TLS
handshake to the Vercel edge often never completes (`code=000`), so both the app and
its API (proxied via the Vercel rewrite) load slowly/flakily. The backend, by contrast,
is ~1ms from CN users (domestic). So CN users are served a **static mirror hosted on the
Tencent box itself**, calling the backend directly.

**Topology**: `http://110.40.131.38:8080` (nginx, static Next export) → browser calls
`http://110.40.131.38:8000/api/*` **directly** (both plain HTTP → no mixed-content;
backend CORS allows it). No Vercel, no cross-border hop.

**Compose**: `frontend` service (nginx:alpine) in `docker-compose.server.yml` mounts
`./frontend-out` (the build) + `./frontend.nginx.conf`, publishes `8080:80`.

**Redeploy the CN frontend** (run locally, then ship — bundle is generated, gitignored):
```bash
cd frontend
NEXT_BUILD_STATIC=true NEXT_PUBLIC_API_URL=http://110.40.131.38:8000 npm run build   # -> out/
tar -czf ../deploy/frontend-out.tgz -C out .
scp ../deploy/frontend-out.tgz hh-server:~/hh-research/deploy/
ssh hh-server "cd ~/hh-research/deploy && rm -rf frontend-out && mkdir frontend-out && \
  tar -xzf frontend-out.tgz -C frontend-out && docker compose -f docker-compose.server.yml restart frontend"
```
> Use `restart frontend` (not just `up -d frontend`): `rm -rf frontend-out` replaces the
> bind-mount source **inode**, and `up -d` won't recreate the container when compose
> config is unchanged, so it keeps serving the deleted dir (403). A restart re-resolves
> the mount.
`generateStaticParams` fetches all entities at build time to pre-render per-entity wiki
pages; brand-new entities need a rebuild for deep-links (in-app nav works regardless).

**REQUIRED one-time step**: open **TCP 8080** inbound in the **Tencent Cloud security
group** (only 8000/8765 were open). Verified: nginx serves 200 on `localhost:8080`,
docker binds `0.0.0.0:8080`, `ufw` inactive — external access is blocked solely by the
security group until 8080 is allowed.

## Research Studio (`webapp/`) — separate frontend

A **standalone** Next.js app at `webapp/` (does **not** modify `frontend/`). Google-style
deep-research home + ChatGPT-like session sidebar; report page with PDF export and three
interactive sub-pages: **技术路线演进** (trajectory timeline), **核心人物** (highlighted
knowledge subgraph), **产业追踪** (industry signals/impact/talent/capital).

**Topology**: `http://110.40.131.38:8081` (nginx, static Next export) → browser calls
`http://110.40.131.38:8000/api/*` directly (same as the CN mirror on :8080).

**Backend**: `POST/GET/DELETE /api/research/sessions` persists runs in `research_sessions`
(migration `0010` / `migration_0010.sql`). Creating a session starts an agent job and stores
`agent_job_id`; polling `GET /api/research/sessions/{id}` syncs progress/result (report,
`scope`, `industry`, `kb_sources`, `sources`) into the DB when done.

**Agent extensions**: `run_deep_research` now also returns `scope` (topic lane/row mapping +
entity IDs from KB + graph) and `industry` (web-grounded tech signals, impact, top people,
capital). The report always includes `## 技术路线演进`, `## 核心人物`, `## 产业追踪`.

**Redeploy the CN webapp** (run locally):
```bash
cd webapp
NEXT_BUILD_STATIC=true NEXT_PUBLIC_API_URL=http://110.40.131.38:8000 npm run build   # -> out/
tar -czf ../deploy/webapp-out.tgz -C out .
scp ../deploy/webapp-out.tgz hh-server:~/hh-research/deploy/
ssh hh-server "cd ~/hh-research/deploy && rm -rf webapp-out && mkdir webapp-out && \
  tar -xzf webapp-out.tgz -C webapp-out && docker compose -f docker-compose.server.yml up -d webapp"
```
> After `rm -rf webapp-out`, use `up -d webapp` or `restart webapp` so nginx re-binds the mount.

**Vercel (second project)**: create a new Vercel project with Root Directory = `webapp`.
`webapp/vercel.json` rewrites `/api/*` → Tencent backend. No `NEXT_BUILD_STATIC` on Vercel.

**One-time**: open **TCP 8081** in the Tencent security group; run migration 0010 on Supabase
(or `docker compose ... run --rm backend alembic upgrade head` on the server).

## Frontend → Vercel  (live: https://investment-research-database.vercel.app/)

The `public` repo is connected to **Vercel**, which auto-deploys on every push to
its `main`. So deploying the frontend is just:

```bash
git push public database/v1.0:main --force   # Vercel auto-builds & deploys
```

The deployed frontend reaches the backend through a **Vercel edge rewrite**:
`frontend/vercel.json` proxies `/api/:path*` → the Tencent backend
(`http://110.40.131.38:8000/api/:path*`). This keeps the browser on HTTPS while the
backend is HTTP-only (no mixed-content). Notes:
- `next.config.js` enables `rewrites()` **only in dev**; in prod Vercel uses
  `vercel.json`. `trailingSlash` is enabled **only** for GitHub-Pages builds
  (`NEXT_PUBLIC_BASE_PATH`); on Vercel it must stay off or 308 redirects break the proxy.
- To point at the HF backend instead, set `NEXT_PUBLIC_API_URL` and drop the rewrite.

> History / gotchas:
> - We do **NOT** use GitHub Pages. A `deploy-pages.yml` workflow exists but is not
>   the deploy path; ignore it (Pages was never the production host).
> - `next.config.js` only sets `output: 'export'` when `NEXT_BUILD_STATIC=true`;
>   Vercel builds in normal (non-export) mode, so SSR/dynamic routes are fine there.
> - **Static-export gotcha**: with `output: 'export'`, a dynamic route's
>   `generateStaticParams()` must return a **non-empty** array or the build fails
>   with *"is missing generateStaticParams()"*. `wiki/entities/[id]` therefore
>   returns a `placeholder` param when the backend isn't reachable at build time.

## Database (Supabase, manual SQL)

Run in the Supabase SQL editor when schema changes:
- `migration_0004.sql` — daily_digests + funding_events tables.
- `set_embedding_dim.sql` — set `embeddings.vector` dimension to match the model.

## World-model papers import (one-off, idempotent)

`backend/data/world_model_export.json` (186 papers + 4 lanes + 12 rows + 326
connections) is imported into the entity graph by
`backend/scripts/import_world_model_papers.py`. No new schema — papers are just a
new `entity_type="paper"` (no PDF; name + authors + arXiv/DOI url + metadata). Run
it **inside the backend container** (reuses the Supabase creds) after deploying the
backend with the new data file/script:

```bash
ssh hh-server "cd ~/hh-research/deploy && \
  sudo docker compose -f docker-compose.server.yml exec -T backend \
    python scripts/import_world_model_papers.py --reindex"
```

It creates lane/row `topic` entities, `paper` entities, author `person` entities
(existing people reused by exact name; add `--vector-match` to also match via
embeddings), and relations `AUTHORED` / `FOCUSES_ON` / `SUBTOPIC_OF` /
`BUILT_ON|RELATED_TO|COMPETES_WITH`. `--reindex` rebuilds entity embeddings so the
papers are searchable (deep-research DB-first retrieval + graph semantic locate).
Re-running is safe (dedupes by `(canonical_name, entity_type)` and relation triple).

## Wiki auto-sync (sources → entities)

Creating/updating a **person/organization** source now auto-creates/refreshes its
mirror entity (and thus its wiki page) via `backend/app/services/wiki_sync.py`
(best-effort, called from `sources.py`). No deploy step beyond shipping the new
backend code; brand-new wiki deep-links on the **static** CN mirror still need a
frontend rebuild (in-app navigation works immediately).

## Agent (`agent/`)

Runs locally or on any host; not a deployed service. Needs `LLM_API_KEY` and
`KB_API_BASE_URL`. See [`agent/README.md`](../agent/README.md).

## Self-hosted server (Tencent Cloud, Docker) — backend + mcp + agent

An alternative to the HF Spaces for backend + MCP: run all three on one Docker
host while keeping the DB on Supabase and the frontend on Vercel. Artifacts live in
[`deploy/`](../deploy) (`docker-compose.server.yml`, `agent.Dockerfile`,
`.env.server.example`); full steps in [`deploy/README.md`](../deploy/README.md).

- Host: `ubuntu@110.40.131.38` (SSH alias `hh-server`, key `~/.ssh/database.pem`).
- Services (5 containers): `proxy` (gost) → `litellm:4000` (OpenAI→Bedrock gateway)
  → `backend:8000` (→ Supabase, alembic skipped since schema is shared),
  `mcp:8765` (→ `http://backend:8000`), `agent:9000` (Q&A `/qa` + **deep research**
  `/research/*`; also runs pipelines on demand / via cron).
- The agent image build context is the **repo root** (it imports `agent/` + `tools/`
  + `skills/`); backend/mcp build from their own dirs.
- **LLM = AWS Bedrock Claude via the LiteLLM gateway.** Backend (`DEEPSEEK_*` +
  `LLM_MODEL=claude-sonnet-4-6`) and agent (`LLM_*`) point their OpenAI base_url at
  `http://litellm:4000/v1` with `LITELLM_MASTER_KEY` as the key — no app code change.
  litellm maps `claude-sonnet-4-6`/`claude-opus-4-6`/`deepseek-chat` → Bedrock ids.
- **Bedrock geo-block workaround:** Anthropic on Bedrock blocks mainland-China IPs.
  The `proxy` (gost) tunnels to an overseas Shadowsocks node (US); litellm egresses
  Bedrock calls through it via `HTTPS_PROXY=http://proxy:8118` (`BEDROCK_PROXY_URL`).
  `PROXY_FORWARD_URL=ss://...` is the node. Correct Bedrock model id is
  `us.anthropic.claude-sonnet-4-6` (no `-v1:0`; note `anthropic` spelling).
  - SS nodes rotate/expire. When Q&A 502s with proxy `503 Service Unavailable` or
    `i/o timeout`, decode a fresh node from the subscription, TCP-test it, then update
    `PROXY_FORWARD_URL` and recreate `proxy`+`litellm`.
- **LLM fallback (DeepSeek-V4):** litellm `fallbacks` route `claude-sonnet-4-6` →
  `deepseek-v4` (`openai/deepseek-v4-pro` on `api.deepseek.com`, key
  `DEEPSEEK_FALLBACK_API_KEY`) when the primary errors. **`api.deepseek.com` is in
  `NO_PROXY`** so the fallback stays reachable even when the SS proxy is down — the
  whole point of the fallback. (DeepSeek's API exposes `deepseek-v4-pro` /
  `deepseek-v4-flash`, not a bare `deepseek-v4`.)
- **Deep Research agent** (`agent/deep_research_agent/`, served at `agent:9000
  /research/start|status`): the backend proxies `/api/research/*` to it
  (`agent_base_url=http://agent:9000`), so the Vercel frontend `/research` page reaches
  it over the same `/api` edge proxy. Its **web search (DuckDuckGo) + page fetches must
  egress through the SS proxy** — DDG is blocked from CN, so without it `sources` is
  empty and the report is LLM-only. The `agent` service therefore sets
  `HTTP_PROXY/HTTPS_PROXY=${BEDROCK_PROXY_URL}` (= `http://proxy:8118`) with internal
  services (`litellm,backend,mcp,agent,proxy`) in `NO_PROXY` so LLM/KB calls stay
  direct. httpx auto-uses these env proxies (`trust_env`). Research jobs are in-memory
  (lost on agent restart). Verified e2e on the server (~2–4 min/run, real sources).
  - **DB-first + sectioned report (current)**: each sub-topic is grounded in the KB
    (`deep_research_agent/kb.py` → `GET /api/ai/search`, direct to `backend:8000`,
    `trust_env=False`) before the web (web only supplements when KB is thin). The final
    report is written section-by-section (no single `max_tokens` can drop a "big point"),
    and references are appended in code — KB entities (linking to `/wiki/entities/{id}`)
    above external links. Result dict gains `kb_sources`; `/research` page adds **PDF
    export** (browser print of `#research-report`). Needs embeddings configured on the
    backend for the DB-first half (degrades to web-only otherwise).
  - **Concurrency**: one async agent worker carries many runs; the gate is two global
    semaphores — `LLM_MAX_CONCURRENCY=8` (in-flight LLM calls) and
    `SEARCH_MAX_CONCURRENCY=6` (search+fetch bundles). Run admission is generous
    (`RESEARCH_MAX_CONCURRENT=6`, queue up to `RESEARCH_MAX_PENDING=30`, else 429).
    Verified 3 simultaneous runs OK. **Keep `LITELLM_NUM_WORKERS=1`**: the 3.4GB host
    has ~1.4GB free and each LiteLLM worker ≈1GB, so a 2nd worker OOMs (no swap). LiteLLM
    is async, so one worker pipelines the throttled load; `num_retries: 2` + DeepSeek
    fallback absorb Bedrock bursts. Raise worker count only after a RAM upgrade.
- **Latency root cause / perf**: the DB is **Supabase `aws-1-ap-south-1` (Mumbai)** while
  the backend runs on **Tencent Cloud (CN)** — every DB round-trip is **~120ms**, so request
  latency is dominated by *round-trip count*, not row volume (only ~350 sources). Measured
  `/sources?limit=2000` at 4.4s before optimization. Mitigations in place: (1) **GZip**
  middleware (`app/main.py`, ~6–8x smaller JSON over the WAN); (2) `/dashboard/stats`
  collapses 4 COUNTs into **one** scalar-subquery round-trip; (3) the sources **list** drops
  the `experiences` eager-load chain (uses `SourceListOut`; experiences fetched on demand in
  the edit modal / wiki); (4) frontend `lib/api.ts` has a **60s in-memory GET cache + request
  dedup**, cleared on any write — repeat navigation is instant. Re-measured `/sources` at
  ~1.6s / 101KB on-wire. **Biggest remaining win = co-locating the DB with the backend**
  (move Postgres onto Tencent or the backend to the DB's region); not yet done (infra call).
- Embeddings stay on **SiliconFlow bge-m3 (1024 dims)** — reachable from CN directly.
- ghcr/dockerhub pulls from CN: used the **NJU mirror** `ghcr.nju.edu.cn` for the
  litellm image (direct ghcr blob CDN stalls from China); dockerhub `ginuerzh/gost`
  pulled fine. pip in Dockerfiles uses the **Tsinghua mirror** (`PIP_INDEX_URL`).
- Secrets in `deploy/.env` (gitignored): DB, embeddings, `AWS_BEARER_TOKEN_BEDROCK`,
  `LITELLM_MASTER_KEY` (= `DEEPSEEK_API_KEY` = `LLM_API_KEY`), `PROXY_FORWARD_URL`.
- **Open ports 8000 / 8765 in the Tencent Cloud security group** for external access
  (4000/8118 stay internal to the compose network).
