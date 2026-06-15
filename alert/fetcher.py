"""Fetch recent tweets from P0 accounts via socialdata.tools (primary) or twitterapi.io (fallback)."""

import os
import re
import time
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

# twitterapi.io
TWITTERAPI_KEY = os.environ.get("TWITTERAPI_IO_KEY", "")
TWITTERAPI_BASE = "https://api.twitterapi.io"

WHITELIST_PATH = os.environ.get(
    "WHITELIST_PATH",
    str(Path(__file__).resolve().parent / "config" / "p0_whitelist.yml"),
)


EXTRA_HANDLES = []

# Aggregator / second-hand NEWS accounts: they relay unconfirmed news/rumors
# ("某公司据传…") rather than break it first-hand. Items from these get
# source_tier="aggregator" so the classifier treats their claims as
# "据报道 / 转述", downgrades to medium, and labels the summary accordingly.
#
# Deliberately EXCLUDES paper-relay accounts (_akhaliq, omarsar0,
# arankomatsuzaki): those relay arXiv originals with sources, are low-distortion,
# and should NOT be downgraded as rumors — treat them as normal P0 accounts.
AGGREGATOR_HANDLES = {
    "rohanpaul_ai", "rowancheung", "ai_for_success",
    "bindureddy", "TheHumanoidHub", "PolymarketMoney",
}


def _load_p0plus_company_handles() -> set:
    """Load twitter handles for P0+ company accounts (for bypass logic)."""
    handles = set()
    try:
        with open(WHITELIST_PATH) as f:
            data = yaml.safe_load(f)
        for entity in data.get("entities", []):
            if entity.get("tier") == "P0+" and entity.get("entity_type") == "company":
                twitter = entity.get("twitter") or ""
                match = re.search(r"(?:x|twitter)\.com/([^/?\s\)\]]+)", twitter)
                if match:
                    handles.add(match.group(1).lower())
    except Exception:
        pass
    return handles


P0PLUS_COMPANY_HANDLES = _load_p0plus_company_handles()


def load_whitelist_accounts(tiers=("P0+", "P0")) -> list[str]:
    """Load twitter handles from p0_whitelist.yml, filtered by tier, plus extra handles."""
    with open(WHITELIST_PATH) as f:
        data = yaml.safe_load(f)

    handles = []
    for entity in data.get("entities", []):
        if entity.get("tier") not in tiers:
            continue
        twitter = entity.get("twitter") or ""
        # Format: [https://x.com/handle](https://x.com/handle)
        match = re.search(r"\(https?://(?:x|twitter)\.com/([^/?\s\)]+)\)", twitter)
        if not match:
            match = re.search(r"https?://(?:x|twitter)\.com/([^/?\s\)\]]+)", twitter)
        if match:
            handle = match.group(1)
            if handle not in handles:
                handles.append(handle)

    return handles


def _parse_time(s: str):
    if not s:
        return None
    # twitterapi.io format: "Thu Jun 05 08:30:00 +0000 2026"
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
    except (ValueError, TypeError):
        pass
    # ISO format fallback
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass
    return None


def _fetch_raw_tweets(username: str) -> list:
    """Fetch raw tweet list from twitterapi.io."""
    session = requests.Session()
    session.trust_env = False

    for attempt in range(3):
        try:
            resp = session.get(
                f"{TWITTERAPI_BASE}/twitter/user/last_tweets",
                headers={"X-API-Key": TWITTERAPI_KEY},
                params={"userName": username},
                timeout=20,
            )
            if resp.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("tweets") or data.get("data", {}).get("tweets") or []
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            print(f"  [WARN] @{username} twitterapi fetch failed: {e}")
            return []
    return []


def fetch_user(username: str, freshness_hours: int = 2) -> list:
    """Fetch recent tweets for one user. Returns list of tweet dicts."""
    tweets = _fetch_raw_tweets(username)
    if not tweets:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
    results = []

    for t in tweets:
        tweet_id = t.get("id_str") or t.get("id", "")
        text = t.get("text", "")
        if not tweet_id or not text:
            continue

        raw_time = t.get("createdAt") or t.get("created_at", "")
        pub_time = _parse_time(raw_time)
        if pub_time and pub_time < cutoff:
            continue

        # Skip pure retweets (hard filter)
        if text.startswith("RT @"):
            continue

        # Skip very short replies
        if text.startswith("@") and len(text) < 80:
            continue

        # Extract external links from entities
        ext_urls = []
        for u in t.get("entities", {}).get("urls", []):
            expanded = u.get("expanded_url", "")
            if expanded and "x.com/" not in expanded and "twitter.com/" not in expanded:
                ext_urls.append(expanded)

        results.append({
            "username": username,
            "tweet_id": str(tweet_id),
            "text": text,
            "url": t.get("twitterUrl") or t.get("url") or f"https://x.com/{username}/status/{tweet_id}",
            "created_at": raw_time,
            "likes": t.get("favorite_count") or t.get("likeCount") or 0,
            "retweets": t.get("retweet_count") or t.get("retweetCount") or 0,
            "ext_urls": ext_urls,
            "source_tier": "aggregator" if username in AGGREGATOR_HANDLES else "twitter",
        })

    return results


def _search_batch(accounts_batch: list, since_ts: int, session, max_pages: int = 10) -> list:
    """Search tweets from a batch of accounts using advanced search.

    Paginates via next_cursor: a single advanced_search page caps at ~20 tweets,
    so without pagination a high-frequency account (e.g. an aggregator posting
    dozens/hour) can fill the whole first page and starve low-frequency but
    important accounts (LeCun, World Labs) in the same batch. We follow the
    cursor until the API reports no more pages or we hit max_pages (cost guard).
    """
    query_parts = " OR ".join(f"from:{a}" for a in accounts_batch)
    query = f"{query_parts} since_time:{since_ts}"

    all_tweets = []
    cursor = ""
    for page in range(max_pages):
        page_tweets = None
        for attempt in range(3):
            try:
                resp = session.get(
                    f"{TWITTERAPI_BASE}/twitter/tweet/advanced_search",
                    headers={"X-API-Key": TWITTERAPI_KEY},
                    params={"query": query, "queryType": "Latest", "cursor": cursor},
                    timeout=30,
                )
                if resp.status_code == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                if resp.status_code != 200:
                    print(f"  [WARN] Search batch failed: {resp.status_code}")
                    return all_tweets
                data = resp.json()
                page_tweets = data.get("tweets", [])
                has_next = data.get("has_next_page", False)
                cursor = data.get("next_cursor", "") or ""
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                print(f"  [WARN] Search batch failed after 3 attempts: {e}")
                return all_tweets

        if page_tweets is None:
            break
        all_tweets.extend(page_tweets)
        if not has_next or not cursor:
            break
        time.sleep(1)  # be polite between pages

    if len(all_tweets) >= max_pages * 20:
        print(f"  [WARN] Batch hit max_pages={max_pages} cap; some tweets may be unfetched")
    return all_tweets


def fetch_all(accounts: list, freshness_hours: int = 2, per_account_cap: int = 5) -> list:
    """Fetch tweets from all accounts using batch search (much cheaper).

    per_account_cap: 每个账号每轮最多保留最新 N 条。advanced_search 翻页后
    会把高频聚合号（rohanpaul_ai 等一轮几十条）全抓回来；这个上限挡住灌水，
    既保证低频重要号（LeCun）能进来，又不让话痨号撑爆管线和 LLM 调用。
    返回已按时间倒序，所以截断保留的是每个账号最新的 N 条。
    """
    if not TWITTERAPI_KEY:
        print("[ERROR] TWITTERAPI_IO_KEY not set")
        return []

    session = requests.Session()
    session.trust_env = False

    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=freshness_hours)).timestamp())
    batch_size = 20  # ~20 accounts per search query to stay within query length limits

    all_tweets = []
    per_account_count = {}
    capped_total = 0
    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i + batch_size]
        print(f"  Searching batch {i // batch_size + 1} ({len(batch)} accounts)...")

        raw_tweets = _search_batch(batch, since_ts, session)

        for t in raw_tweets:
            author = t.get("author", {})
            username = author.get("userName", "")
            tweet_id = t.get("id", "")
            text = t.get("text", "")

            if not tweet_id or not text:
                continue
            if text.startswith("RT @"):
                continue
            if text.startswith("@") and len(text) < 80:
                continue

            # Per-account cap: keep only the latest N tweets per author
            key = username.lower()
            if per_account_count.get(key, 0) >= per_account_cap:
                capped_total += 1
                continue
            per_account_count[key] = per_account_count.get(key, 0) + 1

            # Extract external links
            ext_urls = []
            for u in t.get("entities", {}).get("urls", []):
                expanded = u.get("expanded_url", "")
                if expanded and "x.com/" not in expanded and "twitter.com/" not in expanded:
                    ext_urls.append(expanded)

            all_tweets.append({
                "username": username,
                "tweet_id": str(tweet_id),
                "text": text,
                "url": t.get("twitterUrl") or t.get("url") or f"https://x.com/{username}/status/{tweet_id}",
                "created_at": t.get("createdAt", ""),
                "likes": t.get("likeCount", 0),
                "retweets": t.get("retweetCount", 0),
                "ext_urls": ext_urls,
                "source_tier": "aggregator" if username in AGGREGATOR_HANDLES else "twitter",
            })

        print(f"  → {len(raw_tweets)} tweets found")
        time.sleep(2)

    if capped_total:
        print(f"  ({capped_total} 条超出 per_account_cap={per_account_cap} 被丢弃，多为高频聚合号)")
    print(f"\n  Total: {len(all_tweets)} new tweets")
    return all_tweets


# ============================================================
# RSS feeds
# ============================================================

RSS_FEEDS_PATH = os.environ.get(
    "RSS_FEEDS_PATH",
    str(Path(__file__).resolve().parent / "config" / "rss_feeds.yaml"),
)

# Media feeds (third-party news) live locally in the alert project.
MEDIA_FEEDS_PATH = os.environ.get(
    "MEDIA_FEEDS_PATH",
    str(Path(__file__).resolve().parent / "config" / "media_feeds.yaml"),
)


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace from RSS summary fields."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # drop tags
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)  # drop entities
    return re.sub(r"\s+", " ", text).strip()


# Browser-like UA — some sites (TechCrunch/Cloudflare, 36Kr) block default UAs.
_ARTICLE_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def fetch_article_text(url: str, max_chars: int = 2000, timeout: int = 10) -> str:
    """Fetch an article page and extract its body text (迭代 D: full-text enrichment).

    RSS feeds only give title + a short summary; key facts (金额/时间表/对标对象)
    live in the article body. This pulls the <p> paragraphs so the classifier sees
    the full event, not just a headline.

    Failure-safe: returns "" on any error (timeout, block, parse) — caller falls
    back to the RSS summary. Keep it polite (single request, short timeout) to limit
    crawl footprint on a shared egress IP.
    """
    if not url:
        return ""
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(url, headers={"User-Agent": _ARTICLE_UA}, timeout=timeout)
        if resp.status_code != 200:
            return ""
        html = resp.text
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, Exception):
        return ""

    # Extract <p> paragraphs, strip tags, keep substantive ones.
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)
    # Nav/chrome boilerplate markers — paragraphs dominated by these are page
    # furniture (menus, share bars, subscribe prompts), not article body.
    _NAV_MARKERS = ("Subscribe", "Sign In", "Sign in", "Sections", "Story text",
                    "Credit:", "Getty Images", "Newsletter", "Advertisement",
                    "Listen to", "Skip to", "Follow us", "分享", "登录", "订阅")
    chunks = []
    for p in paras:
        t = _strip_html(p)
        if len(t) < 40:
            continue  # skip short nav/boilerplate fragments
        # Skip paragraphs with very low punctuation density (menus/breadcrumbs:
        # many words, almost no sentence punctuation).
        words = t.split()
        punct = sum(t.count(c) for c in ".。,，!！?？")
        if len(words) >= 12 and punct / len(words) < 0.05:
            continue
        # Skip paragraphs carrying multiple nav markers.
        if sum(1 for m in _NAV_MARKERS if m in t) >= 2:
            continue
        chunks.append(t)
        if sum(len(c) for c in chunks) >= max_chars:
            break
    return " ".join(chunks)[:max_chars]


def fetch_rss(freshness_hours: int = 2) -> list:
    """Fetch recent entries from RSS feeds."""
    import feedparser

    try:
        with open(RSS_FEEDS_PATH) as f:
            feeds_config = yaml.safe_load(f)
    except Exception as e:
        print(f"  [WARN] RSS feeds config not found: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
    results = []

    for feed_meta in feeds_config.get("feeds", []):
        name = feed_meta.get("name", "")
        url = feed_meta.get("url", "")
        if not url:
            continue

        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                # Parse published time — prefer published over updated.
                # Many blogs (DeepMind, etc.) bump updated_parsed on minor edits,
                # making week-old posts look fresh. Use true publish date as ground truth.
                pub_raw = entry.get("published_parsed")
                upd_raw = entry.get("updated_parsed")
                if pub_raw:
                    pub_dt = datetime(*pub_raw[:6], tzinfo=timezone.utc)
                elif upd_raw:
                    pub_dt = datetime(*upd_raw[:6], tzinfo=timezone.utc)
                else:
                    continue
                if pub_dt < cutoff:
                    continue

                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = _strip_html(entry.get("summary", ""))[:200]

                if not title:
                    continue

                results.append({
                    "username": name,
                    "tweet_id": f"rss_{hashlib.md5(link.encode()).hexdigest()[:12]}",
                    "text": f"{title}. {summary}" if summary else title,
                    "url": link,
                    "created_at": pub_dt.strftime("%a %b %d %H:%M:%S %z %Y"),
                    "likes": 0,
                    "retweets": 0,
                    "ext_urls": [link] if link else [],
                    "source_tier": "official",
                })
        except Exception as e:
            print(f"  [WARN] RSS fetch failed for {name}: {e}")
            continue

    print(f"  RSS: {len(results)} new entries from {len(feeds_config.get('feeds', []))} feeds")
    return results


def fetch_media_rss(freshness_hours: int = 2) -> list:
    """Fetch recent entries from third-party media feeds (media_feeds.yaml).

    Media items are tagged source_tier="media" so the classifier downgrades
    them vs. official sources. Feeds carrying a `keywords` list (e.g. 36Kr,
    a mixed general-news feed) are filtered to AI-related entries only.
    """
    import feedparser

    try:
        with open(MEDIA_FEEDS_PATH) as f:
            feeds_config = yaml.safe_load(f)
    except Exception as e:
        print(f"  [WARN] Media feeds config not found: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
    results = []

    for feed_meta in feeds_config.get("feeds", []):
        name = feed_meta.get("name", "")
        url = feed_meta.get("url", "")
        keywords = feed_meta.get("keywords") or []
        trust = feed_meta.get("trust", "")  # "high" → bypass pending, push directly
        # High-frequency mixed feeds (IT之家/36氪) need a deeper scan window:
        # they publish 100+/day, so the most recent 15 are often all non-AI.
        # Per-feed override via `max_entries`; AI-vertical feeds keep the small default.
        max_entries = feed_meta.get("max_entries", 15)
        if not url:
            continue

        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_entries]:
                pub_raw = entry.get("published_parsed")
                upd_raw = entry.get("updated_parsed")
                if pub_raw:
                    pub_dt = datetime(*pub_raw[:6], tzinfo=timezone.utc)
                elif upd_raw:
                    pub_dt = datetime(*upd_raw[:6], tzinfo=timezone.utc)
                else:
                    continue
                if pub_dt < cutoff:
                    continue

                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = _strip_html(entry.get("summary", ""))[:200]
                if not title:
                    continue

                # Keyword filter for mixed general-news feeds (e.g. 36Kr).
                if keywords:
                    haystack = f"{title} {summary}"
                    if not any(kw.lower() in haystack.lower() for kw in keywords):
                        continue

                results.append({
                    "username": name,
                    "tweet_id": f"media_{hashlib.md5(link.encode()).hexdigest()[:12]}",
                    "text": f"{title}. {summary}" if summary else title,
                    "url": link,
                    "created_at": pub_dt.strftime("%a %b %d %H:%M:%S %z %Y"),
                    "likes": 0,
                    "retweets": 0,
                    "ext_urls": [link] if link else [],
                    "source_tier": "media",
                    "trust": trust,
                })
        except Exception as e:
            print(f"  [WARN] Media RSS fetch failed for {name}: {e}")
            continue

    print(f"  Media: {len(results)} new entries from {len(feeds_config.get('feeds', []))} feeds")
    return results
