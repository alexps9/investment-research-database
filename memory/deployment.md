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

> Auth/schema note: migrations 0008 (`users`) + 0009 (relation dedupe) are
> applied by `alembic upgrade head` (HF `start.sh`). The server compose skips
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

## Frontend → Vercel  (live: https://investment-research-database.vercel.app/)

The `public` repo is connected to **Vercel**, which auto-deploys on every push to
its `main`. So deploying the frontend is just:

```bash
git push public database/v1.0:main --force   # Vercel auto-builds & deploys
```

Set the Vercel project env var `NEXT_PUBLIC_API_URL` to the backend URL
(`https://Alexps9yyy-hh-research-api.hf.space`) so the static client knows where
the API is.

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
  `mcp:8765` (→ `http://backend:8000`), `agent` (idle container, run pipelines on
  demand / via cron).
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
- Embeddings stay on **SiliconFlow bge-m3 (1024 dims)** — reachable from CN directly.
- ghcr/dockerhub pulls from CN: used the **NJU mirror** `ghcr.nju.edu.cn` for the
  litellm image (direct ghcr blob CDN stalls from China); dockerhub `ginuerzh/gost`
  pulled fine. pip in Dockerfiles uses the **Tsinghua mirror** (`PIP_INDEX_URL`).
- Secrets in `deploy/.env` (gitignored): DB, embeddings, `AWS_BEARER_TOKEN_BEDROCK`,
  `LITELLM_MASTER_KEY` (= `DEEPSEEK_API_KEY` = `LLM_API_KEY`), `PROXY_FORWARD_URL`.
- **Open ports 8000 / 8765 in the Tencent Cloud security group** for external access
  (4000/8118 stay internal to the compose network).
