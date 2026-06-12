'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Source } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Plus, ExternalLink, Pencil, Trash2, Download } from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { SourceEditModal } from '@/components/SourceEditModal';

const activityColor: Record<string, 'green' | 'blue' | 'yellow' | 'gray'> = {
  very_active: 'green', active: 'blue', normal: 'yellow', inactive: 'gray', unknown: 'gray',
};

export default function SourcesPage() {
  const { t } = useLang();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Source | null>(null);

  useEffect(() => {
    api.get<Source[]>('/sources?limit=1000').then(setSources).catch(console.error).finally(() => setLoading(false));
  }, []);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }
  function openEdit(src: Source) {
    setEditing(src);
    setModalOpen(true);
  }

  function handleSaved(saved: Source) {
    setSources((prev) => {
      const idx = prev.findIndex((s) => s.id === saved.id);
      if (idx === -1) return [saved, ...prev];
      const next = [...prev];
      next[idx] = saved;
      return next;
    });
  }

  async function handleDelete(src: Source) {
    if (!confirm(t('action.confirm_delete').replace('{name}', src.name))) return;
    try {
      await api.delete(`/sources/${src.id}`);
      setSources((prev) => prev.filter((s) => s.id !== src.id));
    } catch (err) {
      alert(`${t('action.delete_failed')}: ${String(err)}`);
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('sources.title')}</h1>
        <div className="flex items-center gap-2">
          <a
            href={api.url('/export/sources.csv')}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Download size={16} /> {t('action.export')}
          </a>
          <button
            onClick={openCreate}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus size={16} /> {t('action.new')}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">{t('sources.col.name')}</th>
                <th className="px-4 py-3">{t('sources.col.type')}</th>
                <th className="px-4 py-3">{t('sources.col.tier')}</th>
                <th className="px-4 py-3">{t('sources.col.org')}</th>
                <th className="px-4 py-3">{t('sources.col.activity')}</th>
                <th className="px-4 py-3">Links</th>
                <th className="px-4 py-3 text-right">{t('action.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sources.map((src) => (
                <tr key={src.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{src.name}</td>
                  <td className="px-4 py-3"><Badge>{src.source_type}</Badge></td>
                  <td className="px-4 py-3">{src.tier ? <Badge variant="purple">{src.tier}</Badge> : <span className="text-gray-300">—</span>}</td>
                  <td className="px-4 py-3 text-gray-500">{src.organization?.name ?? '—'}</td>
                  <td className="px-4 py-3">
                    <Badge variant={activityColor[src.activity_status] ?? 'gray'}>{src.activity_status}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {src.accounts.map((acc) => (
                        <a key={acc.id} href={acc.url} target="_blank" rel="noreferrer"
                          className="flex items-center gap-0.5 text-xs text-blue-600 hover:underline">
                          {acc.platform} <ExternalLink size={10} />
                        </a>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEdit(src)}
                        className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-600" title={t('action.edit')}>
                        <Pencil size={15} />
                      </button>
                      <button onClick={() => handleDelete(src)}
                        className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600" title={t('action.delete')}>
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {sources.length === 0 && <p className="px-4 py-6 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      )}

      <SourceEditModal
        open={modalOpen}
        source={editing}
        onClose={() => setModalOpen(false)}
        onSaved={handleSaved}
      />
    </div>
  );
}
