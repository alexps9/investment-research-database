'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { Signal, SignalUpdate } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { useLang } from '@/lib/i18n';

const SIGNAL_TYPES = ['paper', 'tweet', 'blog', 'news', 'tech_report', 'github_release', 'model_release', 'benchmark', 'dataset', 'other'];
const STATUSES = ['collected', 'processed', 'duplicated', 'ignored', 'archived'];

const inputCls = 'w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
const labelCls = 'block text-xs font-medium text-gray-600 mb-1';

interface Props {
  open: boolean;
  signal: Signal | null;   // null = create mode
  onClose: () => void;
  onSaved: (s: Signal) => void;
}

export function SignalEditModal({ open, signal, onClose, onSaved }: Props) {
  const { t } = useLang();
  const [form, setForm] = useState<Partial<Signal>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [initId, setInitId] = useState<string | null>(null);
  const currentId = signal?.id ?? '__new__';
  if (open && initId !== currentId) {
    setInitId(currentId);
    setForm(signal ? { ...signal } : { title: '', url: '', signal_type: 'paper', status: 'collected' });
    setError(null);
  }

  function set<K extends keyof Signal>(key: K, value: Signal[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      let saved: Signal;
      if (signal) {
        const payload: SignalUpdate = {
          title: form.title,
          signal_type: form.signal_type,
          abstract: form.abstract,
          content: form.content,
          status: form.status,
          published_at: form.published_at,
        };
        saved = await api.patch<Signal>(`/signals/${signal.id}`, payload);
      } else {
        saved = await api.post<Signal>('/signals', {
          title: form.title, url: form.url, signal_type: form.signal_type,
          status: form.status, abstract: form.abstract,
        });
      }
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(`${t('action.save_failed')}: ${String(err)}`);
    } finally {
      setSaving(false);
    }
  }

  const title = signal ? t('action.edit_signal') : t('signals.title');

  return (
    <Modal open={open} onClose={onClose} title={title} widthClass="max-w-2xl">
      <form onSubmit={handleSave} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className={labelCls}>{t('signals.col.title')} *</label>
          <input required value={form.title ?? ''} onChange={(e) => set('title', e.target.value)} className={inputCls} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>URL *</label>
          <input required type="url" value={form.url ?? ''} disabled={!!signal}
            onChange={(e) => set('url', e.target.value)}
            className={`${inputCls} ${signal ? 'bg-gray-50 text-gray-400' : ''}`} />
        </div>
        <div>
          <label className={labelCls}>{t('signals.col.type')}</label>
          <select value={form.signal_type ?? 'paper'} onChange={(e) => set('signal_type', e.target.value)} className={inputCls}>
            {SIGNAL_TYPES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>{t('signals.col.status')}</label>
          <select value={form.status ?? 'collected'} onChange={(e) => set('status', e.target.value)} className={inputCls}>
            {STATUSES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div className="col-span-2">
          <label className={labelCls}>abstract</label>
          <textarea rows={3} value={form.abstract ?? ''} onChange={(e) => set('abstract', e.target.value || undefined)} className={inputCls} />
        </div>

        {error && <p className="col-span-2 text-sm text-red-600">{error}</p>}

        <div className="col-span-2 flex gap-3 border-t border-gray-100 pt-4">
          <button type="submit" disabled={saving}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? t('action.saving') : t('action.save')}
          </button>
          <button type="button" onClick={onClose}
            className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">
            {t('action.cancel')}
          </button>
        </div>
      </form>
    </Modal>
  );
}
