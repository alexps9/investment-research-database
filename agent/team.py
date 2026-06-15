"""Multi-agent team assembly.

Specialists each live in their own package under ``agent/`` (``agent/data_agent``,
``agent/alert_agent``, ...). ``build_team`` wires the chat-oriented specialists
into a group chat; ``build_alert_agent`` is also exported for the alert pipeline,
which drives it per-signal (see ``agent/alert_agent/pipeline.py``).
"""
from __future__ import annotations

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from agent.data_agent import build_data_agent
from agent.alert_agent import build_alert_agent


def build_team(model_client, max_messages: int = 20):
    """Build the multi-agent team.

    Currently a single-specialist team (the data agent). The alert agent is a
    pipeline-driven specialist (it processes signals one at a time rather than in
    open-ended chat), so it is exposed via ``build_alert_agent`` instead of being
    a round-robin participant here.
    """
    data_agent = build_data_agent(model_client)

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages)

    return RoundRobinGroupChat(
        participants=[data_agent],
        termination_condition=termination,
    )


__all__ = ["build_team", "build_alert_agent"]
