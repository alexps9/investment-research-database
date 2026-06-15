"""Outbound notification tools (Feishu / Lark).

Atomic, side-effecting tools that push a formatted message to a chat group via an
incoming webhook. Like every tool here they never raise — a structured
``{"error": ...}`` / ``{"ok": ...}`` dict is returned instead.

Env:
    FEISHU_WEBHOOK_URL   incoming webhook URL (if unset, runs in dry-run mode)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

WEBHOOK_ENV = "FEISHU_WEBHOOK_URL"
TIMEOUT = float(os.getenv("NOTIFY_TIMEOUT", "10"))


async def send_feishu(message: str, webhook_url: str | None = None) -> dict[str, Any]:
    """Send a plain-text message to a Feishu/Lark group via incoming webhook.

    Args:
        message: the text to send.
        webhook_url: override the ``FEISHU_WEBHOOK_URL`` env var.

    Returns:
        ``{"ok": True}`` on success, ``{"ok": False, "dry_run": True, ...}`` when
        no webhook is configured, or ``{"error": ...}`` on failure.
    """
    url = webhook_url or os.getenv(WEBHOOK_ENV, "")
    if not url:
        return {"ok": False, "dry_run": True, "message": message,
                "detail": f"{WEBHOOK_ENV} not set; message not sent."}

    payload = {"msg_type": "text", "content": {"text": message}}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                url,
                headers={"Content-Type": "application/json; charset=utf-8"},
                json=payload,
            )
    except httpx.RequestError as exc:
        return {"error": "webhook_unreachable", "detail": str(exc)}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code < 400 and (data.get("code") == 0 or data.get("StatusCode") == 0):
        return {"ok": True}
    return {"error": f"feishu_{resp.status_code}", "detail": data}


__all__ = ["send_feishu"]
