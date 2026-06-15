"""Send alert messages to Feishu group via webhook."""

import json
import os

import requests

FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")


def format_alert(tweet: dict, classification: dict) -> str:
    """Format the alert message — keep it minimal."""
    summary = classification.get("summary", "")
    url = tweet.get("url", "")
    alert_level = classification.get("alert_level", "medium")
    ext_urls = tweet.get("ext_urls", [])

    icon = "⚠️" if alert_level == "important" else "🔔"
    # Source-tier tag before the summary, so credibility is visible at a glance:
    #   🔁 转述 — aggregator/relay account (second-hand, unverified — check the source)
    #   📰     — third-party media report (second-hand but editorially filtered)
    #   (none) — P0 account / official first-hand source
    tier = tweet.get("source_tier")
    if tier == "aggregator":
        tag = " 🔁 转述"
    elif tier == "media":
        tag = " 📰"
    else:
        tag = ""
    msg = f"{icon}{tag} {summary}"

    # Multi-source verification: show which independent sources corroborate this.
    if tweet.get("verified"):
        sources = tweet.get("cluster_sources") or []
        if sources:
            shown = "、".join(sources[:4])
            more = f" 等{len(sources)}个来源" if len(sources) > 4 else ""
            msg += f"\n✅ 多源证实（{shown}{more}）"

    msg += f"\n\n🔗 {url}"
    # Show external link only if it differs from the primary url
    # (RSS/media items reuse the same link for both, which would duplicate it).
    if ext_urls and ext_urls[0] and ext_urls[0] != url:
        msg += "\n📎 " + ext_urls[0]

    # Primary source from cross-verification
    primary = classification.get("primary_source")
    if primary and primary.get("url"):
        msg += f"\n📄 原始来源: {primary['url']}"

    return msg


def send_feishu(message: str) -> bool:
    """Send a text message to group via webhook."""
    if not FEISHU_WEBHOOK_URL:
        print("[DRY RUN] FEISHU_WEBHOOK_URL not set. Would send:")
        print(message)
        print()
        return False

    resp = requests.post(
        FEISHU_WEBHOOK_URL,
        headers={"Content-Type": "application/json; charset=utf-8"},
        json={"msg_type": "text", "content": {"text": message}},
        timeout=10,
    )
    data = resp.json()
    if data.get("code") == 0 or data.get("StatusCode") == 0:
        return True
    else:
        print(f"[ERROR] Webhook send failed: {data}")
        return False
