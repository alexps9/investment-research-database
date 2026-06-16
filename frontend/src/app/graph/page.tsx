'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { EntityRelation, SearchHit, AIStatus } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { ENTITY_COLORS, entityColor } from '@/lib/entityColors';
import KnowledgeGraph, { type GraphNode, type GraphLink } from '@/components/graph/KnowledgeGraph';
import { Search, BookOpen, X, Network, Loader2, Sparkles, RefreshCw } from 'lucide-react';

export default function GraphPage() {
  const { t } = useLang();
  const [relations, setRelations] = useState<EntityRelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  // Solo-focus filter: null = show all; string = show only that type.
  const [focusType, setFocusType] = useState<string | null>(null);
  const [focusRelType, setFocusRelType] = useState<string | null>(null);
  const [showRelFilter, setShowRelFilter] = useState(false);
  // Incremented on every filter change to force-remount the canvas so the
  // force simulation restarts from scratch and re-clusters the subgraph.
  const [filterKey, setFilterKey] = useState(0);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [locating, setLocating] = useState(false);
  const [noMatch, setNoMatch] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{ created: number; skipped: number } | null>(null);
  const [inferring, setInferring] = useState(false);
  const [inferResult, setInferResult] = useState<{ created: number; skipped: number } | null>(null);

  useEffect(() => {
    api.get<EntityRelation[]>('/graph/relations?limit=1000').then(setRelations).catch(console.error).finally(() => setLoading(false));
    api.get<AIStatus>('/ai/status').then(setAiStatus).catch(() => setAiStatus(null));
  }, []);

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

  const relTypesPresent = useMemo(() => {
    const s = new Set<string>();
    allLinks.forEach((l) => { if (l.label) s.add(l.label); });
    return Array.from(s).sort();
  }, [allLinks]);

  const { nodes, links } = useMemo(() => {
    // Solo-focus: if a type is focused, include only that type; otherwise all.
    const typeKeptIds = new Set(
      allNodes
        .filter((n) => focusType === null || n.type === focusType)
        .map((n) => n.id),
    );
    const keptLinks = allLinks.filter(
      (l) =>
        typeKeptIds.has(l.source) &&
        typeKeptIds.has(l.target) &&
        (focusRelType === null || l.label === focusRelType),
    );
    // Drop nodes with no kept edges so the subgraph is tight.
    const connected = new Set<string>();
    keptLinks.forEach((l) => { connected.add(l.source); connected.add(l.target); });
    const keptNodes = allNodes.filter((n) => typeKeptIds.has(n.id) && connected.has(n.id));
    return { nodes: keptNodes, links: keptLinks };
  }, [allNodes, allLinks, focusType, focusRelType]);

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
    return relations.filter((r) => r.subject_entity_id === selected.id || r.object_entity_id === selected.id);
  }, [selected, relations]);

  const embeddingsOn = aiStatus?.embeddings_enabled ?? false;

  function toggleType(ty: string) {
    setFocusType((prev) => (prev === ty ? null : ty));
    setFilterKey((k) => k + 1);
  }

  function toggleRelType(ty: string) {
    setFocusRelType((prev) => (prev === ty ? null : ty));
    setFilterKey((k) => k + 1);
  }

  function focusNode(node: GraphNode) {
    setFocusId(node.id);
    setSelected(node);
  }

  async function handleSync() {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await api.post<{ created: number; skipped: number }>('/graph/sync', {});
      setSyncResult(res);
      // Reload relations
      const rels = await api.get<typeof relations>('/graph/relations?limit=1000');
      setRelations(rels);
    } catch (err) {
      alert(`同步失败: ${String(err)}`);
    } finally {
      setSyncing(false);
    }
  }

  async function handleInfer() {
    setInferring(true);
    setInferResult(null);
    try {
      const res = await api.post<{ created: number; skipped: number }>('/graph/infer', {});
      setInferResult(res);
      const rels = await api.get<typeof relations>('/graph/relations?limit=1000');
      setRelations(rels);
    } catch (err) {
      alert(`推断失败: ${String(err)}`);
    } finally {
      setInferring(false);
    }
  }

  // Semantic-first locate: vector search over entities, fall back to substring match.
  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const raw = query.trim();
    if (!raw) return;
    setLocating(true);
    setNoMatch(false);
    try {
      let target: GraphNode | undefined;
      if (embeddingsOn) {
        try {
          const hits = await api.get<SearchHit[]>(`/ai/search?q=${encodeURIComponent(raw)}&types=entity&limit=10`);
          for (const h of hits) {
            const node = nodes.find((n) => n.id === h.object_id);
            if (node) { target = node; break; }
          }
        } catch { /* fall through to substring */ }
      }
      if (!target) {
        const k = raw.toLowerCase();
        target = nodes.find((n) => n.name.toLowerCase().includes(k));
      }
      if (target) focusNode(target);
      else setNoMatch(true);
    } finally {
      setLocating(false);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      {/* header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm shadow-blue-500/30">
            <Network size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">{t('graph.title')}</h1>
            <p className="text-sm text-gray-500">{nodes.length} · {links.length} {t('graph.relations')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing || inferring}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm hover:bg-gray-50 disabled:opacity-50"
            title="从信号源/组织的结构化数据同步显式关系（任职/研究领域/上属机构等）"
          >
            <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
            {syncing ? '同步中…' : '同步关系'}
          </button>
          {syncResult && (
            <span className="text-xs text-green-600">
              +{syncResult.created} 新建，{syncResult.skipped} 已存在
            </span>
          )}
          <button
            onClick={handleInfer}
            disabled={syncing || inferring}
            className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm text-indigo-600 shadow-sm hover:bg-indigo-100 disabled:opacity-50"
            title="推断隐式关系：同事/前同事（共享机构）、共同作者（共享论文）"
          >
            <Sparkles size={14} className={inferring ? 'animate-pulse' : ''} />
            {inferring ? '推断中…' : '推断关系'}
          </button>
          {inferResult && (
            <span className="text-xs text-indigo-600">
              +{inferResult.created} 推断，{inferResult.skipped} 已存在
            </span>
          )}
        </div>
        <form onSubmit={handleSearch} className="relative w-80 max-w-full">
          {embeddingsOn
            ? <Sparkles size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-400" />
            : <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />}
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setNoMatch(false); }}
            placeholder={t('graph.locate')}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-9 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {locating && <Loader2 size={15} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-blue-500" />}
          {noMatch && !locating && (
            <span className="absolute -bottom-5 left-0 text-xs text-amber-600">{t('graph.no_match')}</span>
          )}
        </form>
      </div>

      <div className="relative flex flex-1 overflow-hidden">
        <div className="relative flex-1 bg-slate-50">
          {loading ? (
            <div className="flex h-full items-center justify-center text-sm text-gray-400">{t('graph.loading')}</div>
          ) : nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
              <Network size={40} />
              <p className="text-sm">{t('graph.no_relations')}</p>
            </div>
          ) : (
            <KnowledgeGraph key={filterKey} nodes={nodes} links={links} onSelect={setSelected} focusId={focusId} />
          )}

          {!loading && typesPresent.length > 0 && (
            <div className="absolute bottom-4 left-4 flex flex-col gap-2">
              {/* Node type filter */}
              <div className="max-w-[220px] rounded-xl border border-gray-200 bg-white/90 p-3 shadow-sm backdrop-blur">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{t('graph.entity_types')}</p>
                  {(focusType !== null || focusRelType !== null) && (
                    <button
                      onClick={() => { setFocusType(null); setFocusRelType(null); setFilterKey((k) => k + 1); }}
                      className="rounded px-1.5 py-0.5 text-[10px] text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    >
                      全部
                    </button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {typesPresent.map((ty) => {
                    const active = focusType === ty;
                    const dimmed = focusType !== null && !active;
                    return (
                      <button
                        key={ty}
                        onClick={() => toggleType(ty)}
                        title={active ? '点击取消聚焦' : `只显示 ${ty}`}
                        className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs transition ${
                          active
                            ? 'border-blue-400 bg-blue-50 font-semibold text-blue-700 ring-1 ring-blue-300'
                            : dimmed
                            ? 'border-gray-100 text-gray-300'
                            : 'border-gray-200 text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: dimmed ? '#e5e7eb' : (ENTITY_COLORS[ty] ?? '#94a3b8') }} />
                        {ty}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Relation type filter (toggle) */}
              {relTypesPresent.length > 0 && (
                <div className="max-w-[220px] rounded-xl border border-gray-200 bg-white/90 shadow-sm backdrop-blur">
                  <button
                    onClick={() => setShowRelFilter((v) => !v)}
                    className="flex w-full items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500"
                  >
                    关系类型
                    <span className="text-gray-400">{showRelFilter ? '▲' : '▼'}</span>
                  </button>
                  {showRelFilter && (
                    <div className="flex flex-wrap gap-1.5 p-3 pt-0">
                      {relTypesPresent.map((ty) => {
                        const active = focusRelType === ty;
                        const dimmed = focusRelType !== null && !active;
                        return (
                          <button
                            key={ty}
                            onClick={() => toggleRelType(ty)}
                            title={active ? '点击取消聚焦' : `只显示 ${ty} 关系`}
                            className={`rounded-full border px-2 py-0.5 text-xs transition ${
                              active
                                ? 'border-indigo-400 bg-indigo-50 font-semibold text-indigo-700 ring-1 ring-indigo-300'
                                : dimmed
                                ? 'border-gray-100 text-gray-300'
                                : 'border-slate-300 bg-slate-50 text-slate-600 hover:border-slate-400'
                            }`}
                          >
                            {ty}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {selected && (
          <aside className="w-80 shrink-0 animate-fade-in overflow-y-auto border-l border-gray-200 bg-white p-5">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <span className="mb-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-white" style={{ backgroundColor: entityColor(selected.type) }}>
                  {selected.type}
                </span>
                <h2 className="text-lg font-bold text-gray-900">{selected.name}</h2>
                <p className="mt-1 text-xs text-gray-400">{degree[selected.id] ?? 0} {t('graph.connections')}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>

            <Link href={`/wiki/entities/${selected.id}`}
              className="mb-5 flex w-full items-center justify-center gap-1.5 rounded-lg bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700">
              <BookOpen size={14} /> {t('graph.open_wiki')}
            </Link>

            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{t('graph.relations')} ({selectedRelations.length})</p>
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
                      onClick={() => { if (other) focusNode({ id: otherId, name: other.name, type: other.entity_type }); }}
                      className="font-medium text-gray-800 hover:text-blue-600"
                    >
                      {other?.name ?? otherId.slice(0, 8)}
                    </button>
                  </li>
                );
              })}
              {selectedRelations.length === 0 && <li className="text-xs text-gray-400">{t('common.empty')}</li>}
            </ul>
          </aside>
        )}
      </div>
    </div>
  );
}
