# Knowledge Base MCP Server

Exposes the AI Intelligence Knowledge Base to other agents via the
[Model Context Protocol](https://modelcontextprotocol.io).

It is a thin wrapper that calls the existing FastAPI backend over HTTP —
PostgreSQL stays the single source of truth and the backend remains the only
component touching the database.

```
Agent (Claude / Cursor / custom)
        │  MCP (stdio or streamable-http)
        ▼
   mcp_server/server.py
        │  HTTP /api/*
        ▼
   FastAPI backend ──► PostgreSQL
```

---

## Tools

**Read**
- `search_knowledge(q)` — global search across entities / signals / sources
- `get_dashboard_stats()` — aggregate counts
- `list_sources(skip, limit)` / `get_source(source_id)`
- `list_signals(signal_type, source_id, status, q, ...)` / `get_signal(signal_id)` / `get_related_signals(signal_id)`
- `list_entities(entity_type, q)` / `get_entity_wiki(entity_id)` / `get_entity_relations(entity_id)`
- `list_all_relations(limit)` — full relation edge list
- `list_relation_types()` — allowlist for relations
- `list_pipeline_runs(limit)`

**Write (create / update / delete — full CRUD)**
- `create_signal(...)` / `update_signal(signal_id, ...)` / `delete_signal(signal_id)`
- `create_source(...)` / `update_source(source_id, ...)` / `delete_source(source_id)`
- `create_entity(...)` / `update_entity(entity_id, ...)`
- `add_entity_relation(subject_entity_id, relation_type, object_entity_id, ...)`

**Vector search & RAG**
- `ai_status()` — whether embeddings / chat are configured
- `semantic_search(q, types, limit)` — embedding similarity search
- `ask(question, top_k)` — RAG question answering (DeepSeek + retrieval)
- `reindex_embeddings(object_types)` — (re)build the vector index

**Funding (investment / financing)**
- `list_funding(sector, round, q, limit)` / `get_funding(id)` / `funding_trends()`
- `create_funding(...)` / `update_funding(id, ...)` / `delete_funding(id)`

**Daily Boost**
- `get_daily_digest(date)` / `list_daily_digests(limit)` / `generate_daily_digest(date, window_days, limit)`

**Resources**
- `kb://stats` — aggregate counts
- `kb://entities/{entity_id}` — full entity Wiki profile
- `kb://daily/latest` — latest Daily Boost digest

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `KB_API_BASE_URL` | `http://localhost:8000` | Backend base URL |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | Host (http transport only) |
| `MCP_PORT` | `8765` | Port (http transport only) |

---

## Run

```bash
cd mcp_server
pip install -r requirements.txt

# Make sure the backend is running first (http://localhost:8000)

# stdio (local clients like Claude Desktop / Cursor)
python server.py

# streamable-http (remote / multi-agent), served at http://localhost:8765/mcp
MCP_TRANSPORT=streamable-http python server.py
```

Via Docker Compose (the `mcp` service runs in `streamable-http` mode):

```bash
docker compose up --build mcp
# endpoint: http://localhost:8765/mcp
```

---

## Client configuration

### Claude Desktop / Cursor — stdio

`~/.cursor/mcp.json` or Claude Desktop config:

```json
{
  "mcpServers": {
    "ai-knowledge-base": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server/server.py"],
      "env": {
        "KB_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Remote agents — streamable-http

```json
{
  "mcpServers": {
    "ai-knowledge-base": {
      "transport": {
        "type": "streamable-http",
        "url": "http://localhost:8765/mcp"
      }
    }
  }
}
```

---

## Quick check (MCP Inspector)

```bash
# Lists exposed tools/resources without writing a client
npx @modelcontextprotocol/inspector python server.py
```
