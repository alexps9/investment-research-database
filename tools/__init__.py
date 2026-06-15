"""Atomic knowledge-base tools, organised one package per functional domain.

Layout (each directory is named after its function):
    tools/dashboard   overview counts + keyword search
    tools/sources     source CRUD
    tools/signals     signal CRUD
    tools/entities    entity & knowledge-graph
    tools/search      semantic search & RAG
    tools/funding     investment / financing
    tools/daily       Daily Boost digests
    tools/notify      outbound notifications (Feishu/Lark push)
    tools/websearch   free web search + primary-source lookup
    tools/_client     shared HTTP plumbing (not a tool)

Import the curated tool lists into any agent framework:

    from tools import READONLY_TOOLS, WRITE_TOOLS, ALL_TOOLS

``READONLY_TOOLS`` never mutate data (safe to expose widely); ``WRITE_TOOLS``
create/update/delete and should be gated behind confirmation in production.
"""
from tools.dashboard import dashboard_stats, search_knowledge
from tools.sources import (
    list_sources, get_source, create_source, update_source, delete_source,
)
from tools.signals import (
    list_signals, get_signal, create_signal, update_signal, delete_signal,
    add_signal_analysis, link_signal_entity, set_signal_status,
)
from tools.entities import (
    list_entities, get_entity, get_entity_wiki, add_entity_relation,
    create_entity, add_entity_alias, get_graph_relations, find_entity_by_name,
)
from tools.search import ai_status, semantic_search, ask, reindex_embeddings
from tools.funding import (
    list_funding, get_funding, funding_trends,
    create_funding, update_funding, delete_funding,
)
from tools.daily import get_daily_digest, list_daily_digests, generate_daily_digest
from tools.websearch import search_web, find_primary_source
from tools.notify import send_feishu

# Read-only (safe) tools
READONLY_TOOLS = [
    dashboard_stats, search_knowledge,
    list_sources, get_source,
    list_signals, get_signal,
    list_entities, get_entity, get_entity_wiki, get_graph_relations, find_entity_by_name,
    ai_status, semantic_search, ask,
    list_funding, get_funding, funding_trends,
    get_daily_digest, list_daily_digests,
    search_web, find_primary_source,
]

# Mutating tools (create / update / delete / index / generate / notify)
WRITE_TOOLS = [
    create_source, update_source, delete_source,
    create_signal, update_signal, delete_signal,
    add_signal_analysis, link_signal_entity, set_signal_status,
    create_entity, add_entity_alias, add_entity_relation, reindex_embeddings,
    create_funding, update_funding, delete_funding,
    generate_daily_digest,
    send_feishu,
]

ALL_TOOLS = READONLY_TOOLS + WRITE_TOOLS

__all__ = [
    "READONLY_TOOLS", "WRITE_TOOLS", "ALL_TOOLS",
    "dashboard_stats", "search_knowledge",
    "list_sources", "get_source", "create_source", "update_source", "delete_source",
    "list_signals", "get_signal", "create_signal", "update_signal", "delete_signal",
    "add_signal_analysis", "link_signal_entity", "set_signal_status",
    "list_entities", "get_entity", "get_entity_wiki", "add_entity_relation",
    "create_entity", "add_entity_alias", "get_graph_relations", "find_entity_by_name",
    "ai_status", "semantic_search", "ask", "reindex_embeddings",
    "list_funding", "get_funding", "funding_trends",
    "create_funding", "update_funding", "delete_funding",
    "get_daily_digest", "list_daily_digests", "generate_daily_digest",
    "search_web", "find_primary_source", "send_feishu",
]
