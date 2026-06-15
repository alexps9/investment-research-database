# agent/

AutoGen-based **multi-agent system** for the HH-Research knowledge base.

It ships three specialists:

- **Data Agent** (`data_agent/`) — reads, writes and analyses the KB (sources,
  signals, entities, funding, daily digests) through the atomic [`tools/`](../tools)
  and composed [`skills/`](../skills). It's the round-robin chat participant.
- **Alert Agent** (`alert_agent/`) — real-time AI-industry signal triage. It judges
  fetched signals (Twitter/RSS/media), writes a one-line Chinese summary,
  cross-verifies the primary source, pushes worthy alerts to Feishu, and persists
  them to the KB. It's **pipeline-driven** (processed per-signal), not a chat
  participant — see [`alert_agent/README.md`](alert_agent/README.md).
- **Digest Agent** (`digest_agent/`) — the HH Research Daily writer. It buckets the
  day's KB signals into headline / capital / frontier / industry arrays, ranks
  headline candidates with `skills.headline_selection`, then curates + writes a
  ≤15-card Feishu-XML 精选日报 and can publish it. Also **pipeline-driven** — see
  [`digest_agent/README.md`](digest_agent/README.md).

Each agent lives in **its own directory** under `agent/` (named after the agent):

```
agent/
  config.py            # OpenAI-compatible model client (DeepSeek by default)
  team.py              # build_team() + build_alert_agent() + build_digest_agent()
  main.py              # CLI entrypoint (chat team)
  data_agent/          # the Data Agent (tools + skills + system prompt)
    __init__.py
  alert_agent/         # the Alert Agent + its fetch/triage/prefilter pipeline
    __init__.py        #   build_alert_agent() + prompts
    pipeline.py        #   fetch → triage → prefilter → agent judge → push/persist
    fetcher.py store.py prefilter.py approve.py config/
  digest_agent/        # the Digest Agent (daily brief writer)
    __init__.py        #   build_digest_agent() + DIGEST_AGENT_SYSTEM_MESSAGE
    pipeline.py        #   bucket KB signals → rank headlines → agent writes → push

# The v8.0 HeadlineClassifier + HeadlineSelector are vendored in the shared
# skills/headline package (used by the alert prefilter AND digest headline ranking).
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

# Alert pipeline (real-time signal triage → Feishu + KB)
pip install -r agent/alert_agent/requirements.txt
python -m agent.alert_agent.pipeline --limit 5

# Digest pipeline (curate the day's signals → HH Research Daily XML)
pip install -r agent/digest_agent/requirements.txt
python -m agent.digest_agent.pipeline --date 2026-06-15
```

Example tasks:
- "Generate today's daily brief covering the last 7 days."
- "Find potential duplicate signals and propose which to archive."
- "Summarise the funding landscape by sector."
- "Search semantically for researchers working on embodied AI."

## Extending the team

Create a new specialist in its own directory `agent/<agent_name>/` with an
`__init__.py` exposing a `build_<agent_name>()` factory, then build it in
`team.py`'s `build_team()` and append it to `participants`. For role-based routing
consider switching `RoundRobinGroupChat` to `SelectorGroupChat` (AutoGen 0.7).

## Safety

Mutating tools (`create_*`, `update_*`, `delete_*`) are exposed to the Data Agent.
The system prompt requires it to state intended changes first and forbids bulk
deletes without explicit confirmation. For production, gate `WRITE_TOOLS` behind a
human-approval step.
