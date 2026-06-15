"""Sync alert signals to the shared knowledge base (Alex's backend).

Calls POST /api/signals on the shared backend. If the backend is unreachable
or returns an error, logs the failure and returns None — never blocks the
main alert pipeline.

Env:
    KB_API_BASE_URL  (default: https://Alexps9yyy-hh-research-api.hf.space)
"""

import os
import time
import requests

KB_API_BASE_URL = os.environ.get(
    "KB_API_BASE_URL",
    "https://Alexps9yyy-hh-research-api.hf.space"
).rstrip("/")

KB_API_TIMEOUT = int(os.environ.get("KB_API_TIMEOUT", "15"))

_EVENT_TYPE_MAP = {
    "模型/产品发布": "model_release",
    "技术研究突破": "paper",
    "硬件/Infra突破": "news",
    "大佬评论/观点": "tweet",
    "评测/榜单": "benchmark",
    "Demo/演示": "other",
    "公司间商业动作": "news",
    "顶级人员变动": "news",
}

_session = requests.Session()
_session.trust_env = False


def sync_signal(tweet: dict, result: dict) -> dict | None:
    """Write a classified signal to the shared KB.

    Args:
        tweet: raw signal dict from fetcher
        result: classifier output (summary, event_type, alert_level, confidence, reason)

    Returns:
        API response dict on success, None on failure.
    """
    summary = result.get("summary", "")
    if not summary:
        return None

    url = tweet.get("url", "")
    if not url:
        ext_urls = tweet.get("ext_urls", [])
        url = ext_urls[0] if ext_urls else ""
    if not url:
        return None

    signal_type = _EVENT_TYPE_MAP.get(result.get("event_type", ""), "other")

    published_at = tweet.get("published_at", "")
    if not published_at:
        published_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    alert_level = result.get("alert_level", "medium")
    status = "processed" if alert_level == "important" else "collected"

    importance = result.get("alert_level", "medium")
    confidence = result.get("confidence", "reported")
    reason = result.get("reason", "")

    body = {
        "title": summary,
        "url": url,
        "signal_type": signal_type,
        "abstract": tweet.get("text", "")[:1000],
        "published_at": published_at,
        "status": status,
        # 判别器字段 — Alex 的 API 目前不接受，会被忽略或 422；
        # 等他加 signal_analysis 写入接口后这些就能落库。
        "importance": importance,
        "confidence": confidence,
        "reason": reason,
    }

    try:
        resp = _session.post(
            f"{KB_API_BASE_URL}/api/signals",
            json=body,
            timeout=KB_API_TIMEOUT,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            print(f"    → KB sync OK: {data.get('id', '?')}")
            return data
        else:
            print(f"    → KB sync failed ({resp.status_code}): {resp.text[:100]}")
            return None
    except Exception as e:
        print(f"    → KB sync error: {type(e).__name__}: {e}")
        return None
