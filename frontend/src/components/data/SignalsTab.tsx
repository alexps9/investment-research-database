'use client';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Signal } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Plus, ExternalLink, Pencil, Trash2, Search } from 'lucide-react';
import { format } from 'date-fns';
import { SignalEditModal } from '@/components/SignalEditModal';
import { downloadCsv, type CsvColumn } from '@/lib/csv';
import { useRowSelection, Checkbox, ExportBar, bulkDelete } from './selection';

const typeBadge: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  paper: 'blue', blog: 'green', tweet: 'purple', model_release: 'yellow', news: 'default',
};
const statusBadge: Record<string, 'green' | 'yellow' | 'gray' | 'default'> = {
  processed: 'green', collected: 'yellow', duplicated: 'gray', ignored: 'gray', archived: 'gray',
};

const CSV_COLUMNS: CsvColumn<Signal>[] = [
  { key: 'id', header: 'id' },
  { key: 'title', header: 'title' },
  { key: 'url', header: 'url' },
  { key: 'signal_type', header: 'signal_type' },
  { key: 'status', header: 'status' },
  { key: 'published_at', header: 'published_at' },
  { key: 'tldr', header: 'tldr', get: (s) => s.analysis?.tldr ?? '' },
  { key: 'reading_priority', header: 'reading_priority', get: (s) => s.analysis?.reading_priority ?? '' },
];

export function SignalsTab() {
  const { t } = useLang();
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Signal | null>(null);
  const [q, setQ] = useState('');
  const [deleting, setDeleting] = useState(false);
  const { selected, toggle, setAll, clear } = useRowSelection();

  useEffect(() => {
    api.get<Signal[]>('/signals?limit=500').then(setSignals).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return signals;
    return signals.filter((s) =>
      s.title.toLowerCase().includes(k) || (s.analysis?.tldr ?? '').toLowerCase().includes(k),
    );
  }, [signals, q]);

  const allChecked = filtered.length > 0 && filtered.every((s) => selected.has(s.id));

  function handleSaved(saved: Signal) {
    setSignals((prev) => {
      const idx = prev.findIndex((s) => s.id === saved.id);
      if (idx === -1) return [saved, ...prev];
      const next = [...prev];
      next[idx] = saved;
      return next;
    });
  }

  async function handleDelete(sig: Signal) {
    if (!confirm(t('action.confirm_delete').replace('{name}', sig.title))) return;
    try {
      await api.delete(`/signals/${sig.id}`);
      setSignals((prev) => prev.filter((s) => s.id !== sig.id));
    } catch (err) {
      alert(`${t('action.delete_failed')}: ${String(err)}`);
    }
  }

  async function handleBulkDelete() {
    const ids = signals.filter((s) => selected.has(s.id)).map((s) => s.id);
    if (ids.length === 0) return;
    if (!confirm(t('action.confirm_bulk_delete').replace('{n}', String(ids.length)))) return;
    setDeleting(true);
    const { ok, failed } = await bulkDelete(ids, (id) => api.delete(`/signals/${id}`));
    const okSet = new Set(ok);
    setSignals((prev) => prev.filter((s) => !okSet.has(s.id)));
    clear();
    setDeleting(false);
    if (failed.length) alert(t('action.bulk_delete_failed').replace('{n}', String(failed.length)));
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-72 max-w-full">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t('data.search.signals')}
              className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <label className="flex shrink-0 items-center gap-1.5 text-xs text-gray-500">
            <Checkbox checked={allChecked} onChange={() => setAll(filtered.map((s) => s.id), !allChecked)} indeterminate={selected.size > 0} />
            {t('select.all')}
          </label>
        </div>
        <div className="flex items-center gap-2">
          <ExportBar
            count={selected.size}
            onExportSelected={() => downloadCsv(signals.filter((s) => selected.has(s.id)), CSV_COLUMNS, 'signals')}
            onExportAll={() => downloadCsv(filtered, CSV_COLUMNS, 'signals')}
            onClear={clear}
            onDeleteSelected={handleBulkDelete}
            deleting={deleting}
          />
          <button
            onClick={() => { setEditing(null); setModalOpen(true); }}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
          >
            <Plus size={16} /> {t('action.new')}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
      ) : (
        <div className="grid gap-3">
          {filtered.map((sig) => (
            <Card key={sig.id} className={`flex items-start gap-3 p-4 transition-colors ${selected.has(sig.id) ? 'ring-1 ring-blue-300' : ''}`}>
              <div className="pt-0.5"><Checkbox checked={selected.has(sig.id)} onChange={() => toggle(sig.id)} /></div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <Badge variant={typeBadge[sig.signal_type] ?? 'default'}>{sig.signal_type}</Badge>
                  <Badge variant={statusBadge[sig.status] ?? 'default'}>{sig.status}</Badge>
                  {sig.published_at && (
                    <span className="text-xs text-gray-400">{format(new Date(sig.published_at), 'MMM d, yyyy')}</span>
                  )}
                </div>
                <a href={sig.url} target="_blank" rel="noreferrer"
                  className="flex items-start gap-1 text-sm font-medium text-gray-900 hover:text-blue-600">
                  {sig.title} <ExternalLink size={12} className="mt-0.5 shrink-0" />
                </a>
                {sig.analysis?.tldr && <p className="mt-1 line-clamp-2 text-xs text-gray-500">{sig.analysis.tldr}</p>}
                {sig.analysis?.topic_tags && sig.analysis.topic_tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {sig.analysis.topic_tags.map((tag) => <Badge key={tag} variant="purple">{tag}</Badge>)}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1">
                {sig.analysis?.reading_priority && (
                  <Badge variant={sig.analysis.reading_priority === 'must_read' ? 'red' : 'default'}>
                    {sig.analysis.reading_priority}
                  </Badge>
                )}
                <button onClick={() => { setEditing(sig); setModalOpen(true); }}
                  className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-600" title={t('action.edit')}>
                  <Pencil size={15} />
                </button>
                <button onClick={() => handleDelete(sig)}
                  className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600" title={t('action.delete')}>
                  <Trash2 size={15} />
                </button>
              </div>
            </Card>
          ))}
          {filtered.length === 0 && <p className="py-12 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      )}

      <SignalEditModal open={modalOpen} signal={editing} onClose={() => setModalOpen(false)} onSaved={handleSaved} />
    </div>
  );
}
