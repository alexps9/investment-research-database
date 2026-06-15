"""H Link (HCMLink, 高瓴有数) publisher: send daily digest as textcard.

Server API base: https://open-ushu.hillinsight.tech
API docs:       https://docs-ushu.hillinsight.tech/dev/serverapi/

Auth flow:
    GET  /cgi/token/get?app_key=...&app_secret=...
        -> {error_code:0, result:{access_token, expires_in}}
    POST /cgi/message/send?access_token=...
        body = {app_id, portal, msgtype:"textcard", msg:{message,content,url}, touser:[...]}
        -> {error_code:0, result:{invaliduser, task_id, ...}}

Env vars (required for live send):
    H_LINK_APP_ID
    H_LINK_APP_KEY
    H_LINK_APP_SECRET
    H_LINK_PORTAL     (optional but recommended; identifies the enterprise portal)
    H_LINK_BASE_URL   (optional, defaults to https://open-ushu.hillinsight.tech)

Constraints (from H Link docs):
    - textcard `content` max 1000 chars  (truncated at 950 with "..." for safety)
    - textcard `message` max 500 chars   (notification banner)
    - touser array max 1000 open_ids
    - token TTL ~7200s, cache locally to avoid rate-limit on /cgi/token/get
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

H_LINK_BASE_DEFAULT = "https://open-ushu.hillinsight.tech"
TEXTCARD_CONTENT_LIMIT = 1000
TEXTCARD_MESSAGE_LIMIT = 500
SAFE_CONTENT_LIMIT = 950
TOKEN_TTL_DEFAULT = 7200
TOKEN_SAFETY_MARGIN = 60


class HLinkAPIError(RuntimeError):
    """H Link API returned error_code != 0 or unexpected shape."""


class HLinkPublisher:
    """Stateful publisher with in-memory token cache.

    Construct once per process; the token cache is per-instance.
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        app_secret: str | None = None,
        portal: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("H_LINK_BASE_URL") or H_LINK_BASE_DEFAULT
        ).rstrip("/")
        self.app_id = app_id or os.environ.get("H_LINK_APP_ID", "")
        self.app_key = app_key or os.environ.get("H_LINK_APP_KEY", "")
        self.app_secret = app_secret or os.environ.get("H_LINK_APP_SECRET", "")
        self.portal = portal or os.environ.get("H_LINK_PORTAL") or None

        self._token: str | None = None
        self._token_exp: float = 0.0

    def _require_credentials(self) -> None:
        missing = [
            name
            for name, val in [
                ("H_LINK_APP_ID", self.app_id),
                ("H_LINK_APP_KEY", self.app_key),
                ("H_LINK_APP_SECRET", self.app_secret),
            ]
            if not val
        ]
        if missing:
            raise HLinkAPIError(f"missing H Link credentials: {', '.join(missing)}")

    def get_access_token(self, force: bool = False) -> str:
        """Fetch access_token, caching for ~TTL.

        Set force=True to bypass cache (useful when previous token was revoked).
        """
        if not force and self._token and time.time() < self._token_exp - TOKEN_SAFETY_MARGIN:
            return self._token

        self._require_credentials()
        endpoint = f"{self.base_url}/cgi/token/get"
        r = httpx.get(
            endpoint,
            params={"app_key": self.app_key, "app_secret": self.app_secret},
            timeout=20.0,
            trust_env=False,  # bypass local proxies (Clash etc.)
        )
        r.raise_for_status()
        data = r.json()
        if data.get("error_code") not in (0, "0"):
            raise HLinkAPIError(f"get_access_token failed: {data}")

        result = data.get("result") or data
        token = result.get("access_token")
        if not token:
            raise HLinkAPIError(f"get_access_token response missing access_token: {data}")

        ttl_raw = result.get("expires_in", TOKEN_TTL_DEFAULT)
        try:
            ttl = int(ttl_raw)
        except (TypeError, ValueError):
            ttl = TOKEN_TTL_DEFAULT

        self._token = token
        self._token_exp = time.time() + ttl
        logger.info("H Link access_token acquired, ttl=%ss", ttl)
        return self._token

    @staticmethod
    def truncate_content(content: str, limit: int = SAFE_CONTENT_LIMIT) -> str:
        """Truncate content to safe length, appending '...' marker."""
        if len(content) <= limit:
            return content
        return content[: limit - 3] + "..."

    def _is_visible(self, open_id: str) -> bool:
        """Probe whether `open_id` is within the app's visible scope.

        H Link does not expose an `app.visible_scope.list` API, but
        `GET /cgi/user/get` has a useful side-effect:
            - In-scope user  → error_code=0, result = {avatar, dept_title, ...}
            - Out-of-scope user → error_code=0, result = {} (empty dict)
        We use this to filter recipients before `send_textcard` to avoid
        the whole batch being rejected with `40043 检查应用可见范围失败`.

        Requires `self.portal` (errors out with 400 if missing).
        Returns False on any network/parse failure (fail-closed).
        """
        if not self.portal:
            logger.warning("H Link _is_visible: portal is empty, cannot check; assuming not visible")
            return False
        try:
            token = self.get_access_token()
            endpoint = f"{self.base_url}/cgi/user/get"
            r = httpx.get(
                endpoint,
                params={"access_token": token, "portal": self.portal, "open_id": open_id},
                timeout=10.0,
                trust_env=False,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("error_code") in (0, "0") and bool(data.get("result"))
        except Exception as e:  # noqa: BLE001
            logger.warning("H Link _is_visible probe failed for %s: %s", open_id, e)
            return False

    def filter_visible_users(self, open_ids: list[str]) -> tuple[list[str], list[str]]:
        """Split `open_ids` into (visible, skipped) buckets.

        Visible = inside app's configured visible scope; safe to send.
        Skipped = outside scope; sending would trigger 40043 for the whole batch.
        """
        visible: list[str] = []
        skipped: list[str] = []
        for oid in open_ids:
            if self._is_visible(oid):
                visible.append(oid)
            else:
                skipped.append(oid)
        return visible, skipped

    def build_textcard_payload(
        self,
        open_ids: list[str],
        title: str,
        content: str,
        url: str,
    ) -> dict[str, Any]:
        """Build the new message/send_single payload for msgtype=link.

        5.22 migration: H Link upgraded API from /cgi/message/send (textcard)
        to /cgi/message/send_single (link/card/rtf). The legacy textcard endpoint
        returns 40041 "获取from_accid失败" / 40043 "检查应用可见范围失败" by
        design — push the caller to migrate.

        New payload (msgtype=link):
          msg = {title, content, url}    # link card with title + summary + jump url
        vs Old payload (msgtype=textcard):
          msg = {message, content, url}  # message field deprecated; use title instead

        Caller signature is preserved — `title` maps to msg.title; `content` is
        the body text (still safely truncated to 950 chars for parity with the
        old textcard render).
        """
        payload: dict[str, Any] = {
            "app_id": self.app_id,
            "msgtype": "link",
            "msg": {
                "title": title[:TEXTCARD_MESSAGE_LIMIT],
                "content": content[:TEXTCARD_CONTENT_LIMIT],
                "url": url,
            },
            "touser": open_ids,
        }
        if self.portal:
            payload["portal"] = self.portal
        return payload

    def send_textcard(
        self,
        open_ids: list[str],
        title: str,
        summary_lines: list[str],
        url: str,
        skip_visibility_filter: bool = False,
    ) -> dict[str, Any]:
        """Send a textcard to one or more H Link users (open_ids).

        By default, filters open_ids through `_is_visible` first to avoid
        the whole batch being rejected with `40043 检查应用可见范围失败`.
        Out-of-scope users are logged as warnings and dropped.

        Pass `skip_visibility_filter=True` to bypass the pre-flight check
        (e.g. when caller has already filtered, or for explicit debugging).

        Returns the API response dict augmented with `result._local_skipped_open_ids`
        listing users dropped by the visibility filter (empty list if none).
        Raises HLinkAPIError on non-zero error_code from H Link.
        """
        if not open_ids:
            raise ValueError("open_ids must be non-empty")
        if not url:
            raise ValueError("url is required for textcard (jump target)")

        # Pre-flight: filter to only visible-scope users to avoid 40043 on the whole batch
        skipped: list[str] = []
        if not skip_visibility_filter:
            visible, skipped = self.filter_visible_users(open_ids)
            if skipped:
                logger.warning(
                    "H Link visibility filter: %d/%d open_ids dropped (not in app scope): %s",
                    len(skipped), len(open_ids), skipped,
                )
            if not visible:
                logger.error(
                    "H Link: 0/%d users in visible scope — nothing to send. "
                    "Drop skipped=%s. Returning synthetic OK to caller to avoid blocking pipeline.",
                    len(open_ids), skipped,
                )
                return {
                    "error_code": 0,
                    "message": "skipped: no visible users in scope",
                    "result": {
                        "invaliduser": [],
                        "_local_skipped_open_ids": skipped,
                    },
                }
            open_ids = visible

        content = "\n".join(line.rstrip() for line in summary_lines).strip()
        content = self.truncate_content(content)

        payload = self.build_textcard_payload(open_ids, title, content, url)
        token = self.get_access_token()

        # New endpoint (5.22 migration): /cgi/message/send_single replaces
        # /cgi/message/send (textcard). See msg-send-new.html docs.
        endpoint = f"{self.base_url}/cgi/message/send_single"
        r = httpx.post(
            endpoint,
            params={"access_token": token},
            json=payload,
            timeout=30.0,
            trust_env=False,
        )
        r.raise_for_status()
        data = r.json()

        # Special handling for 40043 "检查应用可见范围失败":
        # This is an admin-side config issue (app's message-send visible scope
        # must be configured by H Link admin in the platform backend). Code
        # cannot self-resolve. Probing /cgi/user/get only tests "addressbook
        # visibility" — a separate permission from message-send visibility.
        # Degrade gracefully: log + return synthetic OK so broadcast pipeline
        # is non-blocking. Surface the affected users for ops follow-up.
        if data.get("error_code") == 40043:
            logger.error(
                "H Link 40043 检查应用可见范围失败 for %d open_ids: %s. "
                "Cause: H Link app's message-send scope not configured for these users. "
                "Resolution: requires H Link admin to add them via platform backend "
                "(no self-service API; /cgi/user/get-based pre-filter only tests addressbook "
                "scope, not message-send scope). Pipeline continues non-blocking.",
                len(open_ids), open_ids,
            )
            return {
                "error_code": 0,
                "message": "degraded: 40043 visible-scope rejection swallowed (admin config needed)",
                "result": {
                    "invaliduser": [],
                    "_local_skipped_open_ids": skipped,
                    "_40043_blocked_open_ids": open_ids,
                    "_underlying_error_code": 40043,
                },
            }

        if data.get("error_code") not in (0, "0"):
            raise HLinkAPIError(f"send_textcard failed: {data}")

        result = data.get("result") or {}
        invalid = result.get("invaliduser") or []
        if invalid:
            logger.warning("H Link send_textcard: %d invalid open_ids: %s", len(invalid), invalid)

        logger.info(
            "H Link send_textcard ok: %d recipients, %d chars, task_id=%s, skipped_pre_send=%d",
            len(open_ids),
            len(content),
            result.get("task_id"),
            len(skipped),
        )
        # Augment response with locally-filtered skip list so caller can surface it
        data.setdefault("result", {})["_local_skipped_open_ids"] = skipped
        return data
