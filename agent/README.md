# agent/

AutoGen-based **multi-agent system** for the HH-Research knowledge base.

It currently ships one specialist — the **Data Agent** — which reads, writes and
analyses the KB (sources, signals, entities, funding, daily digests) through the
atomic [`tools/`](../tools) and composed [`skills/`](../skills). The team is built
so additional specialists can be added later.

```
agent/
  config.py            # OpenAI-compatible model client (DeepSeek by default)
  team.py              # build_team(): RoundRobinGroupChat of specialists
  main.py              # CLI entrypoint
  agents/
    data_agent.py      # the Data Agent (tools + skills + system prompt)
```

## Architecture

```
            ┌────────────── agent/ (AutoGen team) ──────────────┐
 task ───►  │  data_agent  ── tools/ + skills/  ──► HTTP /api/* │
            └───────────────────────────────────────────────────┘
                                                       │
                                          FastAPI backend ──► PostgreSQL
```

The agent never touches the database directly — it only calls backend endpoints,
keeping PostgreSQL as the single source of truth.

## Setup

```bash
pip install -r agent/requirements.txt
cp agent/.env.example agent/.env   # then fill in LLM_API_KEY and KB_API_BASE_URL
```

## Run (from the repo root)

```bash
# One-shot task
python -m agent.main "Audit source data quality and list the worst offenders"

# Interactive
python -m agent.main
```

Example tasks:
- "Generate today's daily brief covering the last 7 days."
- "Find potential duplicate signals and propose which to archive."
- "Summarise the funding landscape by sector."
- "Search semantically for researchers working on embodied AI."

## Extending the team

Add a new specialist in `agents/`, build it in `team.py`'s `build_team()` and
append it to `participants`. For role-based routing consider switching
`RoundRobinGroupChat` to `SelectorGroupChat` (AutoGen 0.7).

## Safety

Mutating tools (`create_*`, `update_*`, `delete_*`) are exposed to the Data Agent.
The system prompt requires it to state intended changes first and forbids bulk
deletes without explicit confirmation. For production, gate `WRITE_TOOLS` behind a
human-approval step.
