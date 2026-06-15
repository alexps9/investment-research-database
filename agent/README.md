# agent/

LangGraph-based **multi-agent system** for the HH-Research knowledge base.

## Six agents

| Agent | Role | Trigger |
|-------|------|---------|
| **Ingestion** (`ingestion_agent/`) | Fetch Twitter/RSS/media → create signals | cron / `agent.run ingest` |
| **Analysis** (`analysis_agent/`) | Signal → structured intelligence (LLM) | cron / `agent.run analyze` |
| **Entity** (`entity_agent/`) | Analysis → entities + relations + reindex | cron / `agent.run entity` |
| **Alert** (`alert_agent/`) | Important analyzed signals → Feishu push | cron / `agent.run alert` |
| **Digest** (`digest_agent/`) | Daily brief (Feishu-XML) from analyzed signals | cron daily / `agent.run digest` |
| **Data** (`data_agent/`) | Read-only Q&A over KB (RAG) | HTTP `POST /qa` |

## Architecture

```
cron / HTTP trigger
       │
       ▼
┌──────────────── LangGraph intelligence graph ────────────────┐
│  ingest → analyze → entity (KG)                              │
│              └────→ alert (Feishu push)                      │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
  FastAPI backend ──► Supabase + pgvector

┌──────────── agent.service :9000 ────────────┐
│  POST /qa          Data Agent (read-only)   │
│  POST /trigger/*   manual pipeline stages    │
└─────────────────────────────────────────────┘
```

```
agent/
  llm.py               ChatOpenAI → LiteLLM gateway (Bedrock Claude)
  state.py             PipelineState TypedDict
  graph.py             build_intelligence_graph() + build_digest_graph()
  run.py               CLI for cron (pipeline / ingest / analyze / …)
  service.py           FastAPI (Q&A + triggers)
  ingestion_agent/
  analysis_agent/
  entity_agent/
  alert_agent/         node.py + fetcher/prefilter/store (legacy plumbing)
  digest_agent/        node.py + DIGEST_AGENT_SYSTEM_MESSAGE
  data_agent/          read-only ReAct agent
```

## Setup

```bash
pip install -r agent/requirements.txt
cp agent/.env.example agent/.env   # LLM_API_KEY, KB_API_BASE_URL, FEISHU_WEBHOOK_URL
```

## Run (from repo root)

```bash
# Full pipeline (ingest → analyze → entity + alert)
python -m agent.run pipeline

# Individual stages
python -m agent.run ingest --no-twitter
python -m agent.run analyze --limit 10
python -m agent.run entity
python -m agent.run alert
python -m agent.run digest --date 2026-06-15 --publish

# HTTP service (Q&A + manual triggers)
python -m agent.service
curl -X POST http://localhost:9000/qa -H 'Content-Type: application/json' \
  -d '{"question":"最近有哪些重要的模型发布？"}'
curl -X POST http://localhost:9000/trigger/pipeline
```

## Cron (server)

```cron
0 */2 * * * cd ~/hh-research && docker compose -f deploy/docker-compose.server.yml exec -T agent python -m agent.run pipeline >> ~/pipeline.log 2>&1
0 9 * * * cd ~/hh-research && docker compose -f deploy/docker-compose.server.yml exec -T agent python -m agent.run digest --publish >> ~/digest.log 2>&1
```

## Safety

- **Data Agent** exposes only `READONLY_TOOLS` — no create/update/delete.
- Alert/Digest/Ingestion/Analysis/Entity use write tools gated by pipeline logic.
- Feishu push uses outbound webhook only (`FEISHU_WEBHOOK_URL`); inbound bot Q&A is a future phase.
