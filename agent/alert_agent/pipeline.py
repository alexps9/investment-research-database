"""Alert pipeline — AutoGen refactor of the original ``alert/main.py``.

Flow:
    fetch (Twitter / RSS / media)        -> alert_agent.fetcher        [deterministic]
    score + triangulate + dedupe         -> skills.signal_triage       [deterministic]
    prefilter obvious noise (optional)   -> alert_agent.prefilter      [deterministic]
    judge + summary + verify + push/save -> alert_agent (AutoGen)      [LLM-driven]

The heavy, tuned signal-engineering stays deterministic (cheap, reproducible);
only the per-signal judgement/summary/verification is delegated to the AutoGen
``alert_agent``, which acts via tools (find_primary_source / send_feishu /
create_signal / semantic_search).

Run from the repo root:

    python -m agent.alert_agent.pipeline            # full run
    python -m agent.alert_agent.pipeline --limit 5  # cap signals processed
    python -m agent.alert_agent.pipeline --no-twitter

Env (repo .env / agent/.env / agent/alert_agent/.env):
    LLM_API_KEY / DEEPSEEK_API_KEY   chat model key (required)
    KB_API_BASE_URL                  backend URL (default http://localhost:8000)
    TWITTERAPI_IO_KEY                X fetch (optional; skipped if unset)
    FEISHU_WEBHOOK_URL               push target (optional; dry-run if unset)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
    load_dotenv(_REPO_ROOT / "agent" / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

from autogen_agentchat.ui import Console  # noqa: E402

from agent.config import get_model_client  # noqa: E402
from agent.alert_agent import build_alert_agent, format_signal_for_agent  # noqa: E402
from agent.alert_agent.fetcher import (  # noqa: E402
    fetch_all, fetch_rss, fetch_media_rss, fetch_article_text,
    load_whitelist_accounts, P0PLUS_COMPANY_HANDLES,
)
from agent.alert_agent.prefilter import prefilter  # noqa: E402
from agent.alert_agent.store import Store  # noqa: E402
from skills.signal_triage import triage_signals  # noqa: E402

ALERT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ALERT_DIR / "config" / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch_signals(config: dict, run_twitter: bool) -> list[dict]:
    """Deterministic acquisition: Twitter (optional) + official RSS + media RSS."""
    freshness = config.get("freshness_hours", 2)
    media_freshness = config.get("media_freshness_hours", 6)

    try:
        accounts = load_whitelist_accounts()
    except Exception as exc:
        print(f"  [WARN] whitelist load failed ({exc}); using config.json fallback")
        accounts = config.get("p0_accounts", [])

    signals: list[dict] = []
    if run_twitter and accounts:
        current_hour = int(time.strftime("%H"))
        window = freshness if (current_hour >= 20 or current_hour < 10) else 6
        try:
            signals.extend(fetch_all(accounts, window))
        except Exception as exc:
            print(f"  [WARN] twitter fetch failed: {exc}")
    else:
        print("  Skipping Twitter (disabled or no key); RSS + media only")

    try:
        signals.extend(fetch_rss(freshness))
    except Exception as exc:
        print(f"  [WARN] rss fetch failed: {exc}")
    try:
        signals.extend(fetch_media_rss(media_freshness))
    except Exception as exc:
        print(f"  [WARN] media fetch failed: {exc}")
    return signals


def enrich_article_text(signals: list[dict]) -> int:
    """Fetch article body for short RSS / link-only items (improves judgement)."""
    enriched = 0
    for t in signals:
        text_len = len(t.get("text", ""))
        has_ext_url = bool(t.get("ext_urls"))
        is_rss = t.get("source_tier") in ("media", "official")
        short_twitter_link = (
            text_len < 200 and has_ext_url and t.get("source_tier") == "twitter"
        )
        if (is_rss and text_len < 300) or short_twitter_link:
            url = t["ext_urls"][0] if has_ext_url else t.get("url", "")
            try:
                body = fetch_article_text(url)
            except Exception:
                body = ""
            if body and len(body) > text_len:
                t["text"] = f"{t['text']}\n\n[正文] {body}"
                enriched += 1
            time.sleep(1)
    return enriched


def prefilter_keep(signal: dict) -> bool:
    """Cheap deterministic gate: drop obvious noise before spending an LLM call.
    P0+ official accounts / official RSS always pass through."""
    is_p0plus = signal.get("username", "").lower() in P0PLUS_COMPANY_HANDLES
    is_official_rss = signal.get("source_tier") == "official"
    if is_p0plus or is_official_rss:
        return True
    try:
        pf = prefilter(signal)
    except Exception:
        return True  # prefilter unavailable -> let the agent decide
    return pf.get("action") != "skip"


async def run(limit: int | None = None, run_twitter: bool = True) -> None:
    config = load_config()

    print(f"[{time.strftime('%H:%M:%S')}] Alert pipeline start")
    raw = fetch_signals(config, run_twitter)
    print(f"  Fetched {len(raw)} raw signals")
    if not raw:
        print("  No signals, done.")
        return

    store = Store()
    fresh = [t for t in raw if not store.is_sent(t.get("tweet_id", ""))]
    print(f"  {len(fresh)} unseen after dedup")
    if not fresh:
        store.close()
        return

    # Deterministic signal engineering (tier / engagement / triangulation / dedup).
    triaged = triage_signals(fresh)
    candidates = triaged["deduped"]
    print(f"  Triaged: {triaged['verified_count']} multi-source verified, "
          f"{len(candidates)} candidates after cluster-dedup")

    enriched = enrich_article_text(candidates)
    if enriched:
        print(f"  Enriched {enriched} items with article body")

    candidates = [s for s in candidates if prefilter_keep(s)]
    print(f"  {len(candidates)} candidates pass prefilter")
    if limit is not None:
        candidates = candidates[:limit]
        print(f"  Capped to {len(candidates)} (limit={limit})")

    if not candidates:
        store.close()
        return

    model_client = get_model_client()
    try:
        for i, sig in enumerate(candidates, 1):
            print(f"\n── [{i}/{len(candidates)}] @{sig.get('username', '?')}: "
                  f"{sig.get('text', '')[:60]}...")
            agent = build_alert_agent(model_client)
            task = "请处理以下候选信号（按系统指示判别 → 摘要 → 验证 → 推送/落库）：\n\n" \
                   + format_signal_for_agent(sig)
            try:
                await Console(agent.run_stream(task=task))
            except Exception as exc:
                print(f"  [WARN] agent run failed: {exc}")
            # Mark the tweet seen so it isn't reprocessed next run (event-level
            # dedup + KB dedup are handled by the agent via semantic_search and
            # the unique-url constraint on create_signal).
            store.mark_sent(
                sig.get("tweet_id", ""), sig.get("username", ""), "", "", "",
                sig.get("text", "")[:200], sig.get("tier", ""),
            )
    finally:
        await model_client.close()
        store.close()

    print(f"\n[{time.strftime('%H:%M:%S')}] Done. Processed {len(candidates)} candidates.")


def main() -> None:
    parser = argparse.ArgumentParser(description="HH-Research alert pipeline (AutoGen).")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the number of candidate signals processed")
    parser.add_argument("--no-twitter", action="store_true",
                        help="skip Twitter fetch (RSS + media only)")
    args = parser.parse_args()
    asyncio.run(run(limit=args.limit, run_twitter=not args.no_twitter))


if __name__ == "__main__":
    main()
