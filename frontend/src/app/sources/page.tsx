'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Source, SourceCreate } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Plus, ExternalLink } from 'lucide-react';

const activityColor: Record<string, 'green' | 'blue' | 'yellow' | 'gray'> = {
  very_active: 'green', active: 'blue', normal: 'yellow', inactive: 'gray', unknown: 'gray',
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<SourceCreate>>({ name: '', source_type: 'person', activity_status: 'unknown' });

  useEffect(() => {
    api.get<Source[]>('/sources').then(setSources).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.post<Source>('/sources', form);
      setSources((prev) => [...prev, created]);
      setShowForm(false);
      setForm({ name: '', source_type: 'person', activity_status: 'unknown' });
    } catch (err) {
      alert(String(err));
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Sources</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus size={16} /> New Source
        </button>
      </div>

      {showForm && (
        <Card className="mb-6 p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Create Source</h2>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
              <input required value={form.name ?? ''} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <select value={form.source_type} onChange={e => setForm(f => ({ ...f, source_type: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {['person', 'organization', 'rss', 'website', 'github_repo', 'arxiv_category', 'newsletter', 'social_account'].map(t =>
                  <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Activity Status</label>
              <select value={form.activity_status} onChange={e => setForm(f => ({ ...f, activity_status: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {['very_active', 'active', 'normal', 'inactive', 'unknown'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Affiliation Type</label>
              <select value={form.affiliation_type ?? ''} onChange={e => setForm(f => ({ ...f, affiliation_type: e.target.value || undefined }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">—</option>
                {['industry', 'academia', 'media', 'independent', 'other'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="col-span-2 flex gap-3">
              <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">Create</button>
              <button type="button" onClick={() => setShowForm(false)} className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">Cancel</button>
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
                {['Name', 'Type', 'Organization', 'Accounts', 'Tags', 'Status', 'Importance'].map(h => (
                  <th key={h} className="px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sources.map((src) => (
                <tr key={src.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{src.name}</td>
                  <td className="px-4 py-3"><Badge>{src.source_type}</Badge></td>
                  <td className="px-4 py-3 text-gray-500">{src.organization?.name ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {src.accounts.map(acc => (
                        <a key={acc.id} href={acc.url} target="_blank" rel="noreferrer"
                          className="flex items-center gap-0.5 text-xs text-blue-600 hover:underline">
                          {acc.platform} <ExternalLink size={10} />
                        </a>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {src.source_tags.map(st => (
                        <Badge key={st.tag_id} variant="blue">{st.tag?.name ?? st.tag_id}</Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={activityColor[src.activity_status] ?? 'gray'}>{src.activity_status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{src.importance_score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {sources.length === 0 && <p className="px-4 py-6 text-center text-sm text-gray-400">No sources found.</p>}
        </div>
      )}
    </div>
  );
}
