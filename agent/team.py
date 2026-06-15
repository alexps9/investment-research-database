"""Multi-agent team assembly.

Starts as a single-specialist team (the data agent) and is structured so more
specialists (e.g. a planner, a research/analyst agent, a funding agent) can be
added to the participants list without changing callers.
"""
from __future__ import annotations

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from agent.data_agent import build_data_agent


def build_team(model_client, max_messages: int = 20):
    """Build the multi-agent team. Currently: [data_agent]."""
    data_agent = build_data_agent(model_client)

    # Stop when an agent says TERMINATE, or after a hard message cap (safety net).
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages)

    return RoundRobinGroupChat(
        participants=[data_agent],
        termination_condition=termination,
    )
