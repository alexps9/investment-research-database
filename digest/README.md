# digest/

**HH Research Daily** — the AI investment-research daily-brief subsystem.

A self-contained pipeline that collects signals (arXiv / X / RSS / OpenAlex),
extracts and scores them with Claude, curates a ≤15-signal daily brief
(headlines + tracks + capital moves), and publishes it to Feishu. It sits
alongside [`../alert/`](../alert) as another **data subsystem** in this
multi-agent knowledge base: each subsystem ingests and processes signals
independently, then feeds the central backend KB.

```
external sources ──► collect ──► extract (Claude) ──► curate digest ──► publish (Feishu)
   arXiv / X /          │            signals +            daily brief        群 / 订阅 / H Link
   RSS / OpenAlex        │            analysis              (≤15 signals)
                         └──► (phase 2) kb_sync ──► backend /api/* ──► PostgreSQL KB
```

## Layout

```
digest/
  src/hh_research/
    collectors/   arxiv · x · rss · openalex
    extract/      signal_extractor · daily_writer · author_enricher · claude_client · researcher_mapping/
    publish/      feishu_bot · lark_doc · hlink · digest_index · feishu_anchor
    pipeline/     daily · headline_selector · headline_classifier · canonical_entity
    quality/      digest_rules            storage/  bitable_client · sqlite_dedup · schemas
    utils/        time · logger · preflight
  config/         prompts/daily_digest.md · rss_feeds.yaml · p0_whitelist.yml (信号源 tier 白名单)
  scripts/        run_pipeline · publish_with_anchors · send_*_form_a · broadcast_*
  data/digests/   the daily briefs (committed — used downstream for signal extraction)
  data/signal_sources/   source catalogue snapshots
  tests/          pytest suite
  PROJECT.md · ONBOARDING_INSIGHTS.md   design notes & the investment-insights writing guide
```

## Status & integration with the KB

- **Today**: the pipeline's source-of-truth is a Feishu Bitable (信号 Base); the
  generated briefs land in `data/digests/*.md` and are pushed to Feishu.
- **Phase 2 (planned)**: add `digest/kb_sync.py` to also sync each day's signals
  into the backend over `/api/signals` (mirroring [`../alert/kb_sync.py`](../alert)),
  so digests become first-class KB data — semantically searchable, RAG-queryable,
  and visible in the frontend. Per the repo's golden rule, the backend stays the
  single DB owner; this subsystem will only call `/api/*`, never touch the DB.

The briefs are committed (not gitignored) precisely so the KB can extract and
process signals from them directly.

## Quick start

```bash
cd digest
python -m venv .venv && source .venv/bin/activate
pip install -r <(python -c "import tomllib,sys; d=tomllib.load(open('pyproject.toml','rb')); print('\n'.join(d['project']['dependencies']))") 2>/dev/null || pip install .
cp .env.example .env        # fill in SOCIALDATA / ANTHROPIC keys + Feishu bot creds
# run the daily pipeline (see scripts/ for entrypoints)
python -m hh_research.pipeline.daily
```

## Credentials

All secrets come from `.env` (gitignored; template in `.env.example`): SocialData
(X), Anthropic (Claude), and Feishu bot / Bitable / H Link. Feishu user-auth uses
`lark-cli` profiles. No secrets are committed.
