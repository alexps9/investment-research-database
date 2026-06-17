"""LLM clients for the deep-research agent — all routed through the LiteLLM
gateway (OpenAI-compatible), the same endpoint the rest of the stack uses.

Mirrors open_deep_research's four model roles (summarization / research /
compression / final report) but points them at one gateway model by default so
deployment stays simple. Each role can be overridden by an env var if you want
to use a cheaper model for summarization, etc.
"""
from __future__ import annotations

import asyncio
import os

from langchain_openai import ChatOpenAI

# Global throttle on concurrent in-flight LLM calls across ALL research runs.
# This decouples "how many research jobs are in progress" from "how much load
# hits the shared LiteLLM gateway", so we can run many jobs concurrently while
# keeping the single gateway worker + Bedrock account from being overwhelmed.
_LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "8"))
_llm_sem: asyncio.Semaphore | None = None


def _llm_semaphore() -> asyncio.Semaphore:
    # Lazily created so it binds to the running event loop.
    global _llm_sem
    if _llm_sem is None:
        _llm_sem = asyncio.Semaphore(_LLM_MAX_CONCURRENCY)
    return _llm_sem


async def ainvoke(llm: ChatOpenAI, messages):
    """Invoke an LLM through the global concurrency gate."""
    async with _llm_semaphore():
        return await llm.ainvoke(messages)


def _base_url() -> str:
    return os.getenv("LLM_BASE_URL", "http://litellm:4000/v1")


def _api_key() -> str:
    key = os.getenv("LLM_API_KEY") or os.getenv("LITELLM_MASTER_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "Set LLM_API_KEY (LiteLLM master key) for the deep-research agent."
        )
    return key


def _model(role_env: str, default_env: str = "LLM_MODEL", fallback: str = "claude-sonnet-4-6") -> str:
    return os.getenv(role_env) or os.getenv(default_env) or fallback


def make_llm(role: str, *, temperature: float = 0.0, max_tokens: int | None = None) -> ChatOpenAI:
    """Build a ChatOpenAI bound to the gateway for the given role.

    role ∈ {"summarization", "research", "compression", "report"} — selects an
    optional per-role model override env (e.g. RESEARCH_MODEL).
    """
    role_env = {
        "summarization": "SUMMARIZATION_MODEL",
        "research": "RESEARCH_MODEL",
        "compression": "COMPRESSION_MODEL",
        "report": "FINAL_REPORT_MODEL",
    }.get(role, "LLM_MODEL")

    return ChatOpenAI(
        model=_model(role_env),
        base_url=_base_url(),
        api_key=_api_key(),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=120,
        max_retries=2,
    )
