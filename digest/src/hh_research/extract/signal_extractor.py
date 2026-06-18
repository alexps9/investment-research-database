"""Signal extractor.

Takes a list of Signal objects (freshly collected from arXiv/X, pre-LLM) and
fills in the LLM-derived fields (summary_zh, category, novelty_score, etc.)
by calling Claude Sonnet 4.6 with tool_use for strict JSON output.

Uses Anthropic prompt caching on the ~3K-token system prompt (taxonomy +
few-shot), which Sonnet 4.6 supports at 2048+ token cached prefixes.
"""

from __future__ import annotations

import os
from typing import Any

import anthropic
from pydantic import ValidationError

from ..storage.schemas import Signal
from ..utils.logger import get_logger
from .claude_client import (
    EXTRACT_TOOL,
    CostTracker,
    build_extract_system,
    extract_tool_input,
    make_client,
    resolve_model_id,
)

log = get_logger("signal_extractor")

# Logical name; resolve_model_id() picks the right ID per provider (native vs Bedrock).
MODEL_LOGICAL = "claude-sonnet-4-6"
MAX_TOKENS = 1000


class SignalExtractor:
    def __init__(
        self,
        client=None,
        cost: CostTracker | None = None,
    ) -> None:
        # 5-29 fix: bounded timeout so a stalled Bedrock connection fails within
        # HH_EXTRACT_TIMEOUT_S (default 120s) instead of hanging ~30 min.
        # max_retries=1 keeps total worst-case bounded (1 retry × timeout).
        timeout_s = float(os.getenv("HH_EXTRACT_TIMEOUT_S", "120"))
        self.client = client or make_client(max_retries=1, timeout=timeout_s)
        self.cost = cost or CostTracker()
        self.system = build_extract_system()
        self.model = resolve_model_id(MODEL_LOGICAL)

    def extract_one(self, signal: Signal) -> Signal:
        """Extract LLM fields for one signal. Returns the signal with fields filled
        (or left None on LLM/API failure, with needs_human_review=True)."""
        user_text = self._format_user(signal)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=self.system,
                tools=[EXTRACT_TOOL],
                tool_choice={"type": "tool", "name": "extract_signal"},
                messages=[{"role": "user", "content": user_text}],
            )
        except anthropic.BadRequestError as e:
            log.warning("bad request on %s: %s", signal.source_id, e.message)
            signal.needs_human_review = True
            return signal
        except anthropic.RateLimitError:
            log.warning("rate-limited after retries on %s; skipping", signal.source_id)
            signal.needs_human_review = True
            return signal
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            # 5-29 fix: bounded timeout / connection drop → mark for review and
            # move on, instead of hanging the whole pipeline on one stalled call.
            log.warning("timeout/connection error on %s: %s", signal.source_id, e)
            signal.needs_human_review = True
            return signal
        except anthropic.APIStatusError as e:
            log.error("API %d on %s: %s", e.status_code, signal.source_id, e.message)
            signal.needs_human_review = True
            return signal

        self.cost.record(self.model, response.usage)

        tool_input = extract_tool_input(response)
        if tool_input is None:
            log.warning("no tool_use returned for %s; marking for review", signal.source_id)
            signal.needs_human_review = True
            return signal

        # Merge extracted fields into the Signal (HH 5-track schema)
        try:
            signal.track = tool_input.get("track")
            signal.is_headline_candidate = bool(tool_input.get("is_headline_candidate", False))
            signal.headline_priority = int(tool_input.get("headline_priority", 1))
            signal.summary_zh = tool_input.get("summary_zh")
            signal.cognitive_takeaway_zh = tool_input.get("cognitive_takeaway_zh")
            signal.core_findings_zh = tool_input.get("core_findings_zh", []) or []
            signal.method_framework_zh = tool_input.get("method_framework_zh") or None
            signal.method_detail_zh = tool_input.get("method_detail_zh") or None
            signal.result_summary_zh = tool_input.get("result_summary_zh") or None
            signal.key_terms = tool_input.get("key_terms", []) or []
            signal.novelty_score = tool_input.get("novelty_score")
            signal.signal_source_zh = tool_input.get("signal_source_zh")
            if not signal.needs_human_review:
                signal.needs_human_review = bool(tool_input.get("needs_human_review", False))
            signal.extract_json = _dump_json(tool_input)
        except (ValidationError, KeyError, TypeError) as e:
            log.warning("validation error on %s: %s", signal.source_id, e)
            signal.needs_human_review = True

        return signal

    def extract_many(self, signals: list[Signal]) -> list[Signal]:
        """Process a list of signals sequentially. Order preserved.

        Note: The first call primes the cache (paying ~1.25x on input); subsequent
        calls read from cache at ~0.1x. Verify via self.cost.cache_read_tokens.
        """
        log.info("extracting %d signals with %s ...", len(signals), self.model)
        out: list[Signal] = []
        for i, sig in enumerate(signals):
            out.append(self.extract_one(sig))
            if (i + 1) % 20 == 0:
                log.info("  ... %d/%d done, cost so far: %s", i + 1, len(signals), self.cost.summary())
        log.info("extract complete. %s", self.cost.summary())
        log.info(
            "cache efficiency: %d read / %d write tokens",
            self.cost.cache_read_tokens,
            self.cost.cache_write_tokens,
        )
        return out

    def _format_user(self, signal: Signal) -> str:
        """The per-signal user message — keep this as the ONLY volatile part of the
        request so the cached system prefix stays valid."""
        return (
            f"SOURCE: {signal.source}\n"
            f"AUTHOR: {signal.author_name}\n"
            f"URL: {signal.url}\n"
            f"RAW:\n{signal.raw_text}"
        )


def _dump_json(obj: Any) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
