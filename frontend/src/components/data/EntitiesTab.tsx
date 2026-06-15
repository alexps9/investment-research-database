'use client';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Entity } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import Link from 'next/link';
import { Plus, BookOpen, Search } from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { downloadCsv, type CsvColumn } from '@/lib/csv';
import { useRowSelection, Checkbox, ExportBar } from './selection';

const typeColor: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  person: 'blue', organization: 'green', model: 'purple', method: 'yellow', topic: 'default',
};

const ENTITY_TYPES = ['person', 'organization', 'paper', 'model', 'method', 'dataset', 'benchmark', 'topic', 'project', 'system', 'event'];

const CSV_COLUMNS: CsvColumn<Entity>[] = [
  { key: 'id', header: 'id' },
  { key: 'name', header: 'name' },
  { key: 'canonical_name', header: 'canonical_name' },
  { key: 'entity_type', header: 'entity_type' },
  { key: 'description', header: 'description' },
  { key: 'aliases', header: 'aliases', get: (e) => e.aliases.map((a) => a.alias).join('; ') },
];

export function EntitiesTab() {
  const { t } = useLang();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [q, setQ] = useState('');
  const [form, setForm] = useState({ name: '', canonical_name: '', entity_type: 'topic', description: '' });
  const { selected, toggle, setAll, clear } = useRowSelection();

  useEffect(() => {
    api.get<Entity[]>('/entities?limit=1000').then(setEntities).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return entities;
    return entities.filter((e) =>
      e.name.toLowerCase().includes(k) ||
      (e.description ?? '').toLowerCase().includes(k) ||
      e.aliases.some((a) => a.alias.toLowerCase().includes(k)),
    );
  }, [entities, q]);

  const allChecked = filtered.length > 0 && filtered.every((e) => selected.has(e.id));

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.post<Entity>('/entities', { ...form, metadata: {} });
      setEntities((prev) => [created, ...prev]);
      setShowForm(false);
      setForm({ name: '', canonical_name: '', entity_type: 'topic', description: '' });
    } catch (err) { alert(String(err)); }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-72 max-w-full">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t('data.search.entities')}
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <ExportBar
            count={selected.size}
            onExportSelected={() => downloadCsv(entities.filter((e) => selected.has(e.id)), CSV_COLUMNS, 'entities')}
            onExportAll={() => downloadCsv(filtered, CSV_COLUMNS, 'entities')}
            onClear={clear}
          />
          <button onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
            <Plus size={16} /> {t('action.new')}
          </button>
        </div>
      </div>

      {showForm && (
        <Card className="mb-4 p-5">
          <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Name *</label>
              <input required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Canonical Name *</label>
              <input required value={form.canonical_name} onChange={(e) => setForm((f) => ({ ...f, canonical_name: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Type</label>
              <select value={form.entity_type} onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {ENTITY_TYPES.map((ty) => <option key={ty} value={ty}>{ty}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Description</label>
              <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="col-span-full flex gap-3">
              <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">{t('action.save')}</button>
              <button type="button" onClick={() => setShowForm(false)} className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700">{t('action.cancel')}</button>
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
                <th className="px-4 py-3">{t('entities.col.name')}</th>
                <th className="px-4 py-3">{t('entities.col.type')}</th>
                <th className="px-4 py-3">{t('entities.col.aliases')}</th>
                <th className="px-4 py-3">{t('wiki.col.description')}</th>
                <th className="px-4 py-3 text-right">{t('action.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((ent) => (
                <tr key={ent.id} className={`transition-colors hover:bg-blue-50/40 ${selected.has(ent.id) ? 'bg-blue-50/60' : ''}`}>
                  <td className="px-4 py-3"><Checkbox checked={selected.has(ent.id)} onChange={() => toggle(ent.id)} /></td>
                  <td className="px-4 py-3 font-medium text-gray-900">{ent.name}</td>
                  <td className="px-4 py-3"><Badge variant={typeColor[ent.entity_type] ?? 'default'}>{ent.entity_type}</Badge></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {ent.aliases.slice(0, 3).map((a) => <Badge key={a.id} variant="gray">{a.alias}</Badge>)}
                    </div>
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-gray-500">{ent.description ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <Link href={`/wiki/entities/${ent.id}`}
                        className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50">
                        <BookOpen size={13} /> Wiki
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <p className="px-4 py-10 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      )}
    </div>
  );
}
