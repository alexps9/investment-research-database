"""LangChain chat model configuration for LangGraph agents.

Uses an OpenAI-compatible endpoint (LiteLLM gateway → Bedrock Claude by default).

Env:
    LLM_API_KEY    (or DEEPSEEK_API_KEY)  – required
    LLM_BASE_URL   default http://litellm:4000/v1 (server) or https://api.deepseek.com/v1
    LLM_MODEL      default deepseek-chat (alias on LiteLLM) or claude-sonnet-4-6
"""
from __future__ import annotations

import os
from typing import Any, Optional, Type

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


def get_chat_model(
    *,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    model: Optional[str] = None,
) -> ChatOpenAI:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set LLM_API_KEY (or DEEPSEEK_API_KEY) to an OpenAI-compatible chat API key."
        )
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model_name = model or os.getenv("LLM_MODEL", "deepseek-chat")
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def structured_llm(
    schema: Type[BaseModel],
    *,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    model: Optional[str] = None,
) -> Any:
    """Return a chat model bound to a Pydantic schema for structured output."""
    return get_chat_model(temperature=temperature, max_tokens=max_tokens, model=model).with_structured_output(schema)
