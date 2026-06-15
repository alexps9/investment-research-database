"""Ingestion agent — fetch external sources and create signals in the KB."""
from __future__ import annotations

import json
import time
from pathlib import Path

from tools._client import request
from tools.signals import create_signal

from agent.alert_agent.fetcher import (
    fetch_all,
    fetch_article_text,
    fetch_media_rss,
    fetch_rss,
    load_whitelist_accounts,
)
from skills.signal_triage import triage_signals

ALERT_DIR = Path(__file__).resolve().parents[1] / "alert_agent"
CONFIG_PATH = ALERT_DIR / "config" / "config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _fetch_raw(config: dict, run_twitter: bool) -> list[dict]:
    freshness = config.get("freshness_hours", 2)
    media_freshness = config.get("media_freshness_hours", 6)
    try:
        accounts = load_whitelist_accounts()
    except Exception:
        accounts = config.get("p0_accounts", [])

    signals: list[dict] = []
    if run_twitter and accounts:
        current_hour = int(time.strftime("%H"))
        window = freshness if (current_hour >= 20 or current_hour < 10) else 6
        try:
            signals.extend(fetch_all(accounts, window))
        except Exception as exc:
            print(f"  [WARN] twitter fetch failed: {exc}")
    try:
        signals.extend(fetch_rss(freshness))
    except Exception as exc:
        print(f"  [WARN] rss fetch failed: {exc}")
    try:
        signals.extend(fetch_media_rss(media_freshness))
    except Exception as exc:
        print(f"  [WARN] media fetch failed: {exc}")
    return signals


def _enrich_text(items: list[dict]) -> None:
    for item in items:
        text_len = len(item.get("text", ""))
        has_ext_url = bool(item.get("ext_urls"))
        is_rss = item.get("source_tier") in ("media", "official")
        short_twitter = text_len < 200 and has_ext_url and item.get("source_tier") == "twitter"
        if (is_rss and text_len < 300) or short_twitter:
            url = item["ext_urls"][0] if has_ext_url else item.get("url", "")
            try:
                body = fetch_article_text(url)
            except Exception:
                body = ""
            if body and len(body) > text_len:
                item["text"] = f"{item['text']}\n\n[正文] {body}"
            time.sleep(0.5)


def _map_signal_type(item: dict) -> str:
    tier = item.get("source_tier", "")
    if tier == "official":
        return "news"
    if tier == "media":
        return "news"
    return "tweet"


async def _log_run(total: int, success: int, failed: int) -> None:
    await request(
        "POST",
        "/runs/mock",
        json={
            "run_type": "collect",
            "status": "success" if failed == 0 else "partial",
            "total_items": total,
            "success_items": success,
            "failed_items": failed,
        },
    )


async def run_ingestion(
    *,
    run_twitter: bool = True,
    limit: int | None = None,
) -> dict:
    """Fetch, triage, and persist new signals. Returns partial pipeline state."""
    config = _load_config()
    raw = _fetch_raw(config, run_twitter)
    print(f"  Ingestion: fetched {len(raw)} raw items")
    if not raw:
        await _log_run(0, 0, 0)
        return {"raw_items": [], "signals": [], "run_meta": {"ingested": 0}}

    triaged = triage_signals(raw)
    candidates = triaged.get("deduped") or triaged.get("scored") or []
    _enrich_text(candidates)
    if limit is not None:
        candidates = candidates[:limit]

    created: list[dict] = []
    errors: list[str] = []
    for item in candidates:
        title = (item.get("text") or item.get("title") or "untitled")[:200]
        url = item.get("url") or f"https://x.com/{item.get('username', 'unknown')}/status/{item.get('tweet_id', '0')}"
        abstract = (item.get("text") or "")[:2000]
        published_at = item.get("published_at") or item.get("created_at")
        result = await create_signal(
            title=title,
            url=url,
            signal_type=_map_signal_type(item),
            abstract=abstract,
            published_at=published_at,
            status="collected",
        )
        if isinstance(result, dict) and result.get("error"):
            if "duplicate" in str(result.get("error", "")).lower() or result.get("status_code") == 409:
                continue
            errors.append(f"create_signal failed for {url}: {result}")
            continue
        created.append(result if isinstance(result, dict) else {"raw": result})

    await _log_run(len(candidates), len(created), len(errors))
    print(f"  Ingestion: created {len(created)} signals ({len(errors)} errors)")
    return {
        "raw_items": raw,
        "signals": created,
        "errors": errors,
        "run_meta": {"ingested": len(created), "raw_count": len(raw)},
    }


async def ingestion_node(state: dict) -> dict:
    """LangGraph node wrapper."""
    run_meta = state.get("run_meta") or {}
    result = await run_ingestion(
        run_twitter=run_meta.get("run_twitter", True),
        limit=run_meta.get("limit"),
    )
    return result
