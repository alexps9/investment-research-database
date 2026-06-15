"""Model-client configuration for the AutoGen agents.

Uses an OpenAI-compatible chat endpoint. Defaults to DeepSeek (the same provider
the backend uses for RAG), but any OpenAI-compatible API works by overriding the
env vars below. DeepSeek/SiliconFlow/etc. are not in AutoGen's known-model table,
so we pass an explicit ``model_info``.

Env:
    LLM_API_KEY    (or DEEPSEEK_API_KEY)  – required
    LLM_BASE_URL   default https://api.deepseek.com/v1
    LLM_MODEL      default deepseek-chat
"""
from __future__ import annotations

import os

from autogen_ext.models.openai import OpenAIChatCompletionClient


def get_model_client() -> OpenAIChatCompletionClient:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set LLM_API_KEY (or DEEPSEEK_API_KEY) to an OpenAI-compatible chat API key."
        )
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        # Required for non-OpenAI models: describe the model's capabilities.
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,
        },
        # Tool-using agents in a team behave better without parallel tool calls.
        parallel_tool_calls=False,
    )
