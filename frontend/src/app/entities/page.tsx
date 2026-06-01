'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Entity } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import Link from 'next/link';
import { Plus, BookOpen } from 'lucide-react';

const typeColor: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  person: 'blue', organization: 'green', model: 'purple', method: 'yellow', topic: 'default',
};

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', canonical_name: '', entity_type: 'topic', description: '' });

  useEffect(() => {
    api.get<Entity[]>('/entities').then(setEntities).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.post<Entity>('/entities', { ...form, metadata: {} });
      setEntities((prev) => [...prev, created]);
      setShowForm(false);
      setForm({ name: '', canonical_name: '', entity_type: 'topic', description: '' });
    } catch (err) { alert(String(err)); }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Entities</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          <Plus size={16} /> New Entity
        </button>
      </div>

      {showForm && (
        <Card className="mb-6 p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Create Entity</h2>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
              <input required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Canonical Name *</label>
              <input required value={form.canonical_name} onChange={e => setForm(f => ({ ...f, canonical_name: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <select value={form.entity_type} onChange={e => setForm(f => ({ ...f, entity_type: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {['person', 'organization', 'paper', 'model', 'method', 'dataset', 'benchmark', 'topic', 'project', 'system', 'event'].map(t =>
                  <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="col-span-2 flex gap-3">
              <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">Create</button>
              <button type="button" onClick={() => setShowForm(false)} className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700">Cancel</button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                {['Name', 'Type', 'Aliases', 'Description', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {entities.map((ent) => (
                <tr key={ent.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{ent.name}</td>
                  <td className="px-4 py-3"><Badge variant={typeColor[ent.entity_type] ?? 'default'}>{ent.entity_type}</Badge></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {ent.aliases.slice(0, 3).map(a => <Badge key={a.id} variant="gray">{a.alias}</Badge>)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{ent.description ?? '—'}</td>
                  <td className="px-4 py-3">
                    <Link href={`/wiki/entities/${ent.id}`}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                      <BookOpen size={12} /> Wiki
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {entities.length === 0 && <p className="px-4 py-6 text-center text-sm text-gray-400">No entities found.</p>}
        </div>
      )}
    </div>
  );
}
