# digest_agent

The **HH Research Daily** writer — an AutoGen refactor of the standalone `digest`
subsystem (public repo, `add-digest-agent` branch). It turns the day's knowledge-base
signals into a ≤15-card **精选制** daily brief in Feishu-XML.

```
KB signals + funding ──► bucket (deterministic) ──► rank headlines ──► curate + write (LLM) ──► (optional) push
  list_signals/funding      pipeline.py              skills.headline_selection   digest_agent (AutoGen)   send_feishu
```

## What changed vs the original `digest` pipeline

The original `hh_research.pipeline.daily` collected signals from a Feishu Bitable and
made bespoke Claude calls to curate + write the brief. Here:

- **Source of truth is the project KB** (`/api/signals`, `/api/funding`) — the backend
  stays the single DB owner; this agent only reads via `tools`.
- **One AutoGen `AssistantAgent`** (shared DeepSeek client) does the curation + writing,
  driven by the v7.0 精选制 system prompt (ported from `config/prompts/daily_digest.md`
  + `taxonomy.md`).
- Reusable pieces were hoisted into the project:
  - headline ranking → **`skills.headline_selection.select_headlines`** (wraps the shared
    `skills/headline` v8.0 classifier + selector — the same vendored brain the alert
    prefilter uses).
  - publish → **`tools.notify.send_feishu`**.
- Deterministic **bucketing** of the day's signals into the four payload arrays
  (`HEADLINE_CANDIDATES` / `CAPITAL_SIGNALS` / `FRONTIER_RESEARCH_SIGNALS` /
  `INDUSTRY_APPLICATION_SIGNALS`) lives in `pipeline.py`.

## Run

```bash
pip install -r agent/requirements.txt -r agent/digest_agent/requirements.txt
cp agent/digest_agent/.env.example agent/digest_agent/.env   # fill LLM_API_KEY (+ webhook for --publish)

python -m agent.digest_agent.pipeline                 # today (UTC), writes XML, no push
python -m agent.digest_agent.pipeline --date 2026-06-15
python -m agent.digest_agent.pipeline --window-days 1 --publish
```

The brief is written to `data/digests/HH-Research-Daily-{date}.xml`. With `--publish`
the agent also pushes it to Feishu via the configured webhook (dry-run if unset).

## Layout

```
digest_agent/
  __init__.py     build_digest_agent + DIGEST_AGENT_SYSTEM_MESSAGE + format_payload_for_agent
  pipeline.py     deterministic bucketing/ranking + agent orchestration (CLI)
  requirements.txt / .env.example / .gitignore
```

The v8.0 headline classifier + selector live in the shared `skills/headline`
support package (also used by `agent/alert_agent`).
