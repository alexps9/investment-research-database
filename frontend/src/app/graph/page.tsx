'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { EntityRelation } from '@/lib/types';
import { ENTITY_COLORS, entityColor } from '@/lib/entityColors';
import KnowledgeGraph, { type GraphNode, type GraphLink } from '@/components/graph/KnowledgeGraph';
import { Search, BookOpen, X, Network } from 'lucide-react';

export default function GraphPage() {
  const [relations, setRelations] = useState<EntityRelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [disabledTypes, setDisabledTypes] = useState<Set<string>>(new Set());

  useEffect(() => {
    api
      .get<EntityRelation[]>('/graph/relations?limit=1000')
      .then(setRelations)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // build the full node/link sets from relations
  const { allNodes, allLinks } = useMemo(() => {
    const nodeMap = new Map<string, GraphNode>();
    const links: GraphLink[] = [];
    for (const rel of relations) {
      if (rel.subject) nodeMap.set(rel.subject_entity_id, { id: rel.subject_entity_id, name: rel.subject.name, type: rel.subject.entity_type });
      if (rel.object_entity) nodeMap.set(rel.object_entity_id, { id: rel.object_entity_id, name: rel.object_entity.name, type: rel.object_entity.entity_type });
      if (rel.subject && rel.object_entity) {
        links.push({ id: rel.id, source: rel.subject_entity_id, target: rel.object_entity_id, label: rel.relation_type });
      }
    }
    return { allNodes: Array.from(nodeMap.values()), allLinks: links };
  }, [relations]);

  const typesPresent = useMemo(() => {
    const s = new Set<string>();
    allNodes.forEach((n) => s.add(n.type));
    return Array.from(s).sort();
  }, [allNodes]);

  // apply type filter
  const { nodes, links } = useMemo(() => {
    const keptNodes = allNodes.filter((n) => !disabledTypes.has(n.type));
    const keptIds = new Set(keptNodes.map((n) => n.id));
    const keptLinks = allLinks.filter((l) => keptIds.has(l.source) && keptIds.has(l.target));
    return { nodes: keptNodes, links: keptLinks };
  }, [allNodes, allLinks, disabledTypes]);

  const degree = useMemo(() => {
    const d: Record<string, number> = {};
    for (const l of links) {
      d[l.source] = (d[l.source] ?? 0) + 1;
      d[l.target] = (d[l.target] ?? 0) + 1;
    }
    return d;
  }, [links]);

  const selectedRelations = useMemo(() => {
    if (!selected) return [] as EntityRelation[];
    return relations.filter(
      (r) => r.subject_entity_id === selected.id || r.object_entity_id === selected.id,
    );
  }, [selected, relations]);

  function toggleType(t: string) {
    setDisabledTypes((prev) => {
      const next = new Set(prev);
      next.has(t) ? next.delete(t) : next.add(t);
      return next;
    });
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim().toLowerCase();
    if (!q) return;
    const hit = nodes.find((n) => n.name.toLowerCase().includes(q));
    if (hit) {
      setFocusId(hit.id);
      setSelected(hit);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      {/* header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <Network size={22} className="text-blue-600" /> Knowledge Graph
          </h1>
          <p className="text-sm text-gray-500">
            {nodes.length} entities · {links.length} relations
          </p>
        </div>
        <form onSubmit={handleSearch} className="relative w-72">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Locate an entity…"
            className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </form>
      </div>

      <div className="relative flex flex-1 overflow-hidden">
        {/* graph canvas */}
        <div className="relative flex-1 bg-slate-50">
          {loading ? (
            <div className="flex h-full items-center justify-center text-sm text-gray-400">Loading graph…</div>
          ) : nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
              <Network size={40} />
              <p className="text-sm">No relations yet. Add entity relations to populate the graph.</p>
            </div>
          ) : (
            <KnowledgeGraph nodes={nodes} links={links} onSelect={setSelected} focusId={focusId} />
          )}

          {/* legend / type filter */}
          {!loading && typesPresent.length > 0 && (
            <div className="absolute bottom-4 left-4 max-w-[220px] rounded-xl border border-gray-200 bg-white/90 p-3 shadow-sm backdrop-blur">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Entity Types</p>
              <div className="flex flex-wrap gap-1.5">
                {typesPresent.map((t) => {
                  const off = disabledTypes.has(t);
                  return (
                    <button
                      key={t}
                      onClick={() => toggleType(t)}
                      className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs transition ${
                        off ? 'border-gray-200 text-gray-300' : 'border-gray-200 text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <span
                        className="inline-block h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: off ? '#e5e7eb' : (ENTITY_COLORS[t] ?? '#94a3b8') }}
                      />
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* details side panel */}
        {selected && (
          <aside className="w-80 shrink-0 overflow-y-auto border-l border-gray-200 bg-white p-5">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <span
                  className="mb-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
                  style={{ backgroundColor: entityColor(selected.type) }}
                >
                  {selected.type}
                </span>
                <h2 className="text-lg font-bold text-gray-900">{selected.name}</h2>
                <p className="mt-1 text-xs text-gray-400">{degree[selected.id] ?? 0} connections</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>

            <Link
              href={`/wiki/entities/${selected.id}`}
              className="mb-5 flex w-full items-center justify-center gap-1.5 rounded-lg bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <BookOpen size={14} /> Open Wiki
            </Link>

            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Relations ({selectedRelations.length})
            </p>
            <ul className="space-y-2">
              {selectedRelations.map((r) => {
                const outgoing = r.subject_entity_id === selected.id;
                const other = outgoing ? r.object_entity : r.subject;
                const otherId = outgoing ? r.object_entity_id : r.subject_entity_id;
                return (
                  <li key={r.id} className="rounded-lg border border-gray-100 bg-gray-50 p-2 text-xs">
                    <span className="font-medium text-purple-600">{r.relation_type}</span>
                    <span className="mx-1 text-gray-400">{outgoing ? '→' : '←'}</span>
                    <button
                      onClick={() => {
                        if (other) {
                          setSelected({ id: otherId, name: other.name, type: other.entity_type });
                          setFocusId(otherId);
                        }
                      }}
                      className="font-medium text-gray-800 hover:text-blue-600"
                    >
                      {other?.name ?? otherId.slice(0, 8)}
                    </button>
                  </li>
                );
              })}
              {selectedRelations.length === 0 && (
                <li className="text-xs text-gray-400">No relations.</li>
              )}
            </ul>
          </aside>
        )}
      </div>
    </div>
  );
}
