"""RSS collector for company / lab official blogs.

Subscribes to a curated list of feeds (config/rss_feeds.yaml) and yields any
entries published within [since, until]. Each feed becomes its own "author"
(the team/lab name) so the digest can group by team.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import feedparser
import httpx
import yaml
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..storage.schemas import Signal, WhitelistEntry
from ..utils.logger import get_logger
from .base import CollectorBase

log = get_logger("rss_collector")

UA = {"User-Agent": "Mozilla/5.0 (HH Research Pipeline)"}

DEFAULT_FEEDS_PATH = Path(__file__).parent.parent.parent.parent / "config" / "rss_feeds.yaml"


class RssCollector(CollectorBase):
    source_name = "rss"

    def __init__(
        self,
        feeds_path: Path | None = None,
        request_timeout: float = 15.0,
    ) -> None:
        self.feeds = self._load_feeds(feeds_path or DEFAULT_FEEDS_PATH)
        self._client = httpx.Client(headers=UA, timeout=request_timeout, follow_redirects=True)

    def collect(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        """Iterate all configured feeds; yield Signal for entries in [since, until]."""
        fetched_at = datetime.now(timezone.utc)
        record_ids_by_name = {entry.name.casefold(): entry.record_id for entry in whitelist}
        for feed_meta in self.feeds:
            try:
                whitelist_name = feed_meta.get("whitelist_name") or feed_meta.get("name", "")
                author_record_id = record_ids_by_name.get(str(whitelist_name).casefold())
                yield from self._fetch_feed(feed_meta, since, until, fetched_at, author_record_id)
            except Exception as e:  # noqa: BLE001
                log.warning("rss feed failed for %s: %s", feed_meta.get("name"), e)
                continue

    def close(self) -> None:
        self._client.close()

    # -------- internals --------

    def _load_feeds(self, path: Path) -> list[dict]:
        if not path.exists():
            log.warning("rss config not found: %s", path)
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data.get("feeds", []) or []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.ConnectError, httpx.ReadError)),
        reraise=True,
    )
    def _fetch_feed_inner(self, url: str) -> httpx.Response:
        return self._client.get(url)

    def _fetch_feed(
        self,
        feed_meta: dict,
        since: datetime,
        until: datetime,
        fetched_at: datetime,
        author_record_id: str | None = None,
    ) -> Iterable[Signal]:
        name = feed_meta.get("name", "?")
        url = feed_meta.get("url", "")
        category = feed_meta.get("category", "other")
        if not url:
            return

        log.info("rss: fetching %s (%s)", name, url)
        try:
            resp = self._fetch_feed_inner(url)
        except (httpx.HTTPError, OSError) as e:
            log.warning("rss: %s — %s after retries, skipping", name, e)
            return
        if resp.status_code != 200:
            log.warning("rss: %s returned HTTP %d, skipping", name, resp.status_code)
            return

        parsed = feedparser.parse(resp.content)
        if not parsed.entries:
            log.info("rss: %s — feed empty", name)
            return

        in_window = 0
        for entry in parsed.entries:
            pub_dt = _entry_datetime(entry)
            if pub_dt is None:
                continue
            if not (since <= pub_dt < until):
                continue
            in_window += 1
            yield self._entry_to_signal(entry, name, category, pub_dt, fetched_at, author_record_id)

        log.info("rss: %s — %d entries in window", name, in_window)

    def _entry_to_signal(
        self,
        entry: Any,
        feed_name: str,
        category: str,
        pub_dt: datetime,
        fetched_at: datetime,
        author_record_id: str | None = None,
    ) -> Signal:
        title = entry.get("title", "(no title)")
        url = entry.get("link", "")
        # Prefer summary/content; fall back to description
        body = (
            entry.get("summary")
            or (entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")
            or entry.get("description", "")
            or ""
        )

        # Extract images from HTML content + media_thumbnail/media_content
        from ..extract.image_extractor import extract_rss_post_images

        image_urls: list[str] = []
        # 1. <img> tags inside body
        image_urls.extend(extract_rss_post_images(body, max_images=2))
        # 2. media_thumbnail (RSS standard)
        for thumb in (entry.get("media_thumbnail") or []):
            if isinstance(thumb, dict) and thumb.get("url"):
                image_urls.append(thumb["url"])
        # 3. media_content (RSS standard)
        for media in (entry.get("media_content") or []):
            if isinstance(media, dict) and media.get("url"):
                medium = media.get("medium", "")
                if medium == "image" or media["url"].lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp")
                ):
                    image_urls.append(media["url"])
        # Dedupe preserving order
        seen, uniq_imgs = set(), []
        for u in image_urls:
            if u not in seen:
                seen.add(u)
                uniq_imgs.append(u)
        image_urls = uniq_imgs[:2]  # cap at 2

        # Strip HTML tags from body for raw_text
        import re
        body_text = re.sub(r"<[^>]+>", " ", body)
        body_text = re.sub(r"\s+", " ", body_text).strip()
        raw_text = f"{title}\n\n{body_text}"[:8000]

        # Stable source_id: hash of (feed_name + url)
        sid_input = f"{feed_name}|{url}"
        sid = "rss:" + hashlib.sha1(sid_input.encode("utf-8")).hexdigest()[:16]

        return Signal(
            source="rss",
            source_id=sid,
            author_name=feed_name,
            author_record_id=author_record_id,
            url=url,
            raw_text=raw_text,
            lang="en",
            created_at=pub_dt,
            fetched_at=fetched_at,
            needs_human_review=False,
            image_urls=image_urls,
        )


def _entry_datetime(entry: Any) -> datetime | None:
    """Extract entry publication time as tz-aware datetime in UTC."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = entry.get(key)
        if t:
            try:
                # struct_time → datetime UTC
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
    return None
