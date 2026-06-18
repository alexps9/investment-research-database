"""Feishu enterprise self-built bot publisher: 1-on-1 interactive card push.

Used by HRes' aha moment bot (app: cli_aa84636e237d5bd1) for daily digest
push to team members via personal Feishu DM.

Auth flow:
    POST /open-apis/auth/v3/tenant_access_token/internal
        body = {app_id, app_secret}
        -> {code:0, tenant_access_token, expire}
    POST /open-apis/im/v1/messages?receive_id_type=open_id
        headers: Authorization: Bearer <token>
        body = {receive_id, msg_type:"interactive", content:"<JSON string>"}
        -> {code:0, data:{message_id, ...}}

Env vars (required):
    FEISHU_BOT_APP_ID
    FEISHU_BOT_APP_SECRET

Scope required on the app (configured by leader/IT):
    im:message:send_as_bot   ← 唯一最少权限

Note on receive_id_type:
    - "open_id": app-scoped (this bot's own open_id space). 推荐.
    - "user_id": tenant-wide employee ID, cross-app stable. Requires the
      open_id under THIS app to be unknown but employee user_id is known.
    - "email": works without contact scope as long as recipient has email
      registered with the enterprise Feishu account. Convenient for bootstrap.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FEISHU_BASE_URL_DEFAULT = "https://open.feishu.cn/open-apis"
TOKEN_TTL_DEFAULT = 7200
TOKEN_SAFETY_MARGIN = 60

VALID_RECEIVE_ID_TYPES = {"open_id", "user_id", "union_id", "email", "chat_id"}


def infer_receive_id_type(receive_id: str) -> str:
    """Guess receive_id_type from the value shape.

    Used so the .env recipient list can mix emails and open_ids freely:
        FEISHU_BOT_RECIPIENT_OPENIDS=alice@hill.com,ou_xxx,bob@hill.com
    The publisher dispatches each recipient with the correct type.
    """
    rid = receive_id.strip()
    if "@" in rid:
        return "email"
    if rid.startswith("ou_"):
        return "open_id"
    if rid.startswith("on_"):
        return "union_id"
    if rid.startswith("oc_"):
        return "chat_id"
    # Numeric / opaque employee ID → user_id
    return "user_id"


class FeishuBotAPIError(RuntimeError):
    """Feishu OpenAPI returned code != 0 or unexpected shape."""


class FeishuBotPublisher:
    """Stateful publisher with in-memory tenant_access_token cache.

    Each Feishu app has its own open_id namespace; the open_id used here
    must be acquired against THIS app (cli_aa84636e237d5bd1), not against
    any other app the user may have authorized previously.
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("FEISHU_BOT_BASE_URL") or FEISHU_BASE_URL_DEFAULT
        ).rstrip("/")
        self.app_id = app_id or os.environ.get("FEISHU_BOT_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("FEISHU_BOT_APP_SECRET", "")

        self._token: str | None = None
        self._token_exp: float = 0.0

    def _require_credentials(self) -> None:
        missing = [
            n
            for n, v in [
                ("FEISHU_BOT_APP_ID", self.app_id),
                ("FEISHU_BOT_APP_SECRET", self.app_secret),
            ]
            if not v
        ]
        if missing:
            raise FeishuBotAPIError(f"missing Feishu bot credentials: {', '.join(missing)}")

    def get_tenant_access_token(self, force: bool = False) -> str:
        """Fetch tenant_access_token (app-level), cached for ~TTL."""
        if not force and self._token and time.time() < self._token_exp - TOKEN_SAFETY_MARGIN:
            return self._token

        self._require_credentials()
        endpoint = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        r = httpx.post(
            endpoint,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=20.0,
            trust_env=False,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise FeishuBotAPIError(f"get_tenant_access_token failed: {data}")

        token = data.get("tenant_access_token")
        if not token:
            raise FeishuBotAPIError(f"token response missing tenant_access_token: {data}")

        ttl_raw = data.get("expire", TOKEN_TTL_DEFAULT)
        try:
            ttl = int(ttl_raw)
        except (TypeError, ValueError):
            ttl = TOKEN_TTL_DEFAULT

        self._token = token
        self._token_exp = time.time() + ttl
        logger.info("Feishu bot tenant_access_token acquired, ttl=%ss", ttl)
        return self._token

    def send_interactive_card(
        self,
        receive_id: str,
        card: dict[str, Any],
        receive_id_type: str = "open_id",
    ) -> dict[str, Any]:
        """Send a single interactive card to one recipient.

        Feishu API requires content to be a JSON string (not object).
        """
        if receive_id_type not in VALID_RECEIVE_ID_TYPES:
            raise ValueError(
                f"invalid receive_id_type {receive_id_type!r}; "
                f"must be one of {sorted(VALID_RECEIVE_ID_TYPES)}"
            )
        if not receive_id:
            raise ValueError("receive_id must be non-empty")

        token = self.get_tenant_access_token()
        endpoint = f"{self.base_url}/im/v1/messages"
        payload = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        }
        r = httpx.post(
            endpoint,
            params={"receive_id_type": receive_id_type},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
            timeout=30.0,
            trust_env=False,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise FeishuBotAPIError(
                f"send_interactive_card failed (receive_id={receive_id}, "
                f"type={receive_id_type}): {data}"
            )

        msg_id = (data.get("data") or {}).get("message_id", "")
        logger.info(
            "Feishu bot send ok: receive_id=%s type=%s message_id=%s",
            receive_id,
            receive_id_type,
            msg_id,
        )
        return data

    def send_card_to_recipients(
        self,
        receive_ids: list[str],
        card: dict[str, Any],
        receive_id_type: str | None = None,
    ) -> dict[str, Any]:
        """Fan out a card to multiple recipients sequentially.

        If ``receive_id_type`` is None (default), each recipient's type is
        auto-inferred per value (so .env can mix emails and open_ids).
        Pass an explicit type to force all recipients to that type.

        Returns a summary dict:
            {"sent": [...], "failed": [{"receive_id":..., "error":...}, ...]}

        Failures on individual recipients do not abort the batch (per-spec
        these are usually "user blocked the bot" or "user not in scope" —
        non-fatal).
        """
        if not receive_ids:
            raise ValueError("receive_ids must be non-empty")

        sent: list[str] = []
        failed: list[dict[str, str]] = []

        for rid in receive_ids:
            rid_type = receive_id_type or infer_receive_id_type(rid)
            try:
                self.send_interactive_card(rid, card, receive_id_type=rid_type)
                sent.append(rid)
            except (FeishuBotAPIError, httpx.HTTPError) as e:
                logger.warning("Feishu bot send to %s (%s) failed: %s", rid, rid_type, e)
                failed.append({"receive_id": rid, "type": rid_type, "error": str(e)})

        if failed:
            logger.warning(
                "Feishu bot batch done: %d sent, %d failed", len(sent), len(failed)
            )
        else:
            logger.info("Feishu bot batch done: %d/%d sent", len(sent), len(receive_ids))

        return {"sent": sent, "failed": failed}
