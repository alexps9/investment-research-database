"""X (Twitter) collector via socialdata.tools.

Strategy:
1. For each whitelist entry with a non-empty x_handle:
   a. Resolve handle → numeric user_id (cached per run)
   b. Fetch their recent tweets (paginated)
   c. Filter by time window, exclude retweets (configurable)
2. Yield Signal objects.

Cost model: socialdata.tools charges $0.0002 per item fetched (user profile or tweet).
For 226 active handles × ~3 tweets/day × 30 days = ~$5/month worst case.

Rate limit: 3 req/min free, $0.0002/req above that. We don't worry about hitting
the free limit — we'd rather pay $0.0002 each than slow down.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Iterable

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..storage.schemas import Signal, WhitelistEntry
from ..utils.logger import get_logger
from .base import CollectorBase

log = get_logger("x_collector")


class SocialDataXCollector(CollectorBase):
    source_name = "x"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        exclude_retweets: bool = True,
        exclude_replies: bool = False,
        max_pages_per_user: int = 3,
        request_timeout: float = 30.0,
        per_user_timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("SOCIALDATA_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "SOCIALDATA_API_KEY not set. Add it to .env or export it before running."
            )
        self.base_url = base_url or os.getenv("SOCIALDATA_BASE_URL", "https://api.socialdata.tools")
        self.exclude_retweets = exclude_retweets
        self.exclude_replies = exclude_replies
        self.max_pages_per_user = max_pages_per_user
        self.per_user_timeout = per_user_timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            # tighter explicit timeouts: connect/read/write/pool — prevents
            # hangs when socialdata is slow on a particular user lookup
            timeout=httpx.Timeout(connect=10.0, read=request_timeout, write=10.0, pool=10.0),
        )
        self._user_id_cache: dict[str, str] = {}  # handle (lowercased) → user_id_str

    # -------- public API --------

    def collect(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        fetched_at = datetime.now(timezone.utc)
        seen_ids: set[str] = set()
        import time as _t

        for entry in whitelist:
            handle = entry.twitter_handle
            if not handle:
                continue
            user_start = _t.monotonic()
            try:
                user_id = self._resolve_user_id(handle)
            except (UserNotFoundError, ProtectedAccountError) as e:
                log.warning("skipping %s (@%s): %s", entry.name, handle, e)
                continue
            except httpx.HTTPError as e:
                log.warning("user lookup failed for %s: %s", handle, e)
                continue

            try:
                for tweet in self._fetch_tweets(user_id, since, until):
                    # Per-user wall-clock timeout — bail if this user takes too long
                    if _t.monotonic() - user_start > self.per_user_timeout:
                        log.warning(
                            "abandoning @%s after %.0fs (per-user timeout)",
                            handle, self.per_user_timeout,
                        )
                        break
                    sid = f"x:{tweet['id_str']}"
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    yield self._tweet_to_signal(tweet, entry, fetched_at)
            except httpx.HTTPError as e:
                log.warning("tweet fetch failed for %s (@%s): %s", entry.name, handle, e)
                continue

    def close(self) -> None:
        self._client.close()

    # -------- internals --------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def _resolve_user_id(self, handle: str) -> str:
        """Resolve @handle → numeric user_id. Cached per collector instance."""
        key = handle.lstrip("@").lower()
        if key in self._user_id_cache:
            return self._user_id_cache[key]

        resp = self._client.get(f"/twitter/user/{key}")
        if resp.status_code == 404:
            raise UserNotFoundError(f"user @{key} not found")
        if resp.status_code == 403:
            raise ProtectedAccountError(f"user @{key} is protected or suspended")
        resp.raise_for_status()

        data = resp.json()
        user_id = data.get("id_str") or str(data.get("id", ""))
        if not user_id:
            raise UserNotFoundError(f"no id returned for @{key}: {data}")

        self._user_id_cache[key] = user_id
        return user_id

    def _fetch_tweets(
        self,
        user_id: str,
        since: datetime,
        until: datetime,
    ) -> Iterable[dict[str, Any]]:
        """Fetch a user's recent tweets, paginating until we cross `since`."""
        cursor: str | None = None
        for page_num in range(self.max_pages_per_user):
            url = f"/twitter/user/{user_id}/tweets"
            params: dict[str, str] = {}
            if cursor:
                params["cursor"] = cursor

            resp = self._fetch_page(url, params)
            tweets = resp.get("tweets", [])
            if not tweets:
                return

            stop_paginating = False
            for t in tweets:
                created_at = _parse_x_datetime(t.get("tweet_created_at"))
                if created_at is None:
                    continue
                if created_at < since:
                    # All subsequent tweets will also be < since; stop after this page
                    stop_paginating = True
                    continue
                if created_at >= until:
                    continue
                if self.exclude_retweets and t.get("retweeted_status") is not None:
                    continue
                if self.exclude_replies and t.get("in_reply_to_user_id_str"):
                    continue
                yield t

            if stop_paginating:
                return
            cursor = resp.get("next_cursor")
            if not cursor:
                return

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def _fetch_page(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        resp = self._client.get(url, params=params)
        if resp.status_code == 429:
            log.warning("rate limited on %s, backing off", url)
        resp.raise_for_status()
        return resp.json()

    def _tweet_to_signal(
        self,
        tweet: dict[str, Any],
        entry: WhitelistEntry,
        fetched_at: datetime,
    ) -> Signal:
        tid = tweet["id_str"]
        # Use full_text if available, else text. socialdata.tools usually returns full_text.
        raw_text = tweet.get("full_text") or tweet.get("text") or ""
        # Build canonical X URL
        screen_name = (tweet.get("user") or {}).get("screen_name", "")
        url = f"https://x.com/{screen_name}/status/{tid}" if screen_name else f"https://x.com/i/status/{tid}"
        created_at = _parse_x_datetime(tweet.get("tweet_created_at")) or fetched_at
        lang_raw = tweet.get("lang", "en")
        lang = "zh" if lang_raw and lang_raw.startswith("zh") else "en" if lang_raw == "en" else "other"

        return Signal(
            source="x",
            source_id=f"x:{tid}",
            author_name=entry.name,
            author_record_id=entry.record_id,
            url=url,
            raw_text=raw_text[:8000],  # truncate giant threads
            lang=lang,
            created_at=created_at,
            fetched_at=fetched_at,
            needs_human_review=False,
        )


# ---- helpers ----

class UserNotFoundError(Exception):
    pass


class ProtectedAccountError(Exception):
    pass


def _parse_x_datetime(s: str | None) -> datetime | None:
    """Parse socialdata.tools' ISO 8601 timestamps like '2026-03-26T15:50:37.000000Z'."""
    if not s:
        return None
    try:
        # strip trailing 'Z' → +00:00 for fromisoformat
        normalized = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None
