# skills/

Composed, higher-level **workflows** built on top of the atomic functions in
[`tools/`](../tools). Where a *tool* maps 1:1 to a backend endpoint, a *skill*
chains several tools together and returns a human-readable (markdown) result.

**Each skill has its own directory, named after its function:**

| Directory | Skill | What it does | Tools used |
|-----------|-------|--------------|------------|
| `source_quality_audit/` | `audit_source_quality()` | Reports sources missing key fields | `tools.sources.list_sources` |
| `duplicate_signals/` | `find_duplicate_signals()` | Flags signals with duplicate titles | `tools.signals.list_signals` |
| `daily_brief/` | `daily_brief(window_days)` | Generates the Daily Boost digest | `tools.daily.generate_daily_digest` |
| `funding_summary/` | `funding_landscape_summary()` | Summarises funding trends | `tools.funding.funding_trends` |
| `rag_answer/` | `answer_with_sources(question)` | RAG answer with cited sources | `tools.search.ask` |
| `signal_triage/` | `triage_signals(signals)` | Deterministic tier/engagement scoring, cross-language triangulation & cluster-dedup of a batch of raw signals | none (pure logic; jieba optional) |
| `headline_selection/` | `select_headlines(signals)` | Classify (v8.0 m1–m5 + 8 strong constraints) and rank a batch of signals into auto-headline / edge / body tiers | none (pure logic; uses `skills.headline`) |

> `signal_triage` and `headline_selection` are the exceptions to "skills call tools":
> they're pure, deterministic signal-engineering (no backend). `signal_triage` is used
> by `agent/alert_agent/pipeline.py`; `headline_selection` is used by
> `agent/digest_agent/pipeline.py` to pick headline candidates. Both are sync and
> return JSON-serialisable dicts.

### Support packages (not skills)

| Directory | What it is |
|-----------|------------|
| `headline/` | Vendored HH-Research **v8.0 HeadlineClassifier + HeadlineSelector** (`schemas`, `canonical_entity`, `headline_classifier`, `headline_selector`, `whitelist`). Shared by `agent/alert_agent` (prefilter) and `skills.headline_selection`. Carries **no** `SKILLS` entry. |

## Usage

```python
import asyncio
from skills.daily_brief import daily_brief   # one specific skill
from skills import SKILLS                     # all skills, for agents

print(asyncio.run(daily_brief(window_days=7)))
```

## Adding a skill

1. Create a directory `skills/<function_name>/` with an `__init__.py`.
2. Add an `async def` that composes calls from the `tools.*` packages; return a
   string or JSON-serialisable value, and export it in `__all__`.
3. Import it into `skills/__init__.py` and append it to `SKILLS`.
4. Keep a clear docstring — agents use it as the tool description.
