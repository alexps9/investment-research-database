'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Signal } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Plus, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';

const typeBadge: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  paper: 'blue', blog: 'green', tweet: 'purple', model_release: 'yellow', news: 'default',
};
const statusBadge: Record<string, 'green' | 'yellow' | 'gray' | 'default'> = {
  processed: 'green', collected: 'yellow', duplicated: 'gray', ignored: 'gray', archived: 'gray',
};

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', url: '', signal_type: 'paper', status: 'collected' });

  useEffect(() => {
    api.get<Signal[]>('/signals').then(setSignals).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.post<Signal>('/signals', form);
      setSignals((prev) => [created, ...prev]);
      setShowForm(false);
      setForm({ title: '', url: '', signal_type: 'paper', status: 'collected' });
    } catch (err) { alert(String(err)); }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Signals</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          <Plus size={16} /> New Signal
        </button>
      </div>

      {showForm && (
        <Card className="mb-6 p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Create Signal</h2>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
              <input required value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">URL *</label>
              <input required type="url" value={form.url} onChange={e => setForm(f => ({ ...f, url: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <select value={form.signal_type} onChange={e => setForm(f => ({ ...f, signal_type: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {['paper', 'tweet', 'blog', 'news', 'tech_report', 'github_release', 'model_release', 'benchmark', 'dataset', 'other'].map(t =>
                  <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {['collected', 'processed', 'duplicated', 'ignored', 'archived'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
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
        <div className="grid gap-4">
          {signals.map((sig) => (
            <Card key={sig.id} className="flex items-start gap-4 p-4">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <Badge variant={typeBadge[sig.signal_type] ?? 'default'}>{sig.signal_type}</Badge>
                  <Badge variant={statusBadge[sig.status] ?? 'default'}>{sig.status}</Badge>
                  {sig.published_at && (
                    <span className="text-xs text-gray-400">{format(new Date(sig.published_at), 'MMM d, yyyy')}</span>
                  )}
                </div>
                <a href={sig.url} target="_blank" rel="noreferrer"
                  className="flex items-start gap-1 font-medium text-gray-900 hover:text-blue-600 text-sm">
                  {sig.title} <ExternalLink size={12} className="mt-0.5 shrink-0" />
                </a>
                {sig.analysis?.tldr && (
                  <p className="mt-1 text-xs text-gray-500 line-clamp-2">{sig.analysis.tldr}</p>
                )}
                {sig.analysis?.topic_tags && sig.analysis.topic_tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {sig.analysis.topic_tags.map(t => <Badge key={t} variant="purple">{t}</Badge>)}
                  </div>
                )}
              </div>
              {sig.analysis?.reading_priority && (
                <Badge variant={sig.analysis.reading_priority === 'must_read' ? 'red' : 'default'}>
                  {sig.analysis.reading_priority}
                </Badge>
              )}
            </Card>
          ))}
          {signals.length === 0 && <p className="text-center text-sm text-gray-400 py-12">No signals found.</p>}
        </div>
      )}
    </div>
  );
}
