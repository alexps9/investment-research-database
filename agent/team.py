"""Multi-agent team assembly (LangGraph era).

Pipelines are orchestrated by ``agent.graph`` and triggered via ``agent.run`` or
``agent.service`` HTTP endpoints. Individual agent nodes live in their packages:

    agent/ingestion_agent   fetch → create signals
    agent/analysis_agent    signal → structured intelligence
    agent/entity_agent      analysis → knowledge graph
    agent/alert_agent       important events → Feishu push
    agent/digest_agent      daily brief → Feishu push
    agent/data_agent        read-only Q&A (HTTP /qa)
"""
from __future__ import annotations

from agent.alert_agent.node import run_alerts
from agent.analysis_agent import run_analysis
from agent.digest_agent.node import run_digest
from agent.entity_agent import run_entity_extraction
from agent.graph import get_digest_graph, get_intelligence_graph
from agent.ingestion_agent import run_ingestion

__all__ = [
    "get_intelligence_graph",
    "get_digest_graph",
    "run_ingestion",
    "run_analysis",
    "run_entity_extraction",
    "run_alerts",
    "run_digest",
]
