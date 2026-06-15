"""Shared HTTP plumbing for all tool packages.

The backend (FastAPI) is the single source of truth and the only component that
touches PostgreSQL; every tool here is a thin async wrapper over one REST endpoint
and always returns JSON-serialisable values (never raises on HTTP errors — a
structured ``{"error": ...}`` dict is returned instead).

Configuration (env):
    KB_API_BASE_URL   backend base URL (default: http://localhost:8000)
    KB_API_TIMEOUT    per-request timeout in seconds (default: 30)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

API_BASE_URL = os.getenv("KB_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = "/api"
TIMEOUT = float(os.getenv("KB_API_TIMEOUT", "30"))

VALID_RELATION_TYPES = [
    "WORKS_AT", "AFFILIATED_WITH", "PUBLISHED", "AUTHORED", "RELEASED",
    "PROPOSES", "USES", "EVALUATES_ON", "BUILT_ON", "MENTIONS", "ABOUT",
    "FOCUSES_ON", "RELATED_TO", "COMPETES_WITH", "IMPROVES", "INTRODUCES",
]


async def request(method: str, path: str, **kwargs: Any) -> Any:
    """Call the backend and return parsed JSON, or a structured error dict."""
    url = f"{API_BASE_URL}{API_PREFIX}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        return {"error": "backend_unreachable", "detail": str(exc), "url": url}

    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {"error": f"http_{resp.status_code}", "detail": detail, "url": url}

    if resp.status_code == 204 or not resp.content:
        return {"ok": True}
    return resp.json()


def clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop None values so we don't send empty query params / body fields."""
    return {k: v for k, v in params.items() if v is not None}
