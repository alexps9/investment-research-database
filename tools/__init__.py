"""Reusable, atomic knowledge-base tools (one function per backend endpoint).

Import the curated tool lists into any agent framework:

    from tools import READONLY_TOOLS, WRITE_TOOLS, ALL_TOOLS

``READONLY_TOOLS`` never mutate data (safe to expose widely); ``WRITE_TOOLS``
create/update/delete and should be gated behind confirmation in production.
"""
from tools import kb_client as kb

# Read-only (safe) tools
READONLY_TOOLS = [
    kb.dashboard_stats,
    kb.search_knowledge,
    kb.list_sources,
    kb.get_source,
    kb.list_signals,
    kb.get_signal,
    kb.list_entities,
    kb.get_entity,
    kb.get_entity_wiki,
    kb.ai_status,
    kb.semantic_search,
    kb.ask,
    kb.list_funding,
    kb.get_funding,
    kb.funding_trends,
    kb.get_daily_digest,
    kb.list_daily_digests,
]

# Mutating tools (create / update / delete / index / generate)
WRITE_TOOLS = [
    kb.create_source,
    kb.update_source,
    kb.delete_source,
    kb.create_signal,
    kb.update_signal,
    kb.delete_signal,
    kb.add_entity_relation,
    kb.reindex_embeddings,
    kb.create_funding,
    kb.update_funding,
    kb.delete_funding,
    kb.generate_daily_digest,
]

ALL_TOOLS = READONLY_TOOLS + WRITE_TOOLS

__all__ = ["kb", "READONLY_TOOLS", "WRITE_TOOLS", "ALL_TOOLS"]
