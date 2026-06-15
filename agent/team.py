"""Multi-agent team assembly.

Specialists each live in their own package under ``agent/`` (``agent/data_agent``,
``agent/alert_agent``, ``agent/digest_agent``, ...). ``build_team`` wires the
chat-oriented specialists into a group chat; ``build_alert_agent`` and
``build_digest_agent`` are also exported for their pipelines, which drive them
directly (see ``agent/alert_agent/pipeline.py`` / ``agent/digest_agent/pipeline.py``).
"""
from __future__ import annotations

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from agent.data_agent import build_data_agent
from agent.alert_agent import build_alert_agent
from agent.digest_agent import build_digest_agent


def build_team(model_client, max_messages: int = 20):
    """Build the multi-agent team.

    Currently a single-specialist chat team (the data agent). The alert and digest
    agents are pipeline-driven specialists (they process a batch of signals rather
    than holding open-ended chat), so they are exposed via ``build_alert_agent`` /
    ``build_digest_agent`` instead of being round-robin participants here.
    """
    data_agent = build_data_agent(model_client)

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages)

    return RoundRobinGroupChat(
        participants=[data_agent],
        termination_condition=termination,
    )


__all__ = ["build_team", "build_alert_agent", "build_digest_agent"]
