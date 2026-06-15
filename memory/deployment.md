# Deployment

Three free-tier hosts + Supabase. Working branch: `database/v1.0`.

## Git remotes

| Remote | Target | Purpose |
|--------|--------|---------|
| `origin` | `github.com/jingruzhao103-bit/HH-Research` | source of truth (push `database/v1.0`) |
| `public` | `github.com/alexps9/investment-research-database` | frontend → GitHub Pages (push to `main`) |
| `hf` | HF Space `Alexps9yyy/hh-research-api` | backend (subtree of `backend/`) |
| (mcp) | HF Space `Alexps9yyy/hh-research-mcp` | MCP server (subtree of `mcp_server/`) |

## Backend → Hugging Face Space (Docker)

```bash
git subtree split --prefix backend -b hf-deploy
git push hf hf-deploy:main --force
```
Set Space secrets: `DATABASE_URL` (Supabase session pooler), `DB_SSL_MODE=require`,
`EMBEDDING_API_KEY`, `DEEPSEEK_API_KEY` (optional), embedding overrides as needed.
URL: `https://Alexps9yyy-hh-research-api.hf.space` (health at `/health`).

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

## Frontend → GitHub Pages

Push `database/v1.0` to `public:main`; the `deploy-pages.yml` Action builds the
Next.js static export. Set repo var `NEXT_PUBLIC_API_URL` to the backend URL.

```bash
git push public database/v1.0:main --force
```

## Database (Supabase, manual SQL)

Run in the Supabase SQL editor when schema changes:
- `migration_0004.sql` — daily_digests + funding_events tables.
- `set_embedding_dim.sql` — set `embeddings.vector` dimension to match the model.

## Agent (`agent/`)

Runs locally or on any host; not a deployed service. Needs `LLM_API_KEY` and
`KB_API_BASE_URL`. See [`agent/README.md`](../agent/README.md).
