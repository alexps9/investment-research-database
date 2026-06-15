"""LangGraph orchestration for the HH-Research multi-agent pipeline."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.alert_agent.node import alert_node
from agent.analysis_agent import analysis_node
from agent.digest_agent.node import digest_node
from agent.entity_agent import entity_node
from agent.ingestion_agent import ingestion_node
from agent.state import PipelineState


def build_intelligence_graph():
    """Main pipeline: Ingestion → Analysis → (Entity + Alert in parallel)."""
    graph = StateGraph(PipelineState)
    graph.add_node("ingest", ingestion_node)
    graph.add_node("analyze", analysis_node)
    graph.add_node("entity", entity_node)
    graph.add_node("alert", alert_node)

    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "analyze")
    graph.add_edge("analyze", "entity")
    graph.add_edge("analyze", "alert")
    graph.add_edge("entity", END)
    graph.add_edge("alert", END)

    return graph.compile()


def build_digest_graph():
    """Daily digest graph (standalone)."""
    graph = StateGraph(PipelineState)
    graph.add_node("digest", digest_node)
    graph.add_edge(START, "digest")
    graph.add_edge("digest", END)
    return graph.compile()


# Singleton compiled graphs
_intelligence_graph = None
_digest_graph = None


def get_intelligence_graph():
    global _intelligence_graph
    if _intelligence_graph is None:
        _intelligence_graph = build_intelligence_graph()
    return _intelligence_graph


def get_digest_graph():
    global _digest_graph
    if _digest_graph is None:
        _digest_graph = build_digest_graph()
    return _digest_graph
