#!/usr/bin/env python3
"""Alert pipeline: fetch → classify → send."""

import json
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fetcher import fetch_all, fetch_rss, fetch_media_rss, fetch_article_text, load_whitelist_accounts
from classifier import classify
from sender import format_alert, send_feishu
from store import Store, _TIER_RANK
from score import score_signals, dedupe_clusters
from reviewer import review_alert
from verifier import cross_verify
from prefilter import prefilter
from fetcher import P0PLUS_COMPANY_HANDLES

ALERT_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_DIR = os.path.join(ALERT_DIR, "pending")

# 需要人工审核的源（中文媒体 RSS），推送前先进 pending 队列等待确认。
REVIEW_QUEUE_SOURCES = {"36Kr", "36氪快讯", "IT之家", "宝玉", "雷锋网AI", "晚点LatePost"}
CONFIG_PATH = os.path.join(ALERT_DIR, "config", "config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def run():
    config = load_config()
    # Try whitelist yml first, fallback to config.json
    try:
        accounts = load_whitelist_accounts()
        print(f"  Loaded {len(accounts)} accounts from whitelist yml")
    except Exception as e:
        print(f"  [WARN] whitelist load failed ({e}), using config.json fallback")
        accounts = config["p0_accounts"]
    freshness_hours = config.get("freshness_hours", 2)
    media_freshness_hours = config.get("media_freshness_hours", 6)

    print(f"[{time.strftime('%H:%M:%S')}] Alert pipeline start")
    print(f"  Monitoring {len(accounts)} accounts, freshness={freshness_hours}h\n")


    # 1. Fetch (Twitter + RSS + Media)
    # Twitter: 20:00-10:00 每小时（美欧活跃时段），10:00-20:00 每3小时。
    # RSS + 中文媒体每小时都跑（便宜，中国 AI 新闻白天出）。
    current_hour = int(time.strftime("%H"))
    if current_hour >= 20 or current_hour < 10:
        run_twitter = True  # 晚8点到早10点：每小时
    else:
        run_twitter = (current_hour % 3 == 1)  # 白天：10,13,16,19 点

    if run_twitter:
        twitter_window = freshness_hours if (current_hour >= 20 or current_hour < 10) else 6
        tweets = fetch_all(accounts, twitter_window)
    else:
        print(f"  Skipping Twitter this hour (next: every 3h during daytime); RSS + media only")
        tweets = []
    rss_items = fetch_rss(freshness_hours)
    tweets.extend(rss_items)
    media_items = fetch_media_rss(media_freshness_hours)
    tweets.extend(media_items)
    print(f"\n  Total: {len(tweets)} signals (tweets + RSS + media)\n")

    if not tweets:
        print("  No new signals, done.")
        return

    # 2. Deduplicate
    store = Store()
    new_tweets = [t for t in tweets if not store.is_sent(t["tweet_id"])]
    print(f"  After dedup: {len(new_tweets)} unseen tweets\n")

    if not new_tweets:
        print("  All tweets already processed, done.")
        store.close()
        return

    # 2b. Score & triangulate (迭代 A'): tier 分级 + engagement 评分 + 多源印证
    score_signals(new_tweets)
    verified_n = sum(1 for t in new_tweets if t.get("verified"))
    print(f"  Scored {len(new_tweets)} signals; {verified_n} multi-source verified\n")

    # 2b'. Cluster dedup（Thomas 的 pool 去重）：同一事件被多源各报时，只推 tier
    # 最高的一条代表（官方>媒体>聚合），代表已带全簇「✅多源证实」标记。避免刷屏。
    before = len(new_tweets)
    new_tweets = dedupe_clusters(new_tweets)
    if len(new_tweets) < before:
        print(f"  Cluster dedup: {before} → {len(new_tweets)} (合并多源同一事件)\n")

    # 2c. Prefilter on ORIGINAL text (before enrichment inflates content).
    # Store prefilter results keyed by tweet_id so we can use them in step 3.
    prefilter_results = {}
    for t in new_tweets:
        prefilter_results[t["tweet_id"]] = prefilter(t)

    # 2d. Full-text enrichment: fetch article body for signals with short text + links.
    # Covers: RSS/media (title-only), P0+ Twitter with link-only tweets.
    enriched = 0
    for t in new_tweets:
        text_len = len(t.get("text", ""))
        has_ext_url = bool(t.get("ext_urls"))
        is_rss = t.get("source_tier") in ("media", "official")
        is_short_twitter_with_link = (text_len < 200 and has_ext_url and t.get("source_tier") == "twitter")
        if (is_rss and text_len < 300) or is_short_twitter_with_link:
            url = t["ext_urls"][0] if has_ext_url else t.get("url", "")
            body = fetch_article_text(url)
            if body and len(body) > text_len:
                t["text"] = f"{t['text']}\n\n[正文] {body}"
                enriched += 1
            time.sleep(1)
    if enriched:
        print(f"  Enriched {enriched} items with article body\n")

    # 3. Classify + Send
    sent_count = 0
    prefilter_skip = 0
    prefilter_pass = 0
    for tweet in new_tweets:
        # Stage 0: Use pre-computed prefilter result (ran on original text)
        pf = prefilter_results[tweet["tweet_id"]]
        is_p0plus_official = tweet.get("username", "").lower() in P0PLUS_COMPANY_HANDLES
        # Official RSS (company blogs from rss_feeds.yaml) = same trust as P0+ Twitter
        is_official_rss = tweet.get("source_tier") == "official"

        # P0+ official accounts / official RSS: never skip (guaranteed to reach LLM judge)
        if pf["action"] == "skip" and not is_p0plus_official and not is_official_rss:
            prefilter_skip += 1
            store.mark_sent(tweet["tweet_id"], tweet["username"], "prefilter-skip", "", "", "")
            continue

        print(f"  Classifying @{tweet['username']}: {tweet['text'][:60]}...")

        # skip_judge only when prefilter strong constraint passes (deterministic high-signal)
        skip_judge = pf["action"] == "pass"
        if skip_judge:
            prefilter_pass += 1
            print(f"    → Prefilter pass ({pf['constraint_rule']})")
            result = classify(tweet, skip_judge=True)
        else:
            # Borderline or P0+ not passing strong constraint — full LLM classify
            result = classify(tweet)

        if not result or (result.get("should_alert") and not result.get("summary")):
            time.sleep(3)
            result = classify(tweet, skip_judge=skip_judge)

        if not result:
            continue

        if not result.get("should_alert"):
            print(f"    → Skip ({result.get('reason', 'no alert')})")
            store.mark_sent(tweet["tweet_id"], tweet["username"], "skipped", "", "", "")
            continue

        summary = result.get("summary") or ""
        if not summary.strip():
            print(f"    → Skip (empty summary after retry)")
            continue

        # Event-level dedup: skip if similar event already pushed recently,
        # UNLESS an official first-hand source (tier_1a/1b) confirms what was
        # previously only reported by media/aggregators → upgrade push.
        prior = store.find_duplicate_event(summary)
        if prior:
            new_tier = tweet.get("tier", "")
            old_tier = prior.get("tier", "")
            is_upgrade = (
                new_tier in ("tier_1a", "tier_1b")
                and _TIER_RANK.get(new_tier, 0) > _TIER_RANK.get(old_tier, 0)
            )
            if is_upgrade:
                upgrade_msg = f"✅ 官方确认：{summary}\n\n🔗 {tweet.get('url', '')}"
                print(f"    → Upgrade push (tier {old_tier} → {new_tier}): {summary[:40]}")
                send_feishu(upgrade_msg)
                sent_count += 1
                store.mark_sent(tweet["tweet_id"], tweet["username"], result.get("event_type", ""), result.get("priority", ""), upgrade_msg, summary, new_tier)
            else:
                print(f"    → Duplicate event, skipping: {summary[:40]}")
                store.mark_sent(tweet["tweet_id"], tweet["username"], result.get("event_type", ""), result.get("priority", ""), "", summary, new_tier)
            continue

        # 4. Pre-send review (迭代 G): final skeptical pass — catches stale news
        # (RSS re-timestamping), duplicates, exaggeration, borderline items.
        verdict = review_alert(tweet, result)
        if not verdict.get("approve"):
            print(f"    → Review rejected: {verdict.get('reason', '')}")
            store.mark_sent(tweet["tweet_id"], tweet["username"], "review-rejected", "", "", summary)
            continue

        # Cross-verify: find authoritative primary source
        alert_date = time.strftime("%Y-%m-%d")
        primary = cross_verify(summary, alert_date=alert_date)
        if primary:
            result["primary_source"] = primary
            print(f"    → Verified: [{primary['domain']}] {primary['title'][:50]}")

        # Format and send
        message = format_alert(tweet, result)
        print(f"    → ALERT [{result['event_type']}] {summary}")

        # pending_all 模式：所有 alert 进 pending 队列（临时人工全审）
        # 媒体信号（source_tier=media）默认进 pending 等人工确认；
        # 但 trust=high 的信任源（如 TechCrunch AI，见 media_feeds.yaml）绕过 pending 直接推。
        force_pending = config.get("pending_all", False)
        is_trusted = tweet.get("trust") == "high"
        is_media = tweet.get("source_tier") == "media" and not is_trusted
        if force_pending or is_media:
            _save_pending(tweet, result, message)
            print(f"    → Pending (needs approval)")
            # 存真实 message（非空）：pending = 已排队待送达用户，应参与后续判重，
            # 避免同一事件被多个媒体源各报一次、在 pending 里堆重复。
            store.mark_sent(tweet["tweet_id"], tweet["username"], result.get("event_type", ""), result.get("priority", ""), message, summary, tweet.get("tier", ""))
            continue

        ok = send_feishu(message)
        if ok:
            print(f"    → Sent!")
            sent_count += 1

        store.mark_sent(
            tweet["tweet_id"],
            tweet["username"],
            result.get("event_type", ""),
            result.get("priority", ""),
            message,
            summary,
            tweet.get("tier", ""),
        )

        time.sleep(1)

    store.close()
    if prefilter_skip:
        print(f"  Prefilter: {prefilter_skip} skipped (noise), {prefilter_pass} auto-pass (strong constraint)")
    print(f"\n[{time.strftime('%H:%M:%S')}] Done. Sent {sent_count} alerts.")


_PENDING_BATCH_FILE = None  # current batch file path (one per pipeline run)
_PENDING_BATCH_COUNT = 0


def _save_pending(tweet: dict, result: dict, message: str):
    """将待审核消息追加到本轮 batch 文件（pending/batch_<timestamp>.json）。"""
    global _PENDING_BATCH_FILE, _PENDING_BATCH_COUNT
    os.makedirs(PENDING_DIR, exist_ok=True)

    item = {
        "tweet_id": tweet.get("tweet_id", ""),
        "username": tweet.get("username", ""),
        "url": tweet.get("url", ""),
        "summary": result.get("summary", ""),
        "event_type": result.get("event_type", ""),
        "message": message,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 首次调用时创建本轮 batch 文件
    if _PENDING_BATCH_FILE is None:
        fname = f"batch_{time.strftime('%Y%m%d%H%M')}.json"
        _PENDING_BATCH_FILE = os.path.join(PENDING_DIR, fname)
        with open(_PENDING_BATCH_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    # 追加到 batch
    with open(_PENDING_BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)
    batch.append(item)
    with open(_PENDING_BATCH_FILE, "w", encoding="utf-8") as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    _PENDING_BATCH_COUNT = len(batch)

    # macOS 系统通知
    os.system(
        f'osascript -e \'display notification "{item["summary"][:60]}" '
        f'with title "日报Alert 待审核" subtitle "本轮第 {_PENDING_BATCH_COUNT} 条"\''
    )


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n[FATAL] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
