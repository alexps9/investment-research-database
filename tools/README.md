# tools/

Atomic knowledge-base tools — one async function per backend `/api` endpoint.
Each **functional domain has its own directory** (named after its function):

| Directory | Function | Tools |
|-----------|----------|-------|
| `dashboard/` | overview & keyword search | `dashboard_stats`, `search_knowledge` |
| `sources/` | source CRUD | `list/get/create/update/delete_source` |
| `signals/` | signal CRUD | `list/get/create/update/delete_signal` |
| `entities/` | entities & graph | `list/get_entity`, `get_entity_wiki`, `add_entity_relation` |
| `search/` | semantic search & RAG | `ai_status`, `semantic_search`, `ask`, `reindex_embeddings` |
| `funding/` | investment / financing | `list/get/create/update/delete_funding`, `funding_trends` |
| `daily/` | Daily Boost | `get/list/generate_daily_digest` |
| `notify/` | outbound push (Feishu/Lark) | `send_feishu` |
| `websearch/` | free web search & source check | `search_web`, `find_primary_source` |
| `_client.py` | shared HTTP plumbing (not a tool) | `request`, `clean`, `VALID_RELATION_TYPES` |

> `notify`/`websearch` don't hit the backend (`send_feishu` posts to a Feishu
> webhook; `websearch` queries DuckDuckGo). They power the alert agent's push &
> cross-verification. `send_feishu` is a `WRITE_TOOLS` member (side-effecting).

All tools call the FastAPI backend over HTTP (never the DB directly) and return
JSON-serialisable values — on failure they return `{"error": ...}` instead of raising.

## Usage

```python
from tools.sources import list_sources          # one specific tool
from tools import READONLY_TOOLS, WRITE_TOOLS    # curated lists for agents
```

`READONLY_TOOLS` are safe to expose anywhere; `WRITE_TOOLS` mutate data and
should be gated behind confirmation in production.

## Config (env)

- `KB_API_BASE_URL` — backend base URL (default `http://localhost:8000`)
- `KB_API_TIMEOUT` — per-request timeout in seconds (default `30`)

## Adding a tool

1. Add an `async def` to the relevant domain package's `__init__.py` (or create a
   new domain directory + `__init__.py`).
2. Export it in that package's `__all__`.
3. Register it in `tools/__init__.py` under `READONLY_TOOLS` or `WRITE_TOOLS`.
