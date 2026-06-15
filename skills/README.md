# skills/

Composed, higher-level **workflows** built on top of the atomic functions in
[`tools/`](../tools). Where a *tool* maps 1:1 to a backend endpoint, a *skill*
chains several tools together and returns a human-readable (markdown) result.

| Skill | What it does | Tools used |
|-------|--------------|------------|
| `audit_source_quality()` | Reports sources missing key fields (tier/sector/org/…) | `list_sources` |
| `find_duplicate_signals()` | Flags signals with duplicate normalised titles | `list_signals` |
| `daily_brief(window_days)` | Generates the Daily Boost digest as markdown | `generate_daily_digest` |
| `funding_landscape_summary()` | Summarises funding trends by sector/round/month | `funding_trends` |
| `answer_with_sources(question)` | RAG answer with cited sources appended | `ask` |

## Usage

```python
import asyncio
from skills import daily_brief

print(asyncio.run(daily_brief(window_days=7)))
```

Skills are also registered as agent tools — see [`agent/`](../agent).

## Adding a skill

1. Add an `async def` to a module here (or a new module).
2. Compose calls from `tools.kb_client`; return a string or JSON-serialisable value.
3. Append it to `SKILLS` in `skills/__init__.py`.
4. Keep a clear docstring — agents use it as the tool description.
