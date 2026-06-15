# deploy/ — self-hosted server deployment (gateway + backend + mcp + agent)

Runs the **backend**, **mcp_server**, **agent**, plus a **LiteLLM gateway** and an
**outbound proxy** as Docker containers on a single host (the Tencent Cloud Ubuntu
box). The database stays on **Supabase** and the frontend stays on **Vercel**.

```
                              Docker host (server, CN)
   ┌────────────────────────────────────────────────────────────────────┐
   │  backend :8000 ─┐                                                    │
   │  agent :9000 ───┼─► litellm :4000 ─► proxy :8118 ─► SS node (US) ─► AWS Bedrock (Claude)
   │                 │      (OpenAI API)    (gost, HTTP)   overseas        Anthropic geo-OK
   │  backend :8000 ─┴─► Supabase (DATABASE_URL, TLS)                      │
   │  backend embeddings ─► SiliconFlow (bge-m3, reachable from CN)        │
   │  mcp :8765 ─► http://backend:8000                                     │
   └────────────────────────────────────────────────────────────────────┘
        ▲                                   frontend → Vercel (unchanged)
   open :8000 / :8765 / :9000 in the Tencent security group
```

**Why the proxy:** AWS Bedrock geo-blocks mainland-China IPs for Anthropic Claude.
The `proxy` (gost) connects to an overseas Shadowsocks node and exposes an HTTP
proxy; the litellm gateway egresses its Bedrock calls through it from a US IP.
Backend/agent speak the OpenAI API to litellm — no app code change.

## Files

- `docker-compose.server.yml` — proxy + litellm + backend + mcp + agent (no local db/redis/minio, no frontend).
- `litellm.config.yaml` — maps `claude-sonnet-4-6` / `claude-opus-4-6` / `deepseek-chat` → Bedrock model ids.
- `agent.Dockerfile` — agent image; **build context = repo root** (needs `agent/` + `tools/` + `skills/`).
- `.env.server.example` — template for the server `.env` (copy to `deploy/.env`).

## .env keys (secrets — never commit; deploy/.env is gitignored)

- `DATABASE_URL` / `DATABASE_URL_SYNC` / `DB_SSL_MODE=require` — Supabase.
- `EMBEDDING_API_KEY` (+ base/model/dims) — SiliconFlow bge-m3, 1024.
- `AWS_BEARER_TOKEN_BEDROCK` / `AWS_REGION_NAME=us-east-1` — Bedrock API key.
- `LITELLM_MASTER_KEY` — the key backend/agent send to the gateway; also set as
  `DEEPSEEK_API_KEY` and `LLM_API_KEY`. `DEEPSEEK_BASE_URL`/`LLM_BASE_URL=http://litellm:4000/v1`, `LLM_MODEL=claude-sonnet-4-6`.
- `PROXY_FORWARD_URL` — `ss://method:pass@host:port` of an overseas node (gost `-F`).
- `BEDROCK_PROXY_URL=http://proxy:8118` — litellm egress proxy.

## One-time deploy

1. Copy the code to the host (from a dev machine):
   ```bash
   tar --exclude=__pycache__ --exclude=.git --exclude=node_modules --exclude=.next \
       --exclude=.venv --exclude='*.pem' --exclude='**/.env' \
       -czf bundle.tgz backend mcp_server agent tools skills deploy
   scp bundle.tgz hh-server:~/
   ssh hh-server "mkdir -p ~/hh-research && tar -xzf ~/bundle.tgz -C ~/hh-research && rm ~/bundle.tgz"
   ```
2. Create `~/hh-research/deploy/.env` from `.env.server.example` and fill in secrets
   (Supabase `DATABASE_URL`, `EMBEDDING_API_KEY`, `DEEPSEEK_API_KEY` / `LLM_API_KEY`).
3. Build & start (compose runs from the repo root so build contexts resolve):
   ```bash
   cd ~/hh-research
   docker compose -f deploy/docker-compose.server.yml --env-file deploy/.env up -d --build
   ```
4. Open ports **8000** and **8765** in the Tencent Cloud security group.

## Verify

```bash
curl http://<server-ip>:8000/health
curl http://<server-ip>:8000/api/dashboard/stats
# MCP endpoint at http://<server-ip>:8765/mcp
```

## Run the agent / pipelines

The agent container runs **uvicorn** on `:9000` (Q&A + manual triggers).

```bash
cd ~/hh-research
# Q&A (read-only Data Agent)
curl -X POST http://localhost:9000/qa -H 'Content-Type: application/json' \
  -d '{"question":"Summarise recent funding in AI infra"}'

# Manual pipeline trigger
curl -X POST http://localhost:9000/trigger/pipeline

# CLI (cron-friendly)
docker compose -f deploy/docker-compose.server.yml exec agent python -m agent.run pipeline
docker compose -f deploy/docker-compose.server.yml exec agent python -m agent.run digest --publish
docker compose -f deploy/docker-compose.server.yml exec agent python -m agent.run alert
```

Schedule with cron on the host:

```cron
# Full intelligence pipeline every 2 hours
0 */2 * * * cd ~/hh-research && docker compose -f deploy/docker-compose.server.yml exec -T agent python -m agent.run pipeline >> ~/pipeline.log 2>&1

# Daily digest at 09:00 UTC+8 (adjust TZ as needed)
0 9 * * * cd ~/hh-research && docker compose -f deploy/docker-compose.server.yml exec -T agent python -m agent.run digest --publish >> ~/digest.log 2>&1
```

## Update / redeploy

Re-run the copy step, then `docker compose -f deploy/docker-compose.server.yml up -d --build`.
