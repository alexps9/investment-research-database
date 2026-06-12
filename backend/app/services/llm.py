"""Thin async clients for OpenAI-compatible embedding & chat APIs.

Embeddings  -> OpenAI  (text-embedding-3-small, 1536 dims)
Chat / RAG  -> DeepSeek (deepseek-chat, OpenAI-compatible endpoint)

Both providers expose the same request/response shape, so a single httpx
helper covers them. Keys are read from settings; when a key is missing the
corresponding feature is considered "disabled" (callers should check first).
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


class LLMNotConfigured(RuntimeError):
    """Raised when an LLM/embedding feature is used without an API key."""


def embeddings_enabled() -> bool:
    return bool(settings.openai_api_key)


def chat_enabled() -> bool:
    return bool(settings.deepseek_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per input text."""
    if not embeddings_enabled():
        raise LLMNotConfigured("OPENAI_API_KEY is not set; embeddings disabled.")
    if not texts:
        return []

    url = f"{settings.openai_base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {"model": settings.embedding_model, "input": texts}

    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # API returns items in input order, but sort by index to be safe.
    items = sorted(data["data"], key=lambda d: d["index"])
    return [item["embedding"] for item in items]


async def embed_text(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]


async def chat(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """Send a chat-completion request to the DeepSeek endpoint; return content."""
    if not chat_enabled():
        raise LLMNotConfigured("DEEPSEEK_API_KEY is not set; chat disabled.")

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}"}
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]
