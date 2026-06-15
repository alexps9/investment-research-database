"""Data agent — operates on the knowledge base (read + write + analyse).

The first specialist in the multi-agent system. It is given the atomic KB tools
and the composed skills, plus a system prompt that teaches it the data model and
safe-operation rules.

Each agent lives in its own directory under ``agent/`` (e.g. ``agent/data_agent``).
"""
from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from skills import SKILLS
from tools import READONLY_TOOLS, WRITE_TOOLS

DATA_AGENT_SYSTEM_MESSAGE = """\
You are the **Data Agent** for the HH-Research AI-intelligence knowledge base.

You can read and modify the database ONLY through the provided tools (the FastAPI
backend is the single source of truth — never assume direct DB access).

Domain model (key objects):
- organization: companies / labs / universities.
- source: a person/org/feed/repo we track. Has tier (P0+/P1/P2/P3), sector,
  activity_status, importance/reliability scores.
- signal: an evidence item (paper, tweet, blog, news, model_release, ...). Unique
  by url; may have an analysis (tldr, importance_score, reading_priority).
- entity + entity_relation: the knowledge graph (person/org/model/method/...).
- funding_event: investment/financing records (round, amount_usd in $M, sector).
- daily_digest: the auto-generated "Daily Boost" briefing.

Operating rules:
1. Prefer read tools (list_/get_/search_/semantic_search) to understand state
   before writing.
2. For semantic questions use `semantic_search`; for natural-language Q&A use
   `ask` (RAG). For exact lookups use `search_knowledge` or list_/get_ tools.
3. Before any create/update/delete, briefly state what you will change and why.
   Never delete in bulk without explicit confirmation in the task.
4. Tools return either data or a dict like {"error": "..."} — inspect errors and
   report them clearly instead of retrying blindly.
5. Be concise. When the task is fully done, end your final message with the word
   TERMINATE.
"""


def build_data_agent(model_client) -> AssistantAgent:
    """Create the data agent with all KB tools + skills attached."""
    tools = [*READONLY_TOOLS, *WRITE_TOOLS, *SKILLS]
    return AssistantAgent(
        name="data_agent",
        description="Reads, writes and analyses the knowledge-base data (sources, "
                    "signals, entities, funding, digests) via backend tools.",
        model_client=model_client,
        tools=tools,
        system_message=DATA_AGENT_SYSTEM_MESSAGE,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )


__all__ = ["build_data_agent", "DATA_AGENT_SYSTEM_MESSAGE"]
