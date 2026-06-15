"""Thin Claude client wrapper.

Responsibilities:
- Build an Anthropic client (Bedrock or native) based on env vars
- Expose a frozen system prompt assembled from config/prompts/*.md
- Track cumulative token usage + cost across a pipeline run
- Provide tool schema + helpers used by signal_extractor and daily_writer

Provider selection (HH_LLM_PROVIDER env var):
  - "bedrock"  → anthropic.AnthropicBedrock with AWS_BEARER_TOKEN_BEDROCK
  - "anthropic" / unset → anthropic.Anthropic with ANTHROPIC_API_KEY
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from ..utils.logger import get_logger

log = get_logger("claude_client")

# --- Model pricing ($/1M tokens) as of 2026-04 ---
# Keys are normalized model names; both native and Bedrock IDs map here.
PRICING = {
    "claude-opus-4-7": {"input": 5.0, "cache_write": 6.25, "cache_read": 0.5, "output": 25.0},
    "claude-opus-4-6": {"input": 5.0, "cache_write": 6.25, "cache_read": 0.5, "output": 25.0},
    "claude-sonnet-4-6": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.3, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "cache_write": 1.25, "cache_read": 0.1, "output": 5.0},
}


def _normalize_model_id(model: str) -> str:
    """Map Bedrock-formatted IDs (us.anthropic.claude-sonnet-4-6) to PRICING keys."""
    # Strip Bedrock region prefix and 'anthropic.' namespace
    stripped = model.removeprefix("us.").removeprefix("eu.").removeprefix("apac.")
    stripped = stripped.removeprefix("anthropic.")
    # Strip Bedrock version suffix '-v1' / '-v2' if present
    for suffix in ("-v1", "-v2", "-v3"):
        if stripped.endswith(suffix):
            stripped = stripped[: -len(suffix)]
            break
    return stripped

# --- Paths ---
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "prompts"


@dataclass
class CostTracker:
    calls: int = 0
    input_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    by_model: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, model: str, usage: Any) -> None:
        """Add a single API response's usage to the running totals."""
        ins = getattr(usage, "input_tokens", 0) or 0
        cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cr = getattr(usage, "cache_read_input_tokens", 0) or 0
        out = getattr(usage, "output_tokens", 0) or 0

        self.calls += 1
        self.input_tokens += ins
        self.cache_write_tokens += cw
        self.cache_read_tokens += cr
        self.output_tokens += out

        p = PRICING.get(_normalize_model_id(model), PRICING["claude-sonnet-4-6"])
        call_cost = (
            ins * p["input"] / 1_000_000
            + cw * p["cache_write"] / 1_000_000
            + cr * p["cache_read"] / 1_000_000
            + out * p["output"] / 1_000_000
        )
        self.usd += call_cost

        model_stats = self.by_model.setdefault(
            model, {"calls": 0, "input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
        )
        model_stats["calls"] += 1
        model_stats["input"] += ins
        model_stats["cache_write"] += cw
        model_stats["cache_read"] += cr
        model_stats["output"] += out

    def summary(self) -> str:
        return (
            f"calls={self.calls} "
            f"in={self.input_tokens} cache_w={self.cache_write_tokens} "
            f"cache_r={self.cache_read_tokens} out={self.output_tokens} "
            f"usd=${self.usd:.4f}"
        )


def load_prompt(name: str) -> str:
    """Load a prompt markdown file from config/prompts/."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def build_extract_system() -> list[dict[str, Any]]:
    """Build the frozen system prompt for signal extraction.

    Combines taxonomy + extract_signal prompts. A single cache_control on the
    last block caches both after the first call (auto prefix caching).
    Result is stable byte-for-byte across calls — do NOT insert datetime /
    UUIDs / per-request content here.
    """
    taxonomy = load_prompt("taxonomy")
    extract = load_prompt("extract_signal")
    # extract_signal contains the SYSTEM section + few-shot examples.
    # We inline the TAXONOMY placeholder so the prompt is self-contained.
    full = extract.replace("{{TAXONOMY}}", taxonomy)
    return [
        {
            "type": "text",
            "text": full,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_digest_system() -> list[dict[str, Any]]:
    """System prompt for daily digest. Called once per day, caching less critical
    but still included for consistency."""
    digest = load_prompt("daily_digest")
    return [
        {
            "type": "text",
            "text": digest,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def make_client(max_retries: int = 4, timeout: float = 300.0):
    """Construct an Anthropic-compatible client (native or Bedrock) with pipeline defaults.

    Provider selection via HH_LLM_PROVIDER env var. Both clients expose the same
    `messages.create()` API, so the rest of the pipeline doesn't need to know.

    max_retries=4 (SDK default is 2) — resilience against transient 429/5xx.
    timeout default 300s; callers that need to fail loud sooner (e.g. the signal
    extractor under HH_EXTRACT_TIMEOUT_S) pass a smaller value explicitly.
    """
    provider = (os.getenv("HH_LLM_PROVIDER") or "anthropic").lower()

    if provider == "bedrock":
        bearer_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        if not bearer_token:
            raise RuntimeError(
                "AWS_BEARER_TOKEN_BEDROCK not set. Add it to .env (with HH_LLM_PROVIDER=bedrock)."
            )
        region = os.getenv("AWS_REGION", "us-east-1")
        log.info("using Bedrock provider (region=%s)", region)
        return anthropic.AnthropicBedrock(
            aws_region=region,
            max_retries=max_retries,
            timeout=timeout,
        )

    # Default: native Anthropic API
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to .env, or set HH_LLM_PROVIDER=bedrock."
        )
    log.info("using native Anthropic provider")
    return anthropic.Anthropic(api_key=api_key, max_retries=max_retries, timeout=timeout)


# --- Model ID resolution per provider ---

# When HH_LLM_PROVIDER=bedrock, these IDs are used; otherwise the native names.
BEDROCK_MODEL_IDS = {
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6",
    "claude-opus-4-6": "us.anthropic.claude-opus-4-6-v1",
    "claude-opus-4-7": "us.anthropic.claude-opus-4-6-v1",  # fallback: 4.7 unavailable on Bedrock
    "claude-haiku-4-5": "us.anthropic.claude-haiku-4-5",   # may not be available; try first
}


def resolve_model_id(logical_name: str) -> str:
    """Return the model ID to pass to messages.create(), based on provider."""
    provider = (os.getenv("HH_LLM_PROVIDER") or "anthropic").lower()
    if provider == "bedrock":
        return BEDROCK_MODEL_IDS.get(logical_name, logical_name)
    return logical_name


# ---- Tool schema for signal extraction (strict JSON via tool_use) ----

EXTRACT_TOOL = {
    "name": "extract_signal",
    "description": "Return the extracted structured summary of this signal per HH Research taxonomy.",
    "input_schema": {
        "type": "object",
        "properties": {
            "track": {
                "type": "string",
                "enum": ["基础模型", "认知模型", "多模态智能", "世界模型", "AI infra", "ai4s", "其他"],
            },
            "is_headline_candidate": {"type": "boolean"},
            "headline_priority": {"type": "integer", "minimum": 1, "maximum": 5},
            "summary_zh": {"type": "string"},
            "cognitive_takeaway_zh": {"type": "string"},
            "core_findings_zh": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "arXiv only; empty for X / RSS / OpenAlex non-paper",
            },
            "method_framework_zh": {
                "type": "string",
                "description": "arXiv only; empty string for non-paper",
            },
            "method_detail_zh": {
                "type": "string",
                "description": "arXiv only; empty string for non-paper",
            },
            "result_summary_zh": {
                "type": "string",
                "description": "arXiv only; empty string for non-paper",
            },
            "key_terms": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
            "entities": {
                "type": "object",
                "properties": {
                    "organizations": {"type": "array", "items": {"type": "string"}},
                    "people": {"type": "array", "items": {"type": "string"}},
                    "models_or_papers": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["organizations", "people", "models_or_papers"],
                "additionalProperties": False,
            },
            "signal_source_zh": {"type": "string"},
            "novelty_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "needs_human_review": {"type": "boolean"},
        },
        "required": [
            "track", "is_headline_candidate", "headline_priority",
            "summary_zh", "cognitive_takeaway_zh",
            "core_findings_zh", "method_framework_zh", "method_detail_zh", "result_summary_zh",
            "key_terms", "entities", "signal_source_zh", "novelty_score", "needs_human_review",
        ],
        "additionalProperties": False,
    },
}


def extract_tool_input(response: anthropic.types.Message) -> dict[str, Any] | None:
    """Pull the tool_use input dict out of a response.

    Returns None if the response didn't call the tool (e.g. model refused).
    """
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_signal":
            # block.input may be dict-like or JSON string depending on SDK version
            if isinstance(block.input, dict):
                return block.input
            try:
                return json.loads(block.input)
            except (TypeError, ValueError):
                logging.getLogger("claude_client").warning(
                    "tool_use input not JSON-decodable: %r", block.input
                )
                return None
    return None
