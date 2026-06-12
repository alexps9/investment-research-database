'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Signal } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Plus, ExternalLink, Pencil, Trash2, Download } from 'lucide-react';
import { format } from 'date-fns';
import { SignalEditModal } from '@/components/SignalEditModal';

const typeBadge: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  paper: 'blue', blog: 'green', tweet: 'purple', model_release: 'yellow', news: 'default',
};
const statusBadge: Record<string, 'green' | 'yellow' | 'gray' | 'default'> = {
  processed: 'green', collected: 'yellow', duplicated: 'gray', ignored: 'gray', archived: 'gray',
};

export default function SignalsPage() {
  const { t } = useLang();
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Signal | null>(null);

  useEffect(() => {
    api.get<Signal[]>('/signals?limit=200').then(setSignals).catch(console.error).finally(() => setLoading(false));
  }, []);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }
  function openEdit(sig: Signal) {
    setEditing(sig);
    setModalOpen(true);
  }

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

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('signals.title')}</h1>
        <div className="flex items-center gap-2">
          <a
            href={api.url('/export/signals.csv')}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Download size={16} /> {t('action.export')}
          </a>
          <button onClick={openCreate}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            <Plus size={16} /> {t('action.new')}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
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
                <button onClick={() => openEdit(sig)}
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
          {signals.length === 0 && <p className="text-center text-sm text-gray-400 py-12">{t('common.empty')}</p>}
        </div>
      )}

      <SignalEditModal
        open={modalOpen}
        signal={editing}
        onClose={() => setModalOpen(false)}
        onSaved={handleSaved}
      />
    </div>
  );
}
