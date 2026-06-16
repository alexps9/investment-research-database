'use client';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Entity, EntityRelation } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import Link from 'next/link';
import { Plus, BookOpen, Search, Pencil, Trash2, Check, X, GitBranch } from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { downloadCsv, type CsvColumn } from '@/lib/csv';
import { useRowSelection, Checkbox, ExportBar } from './selection';

const typeColor: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  topic: 'blue',
};

const FIELD_TYPES = ['topic'];

const CSV_COLUMNS: CsvColumn<Entity>[] = [
  { key: 'id', header: 'id' },
  { key: 'name', header: 'name' },
  { key: 'canonical_name', header: 'canonical_name' },
  { key: 'entity_type', header: 'entity_type' },
  { key: 'introduction', header: 'introduction' },
  { key: 'aliases', header: 'aliases', get: (e) => e.aliases.map((a) => a.alias).join('; ') },
];

interface EditState {
  name: string;
  canonical_name: string;
  entity_type: string;
  introduction: string;
  /** Current SUBTOPIC_OF relation ID (if any) */
  currentRelId: string | null;
  /** Currently selected parent entity ID */
  parentId: string;
}

export function EntitiesTab() {
  const { t } = useLang();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [q, setQ] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [form, setForm] = useState({ name: '', canonical_name: '', entity_type: 'topic', introduction: '' });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState | null>(null);
  const { selected, toggle, setAll, clear } = useRowSelection();

  // Map: entityId → parent entity name (for display in table)
  const [parentMap, setParentMap] = useState<Record<string, string>>({});

  useEffect(() => {
    api.get<Entity[]>('/entities?limit=1000').then((all) => {
      const filtered = all.filter((e) => FIELD_TYPES.includes(e.entity_type));
      setEntities(filtered);

      // Build parent map from SUBTOPIC_OF relations
      const ids = filtered.map((e) => e.id);
      // Fetch all relations for graph and extract parent info
      api.get<EntityRelation[]>('/graph/relations?limit=2000').then((rels) => {
        const map: Record<string, string> = {};
        const byId = Object.fromEntries(filtered.map((e) => [e.id, e]));
        rels.forEach((r) => {
          if (r.relation_type === 'SUBTOPIC_OF' && ids.includes(r.subject_entity_id)) {
            const parent = r.object_entity ?? byId[r.object_entity_id];
            if (parent) map[r.subject_entity_id] = parent.name;
          }
        });
        setParentMap(map);
      }).catch(() => {});
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = entities;
    if (typeFilter !== 'all') list = list.filter((e) => e.entity_type === typeFilter);
    const k = q.trim().toLowerCase();
    if (!k) return list;
    return list.filter((e) =>
      e.name.toLowerCase().includes(k) ||
      (e.introduction ?? '').toLowerCase().includes(k) ||
      e.aliases.some((a) => a.alias.toLowerCase().includes(k)),
    );
  }, [entities, q, typeFilter]);

  const allChecked = filtered.length > 0 && filtered.every((e) => selected.has(e.id));

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.post<Entity>('/entities', { ...form, metadata: {} });
      // Backend get-or-create may return an existing row — dedupe so the list
      // never shows the same entity twice.
      setEntities((prev) => [created, ...prev.filter((e) => e.id !== created.id)]);
      setShowForm(false);
      setForm({ name: '', canonical_name: '', entity_type: 'topic', introduction: '' });
    } catch (err) { alert(String(err)); }
  }

  /** Start editing: load entity's SUBTOPIC_OF relation to pre-fill parent selector */
  async function startEdit(ent: Entity) {
    let currentRelId: string | null = null;
    let parentId = '';
    try {
      const rels = await api.get<EntityRelation[]>(`/entities/${ent.id}/relations`);
      const subtopic = rels.find(
        (r) => r.relation_type === 'SUBTOPIC_OF' && r.subject_entity_id === ent.id,
      );
      if (subtopic) {
        currentRelId = subtopic.id;
        parentId = subtopic.object_entity_id;
      }
    } catch { /* ignore */ }

    setEditingId(ent.id);
    setEditState({
      name: ent.name,
      canonical_name: ent.canonical_name,
      entity_type: ent.entity_type,
      introduction: ent.introduction ?? '',
      currentRelId,
      parentId,
    });
  }

  async function saveEdit(ent: Entity) {
    if (!editState) return;
    try {
      // 1. Update entity fields
      const updated = await api.patch<Entity>(`/entities/${ent.id}`, {
        name: editState.name,
        canonical_name: editState.canonical_name,
        entity_type: editState.entity_type,
        introduction: editState.introduction || undefined,
      });
      setEntities((prev) => prev.map((e) => (e.id === ent.id ? updated : e)));

      // 2. Re-point the parent (SUBTOPIC_OF) relation: drop the old edge then
      // re-create it only when a (different, non-self) parent is selected.
      if (editState.currentRelId) {
        await api.delete(`/entities/relations/${editState.currentRelId}`).catch(() => {});
      }
      if (editState.parentId && editState.parentId !== ent.id) {
        await api.post(`/entities/${ent.id}/relations`, {
          subject_entity_id: ent.id,
          relation_type: 'SUBTOPIC_OF',
          object_entity_id: editState.parentId,
          confidence: 1.0,
          extracted_by: 'manual',
        });
      }

      // Update local parent map
      setParentMap((m) => {
        const next = { ...m };
        if (!editState.parentId) {
          delete next[ent.id];
        } else {
          const parent = entities.find((e) => e.id === editState.parentId);
          if (parent) next[ent.id] = parent.name;
        }
        return next;
      });

      setEditingId(null);
    } catch (err) { alert(String(err)); }
  }

  async function handleDelete(ent: Entity) {
    if (!confirm(`删除「${ent.name}」及其所有图谱关系？`)) return;
    try {
      await api.delete(`/entities/${ent.id}`);
      setEntities((prev) => prev.filter((e) => e.id !== ent.id));
      setParentMap((m) => { const n = { ...m }; delete n[ent.id]; return n; });
    } catch (err) { alert(String(err)); }
  }

  const inputCls = 'w-full rounded border border-gray-200 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500';

  return (
    <div>
      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-64 max-w-full">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索研究领域…"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-1">
          {['all', ...FIELD_TYPES].map((tp) => (
            <button
              key={tp}
              onClick={() => setTypeFilter(tp)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${typeFilter === tp ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {tp === 'all' ? '全部' : tp}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <ExportBar
            count={selected.size}
            onExportSelected={() => downloadCsv(entities.filter((e) => selected.has(e.id)), CSV_COLUMNS, 'research_fields')}
            onExportAll={() => downloadCsv(filtered, CSV_COLUMNS, 'research_fields')}
            onClear={clear}
          />
          <button onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
            <Plus size={16} /> {t('action.new')}
          </button>
        </div>
      </div>

      {/* Create form */}
      {showForm && (
        <Card className="mb-4 p-5">
          <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">名称 *</label>
              <input required value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">规范名称 *</label>
              <input required value={form.canonical_name}
                onChange={(e) => setForm((f) => ({ ...f, canonical_name: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">类型</label>
              <select value={form.entity_type}
                onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))} className={inputCls}>
                {FIELD_TYPES.map((ty) => <option key={ty} value={ty}>{ty}</option>)}
              </select>
            </div>
            <div className="col-span-full">
              <label className="mb-1 block text-xs font-medium text-gray-600">简介</label>
              <textarea rows={2} value={form.introduction}
                onChange={(e) => setForm((f) => ({ ...f, introduction: e.target.value }))} className={inputCls} />
            </div>
            <div className="col-span-full flex gap-3">
              <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                {t('action.save')}
              </button>
              <button type="button" onClick={() => setShowForm(false)}
                className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700">
                {t('action.cancel')}
              </button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50/80 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="w-10 px-4 py-3">
                  <Checkbox checked={allChecked} onChange={() => setAll(filtered.map((e) => e.id), !allChecked)} indeterminate={selected.size > 0} />
                </th>
                <th className="px-4 py-3">名称</th>
                <th className="px-4 py-3">类型</th>
                <th className="px-4 py-3">所属上级</th>
                <th className="px-4 py-3">简介</th>
                <th className="px-4 py-3 text-right">{t('action.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((ent) => {
                const isEditing = editingId === ent.id;
                return (
                  <tr key={ent.id} className={`transition-colors hover:bg-blue-50/40 ${selected.has(ent.id) ? 'bg-blue-50/60' : ''}`}>
                    <td className="px-4 py-2.5">
                      <Checkbox checked={selected.has(ent.id)} onChange={() => toggle(ent.id)} />
                    </td>

                    {/* Name */}
                    <td className="px-4 py-2.5">
                      {isEditing && editState ? (
                        <div className="flex flex-col gap-1.5">
                          <input
                            value={editState.name}
                            onChange={(e) => setEditState((s) => s ? { ...s, name: e.target.value } : s)}
                            className={inputCls} placeholder="名称"
                          />
                          <input
                            value={editState.canonical_name}
                            onChange={(e) => setEditState((s) => s ? { ...s, canonical_name: e.target.value } : s)}
                            className={inputCls} placeholder="规范名称（英文）"
                          />
                        </div>
                      ) : (
                        <div>
                          <span className="font-medium text-gray-900">{ent.name}</span>
                          {ent.canonical_name !== ent.name && (
                            <span className="ml-1 text-xs text-gray-400">({ent.canonical_name})</span>
                          )}
                        </div>
                      )}
                    </td>

                    {/* Type */}
                    <td className="px-4 py-2.5">
                      {isEditing && editState ? (
                        <select
                          value={editState.entity_type}
                          onChange={(e) => setEditState((s) => s ? { ...s, entity_type: e.target.value } : s)}
                          className={inputCls}
                        >
                          {FIELD_TYPES.map((ty) => <option key={ty} value={ty}>{ty}</option>)}
                        </select>
                      ) : (
                        <Badge variant={typeColor[ent.entity_type] ?? 'default'}>{ent.entity_type}</Badge>
                      )}
                    </td>

                    {/* Parent / hierarchy */}
                    <td className="px-4 py-2.5">
                      {isEditing && editState ? (
                        <select
                          value={editState.parentId}
                          onChange={(e) => setEditState((s) => s ? { ...s, parentId: e.target.value } : s)}
                          className={inputCls}
                        >
                          <option value="">— 无上级 —</option>
                          {entities
                            .filter((e) => e.id !== ent.id)
                            .map((e) => (
                              <option key={e.id} value={e.id}>
                                {parentMap[e.id] ? `${parentMap[e.id]} › ` : ''}{e.name}
                              </option>
                            ))}
                        </select>
                      ) : parentMap[ent.id] ? (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <GitBranch size={11} className="text-gray-400" />
                          {parentMap[ent.id]}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-300">—</span>
                      )}
                    </td>

                    {/* Introduction */}
                    <td className="px-4 py-2.5 max-w-xs">
                      {isEditing && editState ? (
                        <textarea
                          rows={2}
                          value={editState.introduction}
                          onChange={(e) => setEditState((s) => s ? { ...s, introduction: e.target.value } : s)}
                          className={inputCls} placeholder="简介"
                        />
                      ) : (
                        <span className="line-clamp-2 text-xs text-gray-500">{ent.introduction ?? '—'}</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        {isEditing ? (
                          <>
                            <button onClick={() => saveEdit(ent)} title="保存"
                              className="rounded p-1 text-green-600 hover:bg-green-50">
                              <Check size={14} />
                            </button>
                            <button onClick={() => setEditingId(null)} title="取消"
                              className="rounded p-1 text-gray-400 hover:bg-gray-100">
                              <X size={14} />
                            </button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => startEdit(ent)} title="编辑"
                              className="rounded p-1 text-gray-400 hover:bg-blue-50 hover:text-blue-600">
                              <Pencil size={13} />
                            </button>
                            <Link href={`/wiki/entities/${ent.id}`} title="Wiki"
                              className="flex items-center rounded p-1 text-blue-600 hover:bg-blue-50">
                              <BookOpen size={13} />
                            </Link>
                            <button onClick={() => handleDelete(ent)} title="删除"
                              className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600">
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && <p className="px-4 py-10 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      )}
    </div>
  );
}
